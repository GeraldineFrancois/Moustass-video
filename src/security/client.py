"""
Security Client - HTTP client for calling Security Service APIs
Used by Auth and Video services to delegate crypto operations
"""

import httpx
from typing import Tuple, Optional, Dict
import base64


class SecurityClient:
    """Client for Security Microservice"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        """
        Initialize security client
        
        Args:
            base_url: Security service base URL (default: http://localhost:8003)
        """
        self.base_url = base_url
        self.api_base = f"{base_url}/api/security"
    
    async def generate_rsa_keypair(self, key_size: int = 3072, service_name: str = "unknown") -> Tuple[str, str]:
        """
        Generate RSA keypair via Security service
        
        Args:
            key_size: RSA key size (default: 3072)
            service_name: Calling service name for audit
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/keys/generate",
                data={"key_size": key_size, "service_name": service_name}
            )
            response.raise_for_status()
            data = response.json()
            return data["private_key"], data["public_key"]
    
    async def sign_data(self, data: bytes, private_key_pem: str, service_name: str = "unknown") -> str:
        """
        Sign data via Security service
        
        Args:
            data: Bytes to sign
            private_key_pem: Private key in PEM format
            service_name: Calling service name
        
        Returns:
            Base64-encoded signature
        """
        data_b64 = base64.b64encode(data).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/sign",
                json={
                    "data_b64": data_b64,
                    "private_key_pem": private_key_pem
                },
                params={"service_name": service_name}
            )
            response.raise_for_status()
            result = response.json()
            return result["signature_b64"]
    
    async def verify_signature(self, data: bytes, signature_b64: str, public_key_pem: str, service_name: str = "unknown") -> bool:
        """
        Verify signature via Security service
        
        Args:
            data: Original data bytes
            signature_b64: Base64-encoded signature
            public_key_pem: Public key in PEM format
            service_name: Calling service name
        
        Returns:
            True if valid, False otherwise
        """
        data_b64 = base64.b64encode(data).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/verify",
                json={
                    "data_b64": data_b64,
                    "signature_b64": signature_b64,
                    "public_key_pem": public_key_pem
                },
                params={"service_name": service_name}
            )
            response.raise_for_status()
            result = response.json()
            return result["is_valid"]
    
    async def validate_token(self, authorization_header: str) -> Optional[Dict]:
        """
        Validate JWT token via Security service
        
        Args:
            authorization_header: "Bearer <token>"
        
        Returns:
            User info dict if valid, None otherwise
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/validate-token",
                headers={"Authorization": authorization_header}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["valid"]:
                return {
                    "user_id": result["user_id"],
                    "email": result.get("email"),
                    "role": result.get("role")
                }
            return None
    
    async def encrypt_aes(self, data: bytes, key_b64: str, iv_b64: Optional[str] = None, service_name: str = "unknown") -> Tuple[str, str]:
        """
        Encrypt data with AES-GCM via Security service
        
        Args:
            data: Plaintext bytes
            key_b64: Base64-encoded AES key
            iv_b64: Optional IV (generated if not provided)
            service_name: Calling service name
        
        Returns:
            Tuple of (ciphertext_b64, iv_b64)
        """
        data_b64 = base64.b64encode(data).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/aes/encrypt",
                json={
                    "data_b64": data_b64,
                    "key_b64": key_b64,
                    "iv_b64": iv_b64
                },
                params={"service_name": service_name}
            )
            response.raise_for_status()
            result = response.json()
            return result["ciphertext_b64"], result["iv_b64"]
    
    async def decrypt_aes(self, ciphertext_b64: str, key_b64: str, iv_b64: str, service_name: str = "unknown") -> bytes:
        """
        Decrypt data with AES-GCM via Security service
        
        Args:
            ciphertext_b64: Base64-encoded ciphertext
            key_b64: Base64-encoded AES key
            iv_b64: Base64-encoded IV
            service_name: Calling service name
        
        Returns:
            Plaintext bytes
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/aes/decrypt",
                json={
                    "ciphertext_b64": ciphertext_b64,
                    "key_b64": key_b64,
                    "iv_b64": iv_b64
                },
                params={"service_name": service_name}
            )
            response.raise_for_status()
            result = response.json()
            return base64.b64decode(result["plaintext_b64"])


# Singleton instance for easy import
security_client = SecurityClient()
