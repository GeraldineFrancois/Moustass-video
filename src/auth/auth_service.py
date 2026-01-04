""" Authentication service: orchestrate user creation, KMS and simple flows. """
from .kms import generate_rsa_keypair
from . import crud


def create_user_with_keys(db, user_data, role='USER'):
	# create user record
	user = crud.create_user(db, user_data, role=role)
	# generate keypair and persist public key
	private_pem, public_pem = generate_rsa_keypair()
	crud.set_public_key(db, user.id, public_pem)
	# return private key to caller so it can be shown once
	return user, private_pem
