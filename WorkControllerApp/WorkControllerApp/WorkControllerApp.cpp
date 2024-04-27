#include <cpprest/details/basic_types.h>
#include <cpprest/http_client.h>
#include <cpprest/ws_client.h>

#include <ShlObj.h>
#include <windows.h>
#include <objidl.h>
#include <iostream>
#include <string>
#include <fstream>
#include <memory>
#include <vector>
#include <curl/curl.h>
#include <locale>
#include <codecvt>

#include <gdiplus.h>
#pragma comment (lib, "Gdiplus.lib")

using namespace web;
using namespace web::websockets::client;

/**
* Ввод Username от пользователя, который будет использоваться для присоеденения к серверу
*/
std::string static GetAuthFromUser() {
	std::string username;
	std::cout << "Enter your username: ";
	std::getline(std::cin, username);
	return username;
}

/**
* Сохранение указанного Username, чтобы его можно было использовать автоматически при перезапуске ПК
*/
void static SaveAuthToFile(const std::string& username) {
	std::ofstream authFile("auth.dat");
	if (authFile.is_open()) {
		// Можно добавить шифрование перед записью
		authFile << username;
		authFile.close();
	}
	else {
		std::cerr << "Unable to open file to save username";
	}
}

/**
* Получение Username который хранится в файле 
*/
std::string static LoadAuthFromFile() {
	std::string username;
	std::ifstream authFile("auth.dat");
	if (authFile.is_open()) {
		// Читаем токен, если он существует
		std::getline(authFile, username);
		authFile.close();
	}
	return username;
}

/**
* Получение ссылки для подключения к веб-сокету сервера
*/
web::uri static MakeUri(const std::string& username, const std::string& machine_name, const std::string& domain) {
	// Использование uri_builder для построения URI
	web::uri_builder uri_builder;
	uri_builder.set_scheme(U("ws"));
	uri_builder.set_host(U("localhost:8000"));
	uri_builder.set_path(U("/ws"));

	// Добавление параметров запроса
	uri_builder.append_query(U("domain"), web::uri::encode_data_string(utility::conversions::to_string_t(domain)));
	uri_builder.append_query(U("machine"), web::uri::encode_data_string(utility::conversions::to_string_t(machine_name)));
	uri_builder.append_query(U("username"), web::uri::encode_data_string(utility::conversions::to_string_t(username)));

	// Возвращаем объект web::uri
	return uri_builder.to_uri();
}


/**
* Получение кодека для сохранения скриншота
*/
int static GetEncoderClsid(const WCHAR* format, CLSID* pClsid) {
	using namespace Gdiplus;
	UINT num = 0, size = 0;
	GetImageEncodersSize(&num, &size); // Получение размера и количества доступных кодеков
	if (size == 0) return -1; // Если кодеки не найдены

	ImageCodecInfo* pImageCodecInfo = (ImageCodecInfo*)(malloc(size));
	if (pImageCodecInfo == NULL) return -1; // Если не удалось выделить память под кодеки

	GetImageEncoders(num, size, pImageCodecInfo);
	for (UINT j = 0; j < num; ++j) {
		if (wcscmp(pImageCodecInfo[j].MimeType, format) == 0) { // Сравнение MIME-типа с искомыми
			*pClsid = pImageCodecInfo[j].Clsid;
			free(pImageCodecInfo);
			return j;
		}
	}
	// Освобождение памяти, кодек не найден, -1
	free(pImageCodecInfo);
	return -1;
}


