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


@app.get('/health')
def health():
	"""Healthcheck simple pour Docker Compose."""
	return {"status": "healthy", "service": "auth-service"}


@app.get('/services', response_class=HTMLResponse)
def services_portal(request: Request):
	"""Portail de navigation entre Auth et Video services."""
	return templates.TemplateResponse('portal.html', {'request': request})


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
		# Générer aussi un JWT pour que l'utilisateur puisse s'authentifier immédiatement
		token = security.create_access_token({'sub': user_obj.email, 'role': user_obj.role, 'user_id': user_obj.id})
		return {
			'user': schemas.UserOut.from_orm(user_obj),
			'private_key': private_key,
			'access_token': token,
			'token_type': 'bearer'
		}
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
		# Générer aussi un JWT pour que l'utilisateur puisse s'authentifier immédiatement
		token = security.create_access_token({'sub': user_obj.email, 'role': user_obj.role, 'user_id': user_obj.id})
		return {
			'user': schemas.UserOut.from_orm(user_obj),
			'private_key': private_key,
			'access_token': token,
			'token_type': 'bearer'
		}
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


@app.get('/me')
def me(request: Request, db: Session = Depends(get_db)):
	"""Return current user's public info based on Bearer token in Authorization header.

	Development helper used by dashboards to fetch the authenticated user's
	public key and email. Returns 401 if token missing/invalid.
	"""
	auth = request.headers.get('authorization', '')
	if not auth.lower().startswith('bearer '):
		raise HTTPException(status_code=401, detail='Missing bearer token')
	token = auth.split(' ', 1)[1]
	payload = security.decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail='Invalid token')
	email = payload.get('sub')
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail='User not found')
	return {'email': u.email, 'public_key': u.public_key, 'role': u.role}


@app.get('/logs')
def my_logs(request: Request, db: Session = Depends(get_db)):
	"""Return recent connection logs for the authenticated user."""
	auth = request.headers.get('authorization', '')
	if not auth.lower().startswith('bearer '):
		raise HTTPException(status_code=401, detail='Missing bearer token')
	token = auth.split(' ', 1)[1]
	payload = security.decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail='Invalid token')
	email = payload.get('sub')
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail='User not found')
	logs = crud.get_logs_for_user(db, u.id)
	# serialize minimal fields
	out = []
	for e in logs:
		out.append({'id': e.id, 'user_id': e.user_id, 'action_type': e.action_type, 'success': bool(e.success), 'timestamp': e.log_date.isoformat() if e.log_date else None})
	return {'logs': out}


@app.get('/admin/logs')
def admin_logs(request: Request, db: Session = Depends(get_db)):
	"""Admin-only: return recent logs for all users."""
	auth = request.headers.get('authorization', '')
	if not auth.lower().startswith('bearer '):
		raise HTTPException(status_code=401, detail='Missing bearer token')
	token = auth.split(' ', 1)[1]
	payload = security.decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail='Invalid token')
	email = payload.get('sub')
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail='User not found')
	if (u.role or '').upper() != 'ADMIN':
		raise HTTPException(status_code=403, detail='Admin access required')
	logs = crud.get_all_logs(db)
	out = []
	# include user role by querying user per entry (keeps it simple)
	for e in logs:
		user = None
		try:
			user = db.query(database.Base.classes.users).get(e.user_id)
		except Exception:
			user = None
		role = None
		if user:
			role = getattr(user, 'role', None)
		out.append({'id': e.id, 'user_id': e.user_id, 'role': role, 'action_type': e.action_type, 'success': bool(e.success), 'timestamp': e.log_date.isoformat() if e.log_date else None})
	return {'logs': out}
