from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Модель стандартного пользователя"""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    """Модель сессии, принадлежащая пользователю"""

    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates='sessions')
    start_time = Column(DateTime(timezone=True), default=func.now())
    last_active_time = Column(DateTime(timezone=True), default=None, nullable=True)
    ip_address = Column(String, default=None, nullable=True)
    domain = Column(String, default=None, nullable=True)
    machine = Column(String, default=None, nullable=True)
    screenshots = relationship("Screenshot", back_populates='session')


class Screenshot(Base):
    """Модель скриншота, привязанная к текущей сессии"""

    __tablename__ = 'screenshots'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    image_data = Column(LargeBinary)
    create_at = Column(DateTime, default=func.now())
    session = relationship("Session", back_populates="screenshots")
