"""
Security Service API - REST endpoints for crypto and scanning
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Form, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import base64

from .database import get_db
from .models import SecurityAuditLog, ScanResult, SecurityEventType
from .crypto import (
    generate_rsa_keypair,
    sign_data,
    verify_signature,
    generate_aes_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    encrypt_rsa_oaep,
    decrypt_rsa_oaep
)
from .jwt_validator import validate_token, extract_user_from_header
from .scanner import SecurityScanner

router = APIRouter(prefix="/api/security", tags=["Security"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class KeyPairResponse(BaseModel):
    private_key: str
    public_key: str
    key_size: int


class SignRequest(BaseModel):
    data_b64: str
    private_key_pem: str


class SignResponse(BaseModel):
    signature_b64: str


class VerifyRequest(BaseModel):
    data_b64: str
    signature_b64: str
    public_key_pem: str


class VerifyResponse(BaseModel):
    is_valid: bool


class AESKeyResponse(BaseModel):
    key_b64: str
    key_size: int


class EncryptAESRequest(BaseModel):
    data_b64: str
    key_b64: str
    iv_b64: Optional[str] = None


class EncryptAESResponse(BaseModel):
    ciphertext_b64: str
    iv_b64: str


class DecryptAESRequest(BaseModel):
    ciphertext_b64: str
    key_b64: str
    iv_b64: str


class DecryptAESResponse(BaseModel):
    plaintext_b64: str


class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# CRYPTOGRAPHY ENDPOINTS
# ============================================================================

@router.get("/keys/admin-public")
async def get_admin_public_key():
    """
    Récupère la clé publique RSA de l'admin pour chiffrer les clés AES.
    Pour simplifier, génère une clé statique à chaque appel.
    TODO: Implémenter un stockage persistant sécurisé.
    """
    try:
        # Générer une paire de clés RSA-3072
        # Note: Pour la production, cette clé devrait être stockée de manière sécurisée
        private_key_pem, public_key_pem = generate_rsa_keypair(key_size=3072)
        
        # Retourner uniquement la clé publique
        return {"public_key_pem": public_key_pem}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating admin public key: {str(e)}")


@router.post("/keys/generate", response_model=KeyPairResponse)
async def generate_keys(
    key_size: int = 3072,
    service_name: str = Form("unknown"),
    db: Session = Depends(get_db)
):
    """
    Generate RSA keypair
    
    - **key_size**: 3072 (recommended) or 2048
    - Returns: private and public keys in PEM format
    """
    try:
        private_pem, public_pem = generate_rsa_keypair(key_size)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.KEY_GENERATED,
            service_name=service_name,
            operation_details=f"RSA-{key_size} keypair generated",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return KeyPairResponse(
            private_key=private_pem,
            public_key=public_pem,
            key_size=key_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key generation failed: {str(e)}")


@router.post("/sign", response_model=SignResponse)
async def sign(
    request: SignRequest,
    service_name: str = "unknown",
    db: Session = Depends(get_db)
):
    """
    Sign data with RSA private key
    
    - **data_b64**: Base64-encoded data to sign
    - **private_key_pem**: Private key in PEM format
    - **service_name**: (query param) Service name for audit logging
    """
    try:
        data = base64.b64decode(request.data_b64)
        signature = sign_data(data, request.private_key_pem)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.SIGNATURE_CREATED,
            service_name=service_name,
            operation_details=f"Data signed ({len(data)} bytes)",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return SignResponse(signature_b64=signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    request: VerifyRequest,
    service_name: str = "unknown",
    db: Session = Depends(get_db)
):
    """
    Verify RSA signature
    
    - **data_b64**: Base64-encoded original data
    - **signature_b64**: Base64-encoded signature
    - **public_key_pem**: Public key in PEM format
    """
    try:
        data = base64.b64decode(request.data_b64)
        is_valid = verify_signature(data, request.signature_b64, request.public_key_pem)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.SIGNATURE_VERIFIED,
            service_name=service_name,
            operation_details=f"Signature verification: {'valid' if is_valid else 'invalid'}",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return VerifyResponse(is_valid=is_valid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aes/generate-key", response_model=AESKeyResponse)
async def generate_aes(key_size: int = 256):
    """
    Generate AES key
    
    - **key_size**: 128, 192, or 256 bits
    """
    try:
        key_b64 = generate_aes_key(key_size)
        return AESKeyResponse(key_b64=key_b64, key_size=key_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aes/encrypt", response_model=EncryptAESResponse)
async def encrypt_aes(
    request: EncryptAESRequest,
    service_name: str = Form("unknown"),
    db: Session = Depends(get_db)
):
    """
    Encrypt data with AES-GCM
    
    - **data_b64**: Base64-encoded plaintext
    - **key_b64**: Base64-encoded AES key
    - **iv_b64**: Optional IV (generated if not provided)
    """
    try:
        data = base64.b64decode(request.data_b64)
        iv = base64.b64decode(request.iv_b64) if request.iv_b64 else None
        
        ciphertext, iv_used = encrypt_aes_gcm(data, request.key_b64, iv)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.DATA_ENCRYPTED,
            service_name=service_name,
            operation_details=f"AES-GCM encryption ({len(data)} bytes)",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return EncryptAESResponse(
            ciphertext_b64=base64.b64encode(ciphertext).decode(),
            iv_b64=base64.b64encode(iv_used).decode()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aes/decrypt", response_model=DecryptAESResponse)
async def decrypt_aes(
    request: DecryptAESRequest,
    service_name: str = Form("unknown"),
    db: Session = Depends(get_db)
):
    """
    Decrypt data with AES-GCM
    
    - **ciphertext_b64**: Base64-encoded ciphertext
    - **key_b64**: Base64-encoded AES key
    - **iv_b64**: Base64-encoded IV
    """
    try:
        ciphertext = base64.b64decode(request.ciphertext_b64)
        iv = base64.b64decode(request.iv_b64)
        
        plaintext = decrypt_aes_gcm(ciphertext, request.key_b64, iv)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.DATA_DECRYPTED,
            service_name=service_name,
            operation_details=f"AES-GCM decryption ({len(plaintext)} bytes)",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return DecryptAESResponse(
            plaintext_b64=base64.b64encode(plaintext).decode()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")


# ============================================================================
# JWT VALIDATION ENDPOINT
# ============================================================================

@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_jwt(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Validate JWT token from Authorization header
    
    Returns user info if valid
    """
    try:
        if not authorization:
            return TokenValidationResponse(valid=False)
        
        user_id = extract_user_from_header(authorization)
        token = authorization.split()[1]
        user_info = validate_token(token)
        
        # Audit log
        audit = SecurityAuditLog(
            event_type=SecurityEventType.TOKEN_VALIDATED,
            service_name="security",
            user_id=user_id,
            operation_details="JWT validated",
            success=True
        )
        db.add(audit)
        db.commit()
        
        return TokenValidationResponse(
            valid=True,
            user_id=user_info["user_id"],
            email=user_info.get("email"),
            role=user_info.get("role")
        )
    except Exception:
        return TokenValidationResponse(valid=False)


