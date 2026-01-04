"""Database CRUD helpers for the auth subsystem.

Small, focused functions that the service layer and API use. Keep logic
minimal here — just perform DB operations and return ORM objects.
"""

from sqlalchemy.orm import Session
from . import models
from .schemas import UserCreate
from .security import hash_password
import os
import secrets


def create_user(db: Session, user: UserCreate, role: str = 'USER'):
    # Generate an application-level salt for auditing/compatibility purposes.
    # Note: we DO NOT append this salt to the password before hashing because
    # modern schemes (passlib) handle salting internally and bcrypt has a 72
    # byte input limit.
    salt = secrets.token_hex(16)
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
    """Return the first user matching `email` or None."""
    return db.query(models.User).filter(models.User.email == email).first()


def delete_user(db: Session, user_id: int):
    # Use session get by primary key
    u = db.query(models.User).get(user_id)
    if u:
        db.delete(u)
        db.commit()
        return True
    return False


def set_public_key(db: Session, user_id: int, public_pem: str):
    """Store the user's public key and clear the `first_login` flag."""
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
    # Lightweight audit log used by the auth service (login, create, delete)
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
