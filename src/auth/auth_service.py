"""Higher-level auth operations.

This module contains orchestration logic that combines CRUD operations,
key generation and other small workflows. Keeping this separate from the
API layer keeps handlers readable and easy to test.
"""

import httpx
from . import crud

# Security Service URL (use Docker service name in production)
# SECURITY: HTTP is acceptable here as communication is internal to Docker network
# In a multi-datacenter deployment, upgrade to HTTPS with mTLS
SECURITY_SERVICE_URL = "http://security-service:8003"


def create_user_with_keys(db, user_data, role='USER'):
	"""Create a user record, generate an RSA keypair and persist the public key.

	The private key is returned so the caller (frontend) can present it to the
	user exactly once. The private key is NOT stored by the server.
	"""
	# Create the DB user row
	user = crud.create_user(db, user_data, role=role)

	# Generate RSA keypair via Security service
	try:
		with httpx.Client() as client:
			response = client.post(
				f"{SECURITY_SERVICE_URL}/api/security/keys/generate",
				data={"key_size": 3072, "service_name": "auth"}
			)
			response.raise_for_status()
			key_data = response.json()
			private_pem = key_data["private_key"]
			public_pem = key_data["public_key"]
	except Exception as e:
		# Cleanup: delete user if key generation fails
		crud.delete_user(db, user.id)
		raise ValueError(f"Failed to generate keys: {str(e)}")

	# Persist only the public key
	crud.set_public_key(db, user.id, public_pem)

	# Return the ORM user and the private key PEM (one-time display)
	return user, private_pem