# ============================================================================
# SECURITY SCANNING ENDPOINTS
# ============================================================================

@router.post("/scan/snyk-code")
async def scan_snyk_code(
    target_path: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Run Snyk Code security scan
    
    Returns vulnerability report
    """
    scanner = SecurityScanner()
    result = scanner.scan_snyk_code(target_path)
    
    # Save scan result
    if result["status"] == "completed":
        vulns = result.get("vulnerabilities", {})
        scan_record = ScanResult(
            scan_type="snyk_code",
            service_name="all",
            severity_critical=vulns.get("by_severity", {}).get("critical", 0),
            severity_high=vulns.get("by_severity", {}).get("high", 0),
            severity_medium=vulns.get("by_severity", {}).get("medium", 0),
            severity_low=vulns.get("by_severity", {}).get("low", 0),
            total_issues=vulns.get("total", 0),
            scan_status="completed"
        )
        db.add(scan_record)
        db.commit()
    
    return result


@router.post("/scan/snyk-deps")
async def scan_snyk_deps(
    target_path: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Run Snyk dependency scan
    
    Returns dependency vulnerability report
    """
    scanner = SecurityScanner()
    result = scanner.scan_snyk_dependencies(target_path)
    
    # Save scan result
    if result["status"] == "completed":
        vulns = result.get("vulnerabilities", {})
        scan_record = ScanResult(
            scan_type="snyk_dependencies",
            service_name="all",
            severity_critical=vulns.get("by_severity", {}).get("critical", 0),
            severity_high=vulns.get("by_severity", {}).get("high", 0),
            severity_medium=vulns.get("by_severity", {}).get("medium", 0),
            severity_low=vulns.get("by_severity", {}).get("low", 0),
            total_issues=vulns.get("total", 0),
            scan_status="completed"
        )
        db.add(scan_record)
        db.commit()
    
    return result


@router.post("/scan/sonarqube")
async def scan_sonarqube(
    project_key: str = "moustass-video",
    db: Session = Depends(get_db)
):
    """
    Run SonarQube scan
    
    Returns scan status and dashboard URL
    """
    scanner = SecurityScanner()
    result = scanner.scan_sonarqube(project_key)
    
    # Save scan result
    if result["status"] == "completed":
        scan_record = ScanResult(
            scan_type="sonarqube",
            service_name="all",
            scan_status="completed"
        )
        db.add(scan_record)
        db.commit()
    
    return result


@router.get("/scan/summary")
async def get_scan_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive security scan summary
    
    Runs all configured scanners
    """
    scanner = SecurityScanner()
    return scanner.get_scan_summary()


@router.get("/scan/history")
async def get_scan_history(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent scan history
    """
    scans = db.query(ScanResult).order_by(ScanResult.created_at.desc()).limit(limit).all()
    
    return {
        "scans": [
            {
                "id": s.id,
                "scan_type": s.scan_type,
                "service_name": s.service_name,
                "total_issues": s.total_issues,
                "critical": s.severity_critical,
                "high": s.severity_high,
                "medium": s.severity_medium,
                "low": s.severity_low,
                "status": s.scan_status,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in scans
        ]
    }


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 50,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get security audit logs
    """
    query = db.query(SecurityAuditLog).order_by(SecurityAuditLog.timestamp.desc())
    
    if event_type:
        query = query.filter(SecurityAuditLog.event_type == event_type)
    
    logs = query.limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "event_type": log.event_type.value,
                "service_name": log.service_name,
                "user_id": log.user_id,
                "operation_details": log.operation_details,
                "success": log.success,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            }
            for log in logs
        ]
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Security service health check"""
    return {
        "status": "healthy",
        "service": "security",
        "version": "1.0.0"
    }
