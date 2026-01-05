from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(128), nullable=False)
    lastname = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, nullable=False, index=True)
    role = Column(String(32), nullable=False, default='USER')
    password_hash = Column(String(256), nullable=False)
    password_salt = Column(String(128), nullable=False)
    public_key = Column(Text, nullable=True)
    first_login = Column(Boolean, nullable=False, default=True)
    user_date_created = Column(DateTime, server_default=func.now())


class CodeFile(Base):
    __tablename__ = 'code_files'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(512), nullable=False)
    file_hash = Column(String(512), nullable=False)
    file_date_created = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship('User')


class Signature(Base):
    __tablename__ = 'signatures'
    id = Column(Integer, primary_key=True, index=True)
    signature_value = Column(Text, nullable=False)
    signature_date = Column(DateTime, server_default=func.now())
    file_id = Column(Integer, ForeignKey('code_files.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)


class UsersLog(Base):
    __tablename__ = 'users_logs'
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(128), nullable=False)
    file_name = Column(String(512), nullable=True)
    file_hash = Column(String(512), nullable=True)
    signature_value = Column(Text, nullable=True)
    public_key = Column(Text, nullable=True)
    success = Column(Integer, nullable=False)
    log_date = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship('User')