/**
* Создание скриншота и сохранение его в файл
*/
void TakeScreenshot() {
	using namespace Gdiplus;
	ULONG_PTR gdiplusToken;
	GdiplusStartupInput gsi;
	if (GdiplusStartup(&gdiplusToken, &gsi, NULL) != Ok) {
		std::cerr << "GDI+ initialization failed.\n";
		return;
	}

	HWND desktopWindow = GetDesktopWindow();
	HDC desktopDC = GetDC(desktopWindow);
	if (!desktopDC) {
		std::cerr << "Failed to get the desktop device context.\n";
		GdiplusShutdown(gdiplusToken);
		return;
	}

	HDC captureDC = CreateCompatibleDC(desktopDC);
	if (!captureDC) {
		std::cerr << "Failed to create a compatible device context.\n";
		ReleaseDC(desktopWindow, desktopDC);
		GdiplusShutdown(gdiplusToken);
		return;
	}

	int width = GetSystemMetrics(SM_CXSCREEN);
	int height = GetSystemMetrics(SM_CYSCREEN);
	HBITMAP captureBitmap = CreateCompatibleBitmap(desktopDC, width, height);
	if (!captureBitmap) {
		std::cerr << "Failed to create a bitmap for screen capture.\n";
		DeleteDC(captureDC);
		ReleaseDC(desktopWindow, desktopDC);
		GdiplusShutdown(gdiplusToken);
		return;
	}

	SelectObject(captureDC, captureBitmap);
	BitBlt(captureDC, 0, 0, width, height, desktopDC, 0, 0, SRCCOPY | CAPTUREBLT);

	try {
		Bitmap bitmap(captureBitmap, NULL);
		CLSID pngClsid;
		GetEncoderClsid(L"image/png", &pngClsid);
		Status stat = bitmap.Save(L"output.png", &pngClsid, NULL);
		if (stat != Ok) {
			std::cerr << "Failed to save the captured image to a file.\n";
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Exception occurred while saving the image: " << e.what() << std::endl;
	}

	DeleteObject(captureBitmap);
	DeleteDC(captureDC);
	ReleaseDC(desktopWindow, desktopDC);
	GdiplusShutdown(gdiplusToken);
}


/**
* Отправка изображения на сервер
*/ 
bool static SendPNGToServer(const int session_id, const char* filePath) {
	CURL* curl;
	CURLcode res;
	bool success = false;

	std::ostringstream url;
	url << "http://localhost:8000/screenshot/" << std::to_string(session_id);
	std::cout << "Send screenshot to: " << url.str() << std::endl;

	curl = curl_easy_init();
	if (curl) {
		struct curl_httppost* formpost = NULL;
		struct curl_httppost* lastptr = NULL;
		struct curl_slist* headerlist = NULL;
		static const char buf[] = "Expect:";

		curl_formadd(&formpost, &lastptr,
			CURLFORM_COPYNAME, "file",
			CURLFORM_FILE, filePath,
			CURLFORM_END);

		curl_easy_setopt(curl, CURLOPT_URL, url.str().c_str());
		curl_easy_setopt(curl, CURLOPT_HTTPPOST, formpost);
		headerlist = curl_slist_append(headerlist, buf);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headerlist);
		res = curl_easy_perform(curl);
		std::cout << std::endl;
		if (res == CURLE_OK) {
			success = true;
			std::cout << "Screenshot sent successfully" << std::endl;
		}
		else {
			std::cerr << "Curl failed: " << curl_easy_strerror(res) << std::endl;
		}

		curl_easy_cleanup(curl);
		curl_formfree(formpost);
		curl_slist_free_all(headerlist);
	}

	return success;
}


