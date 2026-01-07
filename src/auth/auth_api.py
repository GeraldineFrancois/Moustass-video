""" FastAPI endpoints for authentication and minimal admin/client UI. """
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from . import schemas, crud, security, auth_service
from .database import init_db, get_db
from . import database
from sqlalchemy.orm import Session
import os

# Error message constants to avoid duplication
ERROR_USER_NOT_FOUND = 'User not found'
ERROR_MISSING_BEARER = 'Missing bearer token'
ERROR_INVALID_TOKEN = 'Invalid token'

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'templates'))

app = FastAPI(title='Auth Service')


@app.on_event('startup')
def on_startup():
	init_db()


@app.get('/', response_class=HTMLResponse)
def login_page(request: Request):
	return templates.TemplateResponse('login.html', {'request': request})


# -------------------- Request Parsing Helpers -----------------------------------
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


# -------------------- Authorization Helpers -----------------------------------
def _extract_bearer_token(request: Request) -> str:
	"""Extract Bearer token from Authorization header.

	Raises HTTPException 401 if missing or malformed.
	Returns the token string (without 'Bearer ' prefix).
	"""
	auth = request.headers.get('authorization', '')
	if not auth.lower().startswith('bearer '):
		raise HTTPException(status_code=401, detail=ERROR_MISSING_BEARER)
	return auth.split(' ', 1)[1]


def _get_authenticated_user(request: Request, db: Session):
	"""Extract Bearer token, decode JWT, and return user object.

	Raises HTTPException 401 if token invalid, or 404 if user not found.
	Returns the user ORM object.
	"""
	token = _extract_bearer_token(request)
	payload = security.decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail=ERROR_INVALID_TOKEN)
	email = payload.get('sub')
	user = crud.get_user_by_email(db, email)
	if not user:
		raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
	return user


# -------------------- Log Serialization Helper ---------------------------------
def _serialize_log_entry(log_entry, include_user_role: bool = False, user_obj=None) -> dict:
	"""Convert a log ORM object to a serializable dict.

	Args:
		log_entry: The LogEvent ORM object
		include_user_role: If True, include the user's role field
		user_obj: If include_user_role is True, pass the user object to avoid extra DB query

	Returns a dict with id, action_type, success, timestamp, and optionally user_id and role.
	"""
	result = {
		'id': log_entry.id,
		'action_type': log_entry.action_type,
		'success': bool(log_entry.success),
		'timestamp': log_entry.log_date.isoformat() if log_entry.log_date else None,
	}
	if include_user_role:
		result['user_id'] = log_entry.user_id
		result['role'] = user_obj.role if user_obj else None
	return result


# -------------------- User Creation Helper ------------------------------------
async def _create_user_common(request: Request, db: Session, role: str) -> dict:
	"""Common logic for creating admin or client user accounts.

	Validates password, checks for existing email, creates user with keys.
	Returns dict with user info and private key.

	Args:
		request: The HTTP request
		db: Database session
		role: 'ADMIN' or 'USER'

	Raises HTTPException on validation failures.
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
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role=role)
		return {'user': schemas.UserOut.from_orm(user_obj), 'private_key': private_key}
	except Exception:
		import traceback
		tb = traceback.format_exc()
		return JSONResponse(status_code=500, content={"detail": tb})


# -------------------- Login Helper -------------------------------------------
def _log_failed_login(email: str, password: str, user):
	"""Log authentication failure with diagnostic info for debugging."""
	import logging
	logger = logging.getLogger('uvicorn.error')
	logger.warning(
		'Login failed for %s; pw_len=%d hash_prefix=%s salt_len=%d',
		email,
		len(password),
		(user.password_hash or '')[:10] if user else 'N/A',
		len(user.password_salt or '') if user else 0
	)


def _verify_and_migrate_password(user, plain_password: str, db: Session) -> bool:
	"""Verify `plain_password` against several legacy storage formats.

	Returns True on success. If a legacy format was used, re-hash the plain
	password with the current scheme and persist the new hash (best-effort).
	"""
	stored_hash = user.password_hash or ''
	salt = user.password_salt or ''

	def _safe_verify(candidate: str, hash_to_check: str) -> bool:
		"""Call `security.verify_password` and return False on any error."""
		try:
			return bool(hash_to_check) and security.verify_password(candidate, hash_to_check)
		except Exception:
			return False

	# 1) Modern format: password directly verifies against stored_hash
	if _safe_verify(plain_password, stored_hash):
		return True

	# If there's no stored salt, remaining legacy checks are impossible
	if not salt:
		return False

	# 2) Legacy: stored_hash is hash(password + salt)
	if _safe_verify(plain_password + salt, stored_hash):
		_migrate_hash_if_needed(user, plain_password, db)
		return True

	# 3) Legacy appended-salt: stored_hash == real_hash + salt
	if stored_hash.endswith(salt):
		real_hash = stored_hash[:-len(salt)]
		if _safe_verify(plain_password + salt, real_hash):
			_migrate_hash_if_needed(user, plain_password, db)
			return True

	# none matched
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

	Validates input, checks for existing email, and returns user info with private key.
	Delegates to `_create_user_common` to avoid code duplication.
	"""
	return await _create_user_common(request, db, role='ADMIN')


@app.post('/signup_client')
async def signup_client(request: Request, db: Session = Depends(get_db)):
	"""Create a regular user account (client).

	Delegates to `_create_user_common` to avoid code duplication with signup_admin.
	"""
	return await _create_user_common(request, db, role='USER')


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
	"""Authenticate user with email/password and return JWT token.

	Supports both form and JSON payloads. Handles legacy password formats
	and migrates hashes to current scheme on success.
	"""
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
		_log_failed_login(payload.email, payload.password, user)
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


@app.get('/me')
def me(request: Request, db: Session = Depends(get_db)):
	"""Return current user's public info based on Bearer token.

	Returns email, public_key, and role. Used by dashboards to fetch
	authenticated user's public key. Returns 401 if token invalid/missing.
	"""
	user = _get_authenticated_user(request, db)
	return {'email': user.email, 'public_key': user.public_key, 'role': user.role}


@app.get('/logs')
def my_logs(request: Request, db: Session = Depends(get_db)):
	"""Return recent connection logs for the authenticated user."""
	user = _get_authenticated_user(request, db)
	logs = crud.get_logs_for_user(db, user.id)
	# Serialize log entries
	out = [_serialize_log_entry(log_entry) for log_entry in logs]
	return {'logs': out}


@app.get('/admin/logs')
def admin_logs(request: Request, db: Session = Depends(get_db)):
	"""Admin-only endpoint: return recent logs for all users.

	Requires ADMIN role. Includes user role information in each log entry.
	"""
	user = _get_authenticated_user(request, db)
	if (user.role or '').upper() != 'ADMIN':
		raise HTTPException(status_code=403, detail='Admin access required')

	logs = crud.get_all_logs(db)
	out = []
	# Include user role by looking up user for each log entry
	for log_entry in logs:
		log_user = None
		try:
			log_user = db.query(database.Base.classes.users).get(log_entry.user_id)
		except Exception:
			pass
		out.append(_serialize_log_entry(log_entry, include_user_role=True, user_obj=log_user))
	return {'logs': out}
