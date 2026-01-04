from sqlalchemy.orm import Session
from . import models
from .schemas import UserCreate
from .security import hash_password
import os
import secrets


def create_user(db: Session, user: UserCreate, role: str = 'USER'):
    salt = secrets.token_hex(16)
    # Use passlib's bcrypt which handles salting internally. Do not append our own salt
    # (bcrypt has a 72-byte input limit). We still store an application-level salt
    # for compatibility/audit, but we do not include it in the hash input.
    phash = hash_password(user.password)
    db_user = models.User(
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        role=role,
        password_hash=phash,
        password_salt=salt,
        first_login=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def delete_user(db: Session, user_id: int):
    u = db.query(models.User).get(user_id)
    if u:
        db.delete(u)
        db.commit()
        return True
    return False


def set_public_key(db: Session, user_id: int, public_pem: str):
    u = db.query(models.User).get(user_id)
    if u:
        u.public_key = public_pem
        u.first_login = False
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    return None


def log_event(db: Session, action_type: str, user_id: int, success: int = 1, **kwargs):
    entry = models.UsersLog(
        action_type=action_type,
        user_id=user_id,
        success=1 if success else 0,
        file_name=kwargs.get('file_name'),
        file_hash=kwargs.get('file_hash'),
        signature_value=kwargs.get('signature_value'),
        public_key=kwargs.get('public_key'),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
