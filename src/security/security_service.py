"""
Security Service - Main application
Centralized security microservice for Moustass Video platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from security.database import Base, engine
from security.security_api import router as security_router


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Security Microservice",
    description="Centralized security operations for Moustass Video platform",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
        "http://localhost:8003",
        "http://127.0.0.1:8003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register API router
app.include_router(security_router)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Security service welcome page"""
    return {
        "service": "Security Microservice",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "RSA-3072 Key Generation",
            "RSA Signature & Verification",
            "AES-GCM Encryption/Decryption",
            "JWT Token Validation",
            "Snyk Code Scanning",
            "Snyk Dependency Scanning",
            "SonarQube Integration",
            "Security Audit Logs"
        ],
        "documentation": "/docs",
        "endpoints": {
            "crypto": "/api/security/keys/generate, /api/security/sign, /api/security/verify",
            "aes": "/api/security/aes/encrypt, /api/security/aes/decrypt",
            "jwt": "/api/security/validate-token",
            "scanning": "/api/security/scan/snyk-code, /api/security/scan/sonarqube",
            "audit": "/api/security/audit/logs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "security-microservice",
        "version": "1.0.0"
    }


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Service startup"""
    print("\n" + "="*70)
    print("  🔒 SECURITY MICROSERVICE - MOUSTASS VIDEO")
    print("="*70)
    print("\n🛡️  Security Features:")
    print("   ✓ RSA-3072 Key Generation & Management")
    print("   ✓ Digital Signature (Sign & Verify)")
    print("   ✓ AES-GCM Encryption/Decryption")
    print("   ✓ JWT Token Validation")
    print("   ✓ Snyk Code & Dependency Scanning")
    print("   ✓ SonarQube Integration")
    print("   ✓ Security Audit Logging")
    print("\n📚 Documentation: http://localhost:8003/docs")
    print("🌐 Service endpoint: http://localhost:8003")
    print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown"""
    print("🔒 Security Service - Shutting down...")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info",
        reload=False
    )
