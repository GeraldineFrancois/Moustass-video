from sqlalchemy.orm import Session
from . import models, security
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def create_user_with_keys(db: Session, firstname: str, lastname: str, email: str, password: str, role: str = 'USER'):
    # generate RSA keypair and persist public key; return private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    user = models.User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        password_hash=security.hash_password(password),
        public_key=public_key,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, private_pem


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def log_event(db: Session, action_type: str, user_id: int = None, success: bool = True):
    entry = models.LogEntry(user_id=user_id, action_type=action_type, success=success)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_logs_for_user(db: Session, user_id: int):
    return db.query(models.LogEntry).filter(models.LogEntry.user_id == user_id).order_by(models.LogEntry.log_date.desc()).limit(100).all()


def get_all_logs(db: Session):
    return db.query(models.LogEntry).order_by(models.LogEntry.log_date.desc()).limit(500).all()
