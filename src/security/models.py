"""
Security Service Models
Audit logs and security events
"""

from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Boolean, Enum
from datetime import datetime
import enum
from .database import Base


class SecurityEventType(enum.Enum):
    """Types of security events"""
    KEY_GENERATED = "KEY_GENERATED"
    SIGNATURE_CREATED = "SIGNATURE_CREATED"
    SIGNATURE_VERIFIED = "SIGNATURE_VERIFIED"
    DATA_ENCRYPTED = "DATA_ENCRYPTED"
    DATA_DECRYPTED = "DATA_DECRYPTED"
    TOKEN_VALIDATED = "TOKEN_VALIDATED"
    SCAN_EXECUTED = "SCAN_EXECUTED"
    VULNERABILITY_DETECTED = "VULNERABILITY_DETECTED"


class SecurityAuditLog(Base):
    """Audit log for all security operations"""
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(Enum(SecurityEventType, native_enum=False), nullable=False)
    service_name = Column(String(50), nullable=False)  # auth, video, etc.
    user_id = Column(Integer, nullable=True)  # if applicable
    operation_details = Column(Text, nullable=True)  # JSON details
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


class ScanResult(Base):
    """Security scan results from Snyk/SonarQube"""
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_type = Column(String(50), nullable=False)  # snyk_code, snyk_deps, sonarqube
    service_name = Column(String(50), nullable=False)
    severity_critical = Column(Integer, default=0)
    severity_high = Column(Integer, default=0)
    severity_medium = Column(Integer, default=0)
    severity_low = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    scan_details = Column(Text, nullable=True)  # JSON
    scan_status = Column(String(20), default="completed")  # pending, completed, failed
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
