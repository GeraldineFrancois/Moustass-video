"""Higher-level auth operations.

This module contains orchestration logic that combines CRUD operations,
key generation and other small workflows. Keeping this separate from the
API layer keeps handlers readable and easy to test.
"""

from .kms import generate_rsa_keypair
from . import crud


def create_user_with_keys(db, user_data, role='USER'):
	"""Create a user record, generate an RSA keypair and persist the public key.

	The private key is returned so the caller (frontend) can present it to the
	user exactly once. The private key is NOT stored by the server.
	"""
	# Create the DB user row
	user = crud.create_user(db, user_data, role=role)

	# Generate an RSA keypair and persist only the public key
	private_pem, public_pem = generate_rsa_keypair()
	crud.set_public_key(db, user.id, public_pem)

	# Return the ORM user and the private key PEM (one-time display)
	return user, private_pem