/**
* Получение и обработка сообщений от сервера
*/
void static ConnectWebSocket(const web::uri uri) {
	websocket_client client;
	int session_id;

	try {
		// Подключение
		client.connect(uri).wait();
		std::cout << "Connect to: " << utility::conversions::to_utf8string(uri.to_string()) << std::endl;

		// Начало цикла для прослушивания входящих сообщений
		while (true) {
			client.receive().then([](websocket_incoming_message in_msg) {
				return in_msg.extract_string();
			}).then([&](std::string msg) {
				std::cout << "Received message: " << msg << std::endl;

				// Разбор сообщения
				std::istringstream iss(msg);
				std::string command;
				iss >> command;
				std::vector<std::string> params;
				std::string param;

				// Считывание всех параметров после команды
				while (iss >> param) {
					params.push_back(param);
				}

				// Обработка команды для создания скриншота
				if (command == "get_screenshot") {
					TakeScreenshot();
					SendPNGToServer(session_id, "output.png");
				}
				else if (command == "session" && !params.empty()) {
					session_id = std::stoi(params[0]);
					std::cout << "Session ID received: " << session_id << std::endl;
				}
			}).wait(); // Ожидание следующего сообщения
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Websocket exception: " << e.what() << std::endl;
	}
}


/**
* Получение текущего местоположения программы
*/
std::string GetCurrentExecutablePath() {
	char buffer[MAX_PATH];
	if (GetModuleFileNameA(NULL, buffer, MAX_PATH) == 0) {
		// Обработка ошибки, если не удалось получить путь
		std::cerr << "Failed to get executable path: " << GetLastError() << std::endl;
		return "";
	}
	return std::string(buffer);
}


/**
* Иницализация автозапуска приложения при перезаходе в систему
*/
bool static SetAutorunValue(bool enable) {
	const char* app_name = "Work Controller";
	const char* app_path = GetCurrentExecutablePath().c_str();

	HKEY hKey;
	const char* dir = "Software\\Microsoft\\Windows\\CurrentVersion\\Run";

	long result = RegOpenKeyExA(HKEY_CURRENT_USER, dir, 0, KEY_WRITE, &hKey);
	if (result != ERROR_SUCCESS) {
		return false;
	}

	if (enable) {
		result = RegSetValueExA(hKey, app_name, 0, REG_SZ, (BYTE*)app_path, strlen(app_path) + 1);
	}
	else {
		result = RegDeleteValueA(hKey, app_name);
	}

	RegCloseKey(hKey);
	return result == ERROR_SUCCESS;
}


/**
* Проверка на существование пользователя в системе
*/
bool static CheckUserExists(std::string username) {
	CURL* curl;
	CURLcode res;
	bool success = false;
	long http_code = 0;

	std::ostringstream url;
	url << "http://localhost:8000/user/" << username;
	std::cout << "Trying to get user: " << url.str() << std::endl;

	curl = curl_easy_init();
	if (curl) {
		curl_easy_setopt(curl, CURLOPT_URL, url.str().c_str());
		curl_easy_setopt(curl, CURLOPT_HTTPGET, 1L);
		curl_easy_setopt(curl, CURLOPT_NOBODY, 0L);

		res = curl_easy_perform(curl);
		std::cout << std::endl;

		if (res == CURLE_OK) {
			curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
			if (http_code == 200) {
				std::cout << "Successfully received user data." << std::endl;
				success = true;
			}
			else std::cout << "Failed to get user, HTTP status code: " << http_code << std::endl;
		}
		else std::cerr << "Curl failed: " << curl_easy_strerror(res) << std::endl;

		curl_easy_cleanup(curl);
	}

	return success;
}


/**
* Конвертер строк
*/
std::string wstringToString(const std::wstring& wstr) {
	std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
	return converter.to_bytes(wstr);
}


std::wstring GetComputerName() {
	wchar_t computerName[MAX_COMPUTERNAME_LENGTH + 1];
	DWORD size = sizeof(computerName) / sizeof(computerName[0]);

	if (GetComputerNameW(computerName, &size)) {
		return std::wstring(computerName);
	}
	else {
		std::wcerr << L"Failed to get computer name" << std::endl;
		return L"";
	}
}


std::wstring GetDomainName() {
	wchar_t domainName[256]; // Установите размер достаточный для вашего доменного имени
	DWORD size = sizeof(domainName) / sizeof(domainName[0]);

	if (GetComputerNameExW(ComputerNameDnsDomain, domainName, &size)) {
		return std::wstring(domainName);
	}
	else {
		std::wcerr << L"Failed to get domain name" << std::endl;
		return L"";
	}
}


int main() {
	// Получаем дескриптор окна
	HWND hWnd = GetConsoleWindow();
	ShowWindow(hWnd, SW_HIDE);

	// Получение Username
	std::string username = LoadAuthFromFile();
	if (username.empty()) {
		// Запрашиваем Username, если он отсутствует
		ShowWindow(hWnd, SW_SHOW);
		do {
			username = GetAuthFromUser();
			SetAutorunValue(true);
		} while (!CheckUserExists(username));
		SaveAuthToFile(username);
		ShowWindow(hWnd, SW_HIDE);
	}

	// Запуск веб-сокета
	ConnectWebSocket(MakeUri(username, wstringToString(GetComputerName()), wstringToString(GetDomainName())));
}