""" FastAPI endpoints for authentication and minimal admin/client UI. """
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from . import schemas, crud, security, auth_service
from .database import init_db, get_db
from . import database
from sqlalchemy.orm import Session
import os

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'templates'))

app = FastAPI(title='Auth Service')


@app.on_event('startup')
def on_startup():
	init_db()


@app.get('/', response_class=HTMLResponse)
def login_page(request: Request):
	return templates.TemplateResponse('login.html', {'request': request})


# -------------------- Helpers -------------------------------------------------
def _is_form_request(request: Request) -> bool:
	"""Return True if request likely came from an HTML form (x-www-form-urlencoded)."""
	return request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded')


async def _parse_request(request: Request, fields: tuple):
	"""Parse incoming request as form or JSON and return a dict with requested fields.

	This helper centralizes parsing logic so endpoints remain short and easy to
	read. Missing fields will be preserved for Pydantic validation to catch.
	"""
	if _is_form_request(request):
		form = await request.form()
		return {k: form.get(k) for k in fields}
	# JSON path
	data = await request.json()
	return {k: data.get(k) for k in fields}


def _verify_and_migrate_password(user, plain_password: str, db: Session) -> bool:
	"""Verify `plain_password` against several legacy storage formats.

	Returns True on success. If a legacy format was used, re-hash the plain
	password with the current scheme and persist the new hash (best-effort).
	"""
	stored_hash = user.password_hash or ''
	salt = user.password_salt or ''

	# Try modern verification first (plain password)
	try:
		if stored_hash and security.verify_password(plain_password, stored_hash):
			# already modern format
			return True
	except Exception:
		pass

	# Try legacy case: hash was made over password+salt
	if salt:
		try:
			if security.verify_password(plain_password + salt, stored_hash):
				_migrate_hash_if_needed(user, plain_password, db)
				return True
		except Exception:
			pass

	# Legacy appended-salt: stored_hash actually contains hash + salt appended
	if salt and stored_hash.endswith(salt):
		real_hash = stored_hash[:-len(salt)]
		try:
			if security.verify_password(plain_password + salt, real_hash):
				_migrate_hash_if_needed(user, plain_password, db)
				return True
		except Exception:
			pass

	return False


def _migrate_hash_if_needed(user, plain_password: str, db: Session):
	"""Re-hash the plain password using current scheme and persist.

	This is best-effort and will not raise on failure to avoid breaking login.
	"""
	try:
		new_hash = security.hash_password(plain_password)
		user.password_hash = new_hash
		db.add(user)
		db.commit()
		db.refresh(user)
	except Exception:
		pass



@app.post('/signup_admin')
async def signup_admin(request: Request, db: Session = Depends(get_db)):
	"""Create an admin account.

	Uses `_parse_request` to accept either form or JSON. Validates input via
	`UserCreate` and returns the created user's public fields and a one-time
	private key (PEM) that the client must save immediately.
	"""
	data = await _parse_request(request, ('firstname', 'lastname', 'email', 'password', 'confirm_password'))
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as e:
		raise HTTPException(status_code=422, detail=str(e))

	if user_in.password != user_in.confirm_password:
		raise HTTPException(status_code=400, detail='Passwords do not match')
	if not security.validate_password_strength(user_in.password):
		raise HTTPException(status_code=400, detail='Password does not meet strength requirements')
	if crud.get_user_by_email(db, user_in.email):
		raise HTTPException(status_code=400, detail='Email already registered')

	try:
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role='ADMIN')
		return {'user': schemas.UserOut.from_orm(user_obj), 'private_key': private_key}
	except Exception:
		import traceback
		tb = traceback.format_exc()
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post('/signup_client')
async def signup_client(request: Request, db: Session = Depends(get_db)):
	"""Create a regular user account (client).

	Mirrors `signup_admin` behavior but assigns role `USER`.
	"""
	data = await _parse_request(request, ('firstname', 'lastname', 'email', 'password', 'confirm_password'))
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as e:
		raise HTTPException(status_code=422, detail=str(e))

	if user_in.password != user_in.confirm_password:
		raise HTTPException(status_code=400, detail='Passwords do not match')
	if not security.validate_password_strength(user_in.password):
		raise HTTPException(status_code=400, detail='Password does not meet strength requirements')
	if crud.get_user_by_email(db, user_in.email):
		raise HTTPException(status_code=400, detail='Email already registered')

	try:
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role='USER')
		return {'user': schemas.UserOut.from_orm(user_obj), 'private_key': private_key}
	except Exception:
		import traceback
		tb = traceback.format_exc()
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
	# Parse input (form or JSON) and validate with Pydantic
	data = await _parse_request(request, ('email', 'password'))
	try:
		payload = schemas.LoginRequest(**data)
	except Exception as e:
		raise HTTPException(status_code=422, detail=str(e))

	user = crud.get_user_by_email(db, payload.email)
	if not user:
		raise HTTPException(status_code=401, detail='Invalid credentials')

	# Centralized verification that handles legacy formats and performs
	# migration to the current hash scheme on success.
	if not _verify_and_migrate_password(user, payload.password, db):
		import logging
		logger = logging.getLogger('uvicorn.error')
		logger.warning('Login failed for %s; pw_len=%d hash_prefix=%s salt_len=%d',
					   payload.email, len(payload.password), (user.password_hash or '')[:10],
					   len(user.password_salt or ''))
		raise HTTPException(status_code=401, detail='Invalid credentials')

	# Successful login: return JWT token
	token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
	crud.log_event(db, 'login', user.id, success=1)
	return {'access_token': token, 'token_type': 'bearer', 'role': user.role}


@app.post('/delete_account')
def delete_account(email: str = Form(...), db: Session = Depends(get_db)):
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail='User not found')
	crud.delete_user(db, u.id)
	return {'deleted': True}


@app.get('/admin/dashboard', response_class=HTMLResponse)
def admin_dashboard(request: Request):
	return templates.TemplateResponse('admin.html', {'request': request})


@app.get('/client/dashboard', response_class=HTMLResponse)
def client_dashboard(request: Request):
	return templates.TemplateResponse('client.html', {'request': request})


@app.get('/__debug_user')
def debug_user(email: str, db: Session = Depends(get_db)):
	"""Development-only: return masked hash info for a user to help debug login issues."""
	u = crud.get_user_by_email(db, email)
	if not u:
		return JSONResponse(status_code=404, content={"detail": "not found"})
	# Return only prefix of hash and salt length to avoid leaking full hashes
	return {
		"email": u.email,
		"hash_prefix": (u.password_hash or '')[:60],
		"salt_len": len(u.password_salt or ''),
		"role": u.role,
	}


@app.get('/__debug_db')
def debug_db():
	"""Return the DATABASE_URL value used by the running server (development only)."""
	return {"DATABASE_URL": database.DATABASE_URL}
