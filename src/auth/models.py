from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(128), nullable=True)
    lastname = Column(String(128), nullable=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    public_key = Column(Text, nullable=True)
    role = Column(String(32), default='USER')
    created_at = Column(DateTime, default=datetime.utcnow)

class LogEntry(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action_type = Column(String(64), nullable=False)
    success = Column(Boolean, default=True)
    log_date = Column(DateTime, default=datetime.utcnow)
