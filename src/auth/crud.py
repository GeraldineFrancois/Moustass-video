"""Helpers CRUD pour le module d'authentification.

Ce fichier contient des fonctions simples pour créer, lire, mettre à jour
et supprimer des enregistrements liés aux utilisateurs et aux journaux.
Chaque fonction réalise une opération SQLAlchemy minimale et retourne des
objets ORM. Les règles métiers sont volontairement légères ici : la logique
complexe appartient aux services ou aux contrôleurs.
"""

from sqlalchemy.orm import Session
from . import models
from .schemas import UserCreate
from .security import hash_password
import os
import secrets


def create_user(db: Session, user: UserCreate, role: str = 'USER'):
    # Génère un sel applicatif pour l'audit et la compatibilité.
    # Remarque : on N'APPEND PAS ce sel au mot de passe avant le hash car
    # passlib gère le salage et bcrypt a une limite d'entrée (72 bytes).
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
    """Retourne le premier utilisateur correspondant à `email` ou None."""
    return db.query(models.User).filter(models.User.email == email).first()


def delete_user(db: Session, user_id: int):
    # Supprime un utilisateur en utilisant sa clé primaire
    u = db.query(models.User).get(user_id)
    if u:
        db.delete(u)
        db.commit()
        return True
    return False


def set_public_key(db: Session, user_id: int, public_pem: str):
    """Stocke la clé publique de l'utilisateur et désactive `first_login`."""
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
    # Journal d'audit léger utilisé par le service (login, création, suppression)
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


def get_logs_for_user(db: Session, user_id: int, limit: int = 100):
    """Retourne les entrées de journal récentes pour un utilisateur (plus récentes d'abord)."""
    return db.query(models.UsersLog).filter(models.UsersLog.user_id == user_id).order_by(models.UsersLog.log_date.desc()).limit(limit).all()


def get_all_logs(db: Session, limit: int = 500):
    """Retourne les journaux récents pour tous les utilisateurs (plus récents d'abord)."""
    return db.query(models.UsersLog).order_by(models.UsersLog.log_date.desc()).limit(limit).all()
