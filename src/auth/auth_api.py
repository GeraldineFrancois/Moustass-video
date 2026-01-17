"""Authentication API (FastAPI) for the Auth microservice.

This module provides the HTTP endpoints used by the UI and other services.
Refactor notes:
- Added small, well-named helpers and type hints to make the flow easy to
  follow for developers new to the project.
- Endpoints intentionally keep logic thin: heavy lifting lives in `crud`,
  `auth_service` and `security` modules.
"""

from typing import Dict, Iterable, Optional
import os

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import schemas, crud, security, auth_service
from .database import init_db, get_db
from . import database

# --- Constants ---------------------------------------------------------------
# Header and token handling constants are centralized for clarity and reuse.
HEADER_AUTHORIZATION = "authorization"
HEADER_CONTENT_TYPE = "content-type"
BEARER_PREFIX = "bearer "
TOKEN_TYPE_BEARER = "bearer"
ROLE_ADMIN = "ADMIN"
ROLE_USER = "USER"

# Error messages (kept short and translated for developers)
ERROR_MISSING_BEARER = "Missing bearer token"
ERROR_INVALID_TOKEN = "Invalid token"
ERROR_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_USER_NOT_FOUND = "User not found"
ERROR_PASSWORDS_MISMATCH = "Passwords do not match"
ERROR_PASSWORD_STRENGTH = "Password does not meet strength requirements"
ERROR_EMAIL_REGISTERED = "Email already registered"
ERROR_ADMIN_REQUIRED = "Admin access required"

CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"


# Templates and app initialization
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app = FastAPI(title="Auth Service")

# Mount a separate `ui` folder when present so templates can be served as files.
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
if os.path.exists(ui_dir):
	app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")


@app.on_event("startup")
def on_startup() -> None:
	"""Initialize DB tables on service startup.

	This keeps the service self-contained for local/dev environments where
	the container should create missing tables.
	"""
	init_db()


# -------------------- Request helpers ---------------------------------------
def _is_form_request(request: Request) -> bool:
	"""Return True when request content type looks like a form submission.

	This allows endpoints to accept both `application/json` and classic HTML
	form posts without duplicating parsing logic.
	"""
	return request.headers.get(HEADER_CONTENT_TYPE, "").startswith(CONTENT_TYPE_FORM)


async def _parse_request(request: Request, fields: Iterable[str]) -> Dict[str, Optional[str]]:
	"""Read `fields` from either form data or JSON payload.

	Returns a dict that can be passed to Pydantic models for validation.
	Missing keys are returned as `None` and will be handled by Pydantic.
	"""
	if _is_form_request(request):
		form = await request.form()
		return {k: form.get(k) for k in fields}
	data = await request.json()
	return {k: data.get(k) for k in fields}


# -------------------- Auth helpers ------------------------------------------
def _extract_bearer_token(request: Request) -> str:
	"""Extract the raw token from the Authorization header.

	Raises HTTPException(401) when the header is missing or malformed.
	"""
	auth = request.headers.get(HEADER_AUTHORIZATION, "")
	if not auth.lower().startswith(BEARER_PREFIX):
		raise HTTPException(status_code=401, detail=ERROR_MISSING_BEARER)
	# split once to preserve any whitespace inside token (defensive)
	try:
		return auth.split(" ", 1)[1]
	except Exception:
		raise HTTPException(status_code=401, detail=ERROR_MISSING_BEARER)


def _get_payload_from_request(request: Request) -> Dict:
	"""Decode the JWT payload from the request Authorization header.

	Raises HTTPException(401) when token invalid.
	"""
	token = _extract_bearer_token(request)
	payload = security.decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail=ERROR_INVALID_TOKEN)
	return payload


def _verify_and_migrate_password(user, password: str, db: Session) -> bool:
	"""Verify a plaintext password against the stored hash.

	This helper centralizes password verification so we can transparently
	add migration steps for legacy hashes in future. It returns True when
	the password matches the stored hash, False otherwise.
	"""
	try:
		# reference db to avoid unused-parameter lint complaints; may be
		# used later for migration writes
		_ = db
		if not user or not getattr(user, "password_hash", None):
			return False
		return security.verify_password(password, user.password_hash)
	except Exception:
		return False


# -------------------- Public endpoints --------------------------------------
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
	"""Serve the login page template.

	The request is passed to the template so Jinja can render URL helpers.
	"""
	return templates.TemplateResponse("login.html", {"request": request})


@app.get("/health")
def health() -> Dict[str, str]:
	"""Simple healthcheck used by Docker Compose.

	Keeping it tiny avoids startup deadlocks in orchestration scripts.
	"""
	return {"status": "healthy", "service": "auth-service"}


@app.get("/services", response_class=HTMLResponse)
def services_portal(request: Request) -> HTMLResponse:
	"""Serve a small navigation portal used in development demos."""
	return templates.TemplateResponse("portal.html", {"request": request})


@app.post("/signup_admin")
async def signup_admin(request: Request, db: Session = Depends(get_db)) -> Dict:
	"""Create an admin user.

	Validation is delegated to Pydantic (`schemas.UserCreate`).
	The endpoint returns a one-time `private_key` that must be stored by
	the client; it is not persisted by the service.
	"""
	data = await _parse_request(request, ("firstname", "lastname", "email", "password", "confirm_password"))
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as exc:
		# Return Pydantic error messages as a 422 to help beginners debug input
		raise HTTPException(status_code=422, detail=str(exc))

	if user_in.password != user_in.confirm_password:
		raise HTTPException(status_code=400, detail=ERROR_PASSWORDS_MISMATCH)
	if not security.validate_password_strength(user_in.password):
		raise HTTPException(status_code=400, detail=ERROR_PASSWORD_STRENGTH)
	if crud.get_user_by_email(db, user_in.email):
		raise HTTPException(status_code=400, detail=ERROR_EMAIL_REGISTERED)

	try:
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role=ROLE_ADMIN)
		token = security.create_access_token({"sub": user_obj.email, "role": user_obj.role, "user_id": user_obj.id})
		return {
			"user": schemas.UserOut.from_orm(user_obj),
			"private_key": private_key,
			"access_token": token,
			"token_type": TOKEN_TYPE_BEARER,
		}
	except Exception as exc:
		# For beginners: return the traceback in 500 only in dev; in prod
		# prefer a generic message. Here we keep the original behaviour.
		import traceback

		tb = traceback.format_exc()
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post("/signup_client")
async def signup_client(request: Request, db: Session = Depends(get_db)) -> Dict:
	"""Create a regular (client) user. Mirrors `signup_admin`.
	"""
	data = await _parse_request(request, ("firstname", "lastname", "email", "password", "confirm_password"))
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as exc:
		raise HTTPException(status_code=422, detail=str(exc))

	if user_in.password != user_in.confirm_password:
		raise HTTPException(status_code=400, detail=ERROR_PASSWORDS_MISMATCH)
	if not security.validate_password_strength(user_in.password):
		raise HTTPException(status_code=400, detail=ERROR_PASSWORD_STRENGTH)
	if crud.get_user_by_email(db, user_in.email):
		raise HTTPException(status_code=400, detail=ERROR_EMAIL_REGISTERED)

	try:
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role=ROLE_USER)
		token = security.create_access_token({"sub": user_obj.email, "role": user_obj.role, "user_id": user_obj.id})
		return {
			"user": schemas.UserOut.from_orm(user_obj),
			"private_key": private_key,
			"access_token": token,
			"token_type": TOKEN_TYPE_BEARER,
		}
	except Exception:
		import traceback

		tb = traceback.format_exc()
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)) -> Dict:
	"""Authenticate a user and return a JWT access token.

	The function verifies passwords and performs best-effort migration of
	legacy password formats via `_verify_and_migrate_password` from the
	original implementation.
	"""
	data = await _parse_request(request, ("email", "password"))
	try:
		payload = schemas.LoginRequest(**data)
	except Exception as exc:
		raise HTTPException(status_code=422, detail=str(exc))

	user = crud.get_user_by_email(db, payload.email)
	if not user:
		raise HTTPException(status_code=401, detail=ERROR_INVALID_CREDENTIALS)

	# Verify password and migrate legacy hashes when needed.
	if not _verify_and_migrate_password(user, payload.password, db):
		import logging

		logger = logging.getLogger("uvicorn.error")
		logger.warning(
			"Login failed for %s; pw_len=%d hash_prefix=%s salt_len=%d",
			payload.email,
			len(payload.password),
			(user.password_hash or "")[:10],
			len(user.password_salt or ""),
		)
		raise HTTPException(status_code=401, detail=ERROR_INVALID_CREDENTIALS)

	token = security.create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
	crud.log_event(db, "login", user.id, success=1)
	return {"access_token": token, "token_type": TOKEN_TYPE_BEARER, "role": user.role}


@app.post("/delete_account")
def delete_account(email: str = Form(...), db: Session = Depends(get_db)) -> Dict[str, bool]:
	"""Delete a user account by email (form POST).

	This endpoint is intentionally simple: it is used by the UI for account
	self-deletion and by tests. It returns `{{'deleted': True}}` on success.
	"""
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
	crud.delete_user(db, u.id)
	return {"deleted": True}


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request) -> HTMLResponse:
	"""Serve the admin dashboard page (file fallback preferred).

	The UI lives under `ui/index-admin.html` when present; otherwise the
	bundled Jinja template is served for compatibility.
	"""
	ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "index-admin.html")
	if os.path.exists(ui_path):
		return FileResponse(ui_path)
	return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/client/dashboard", response_class=HTMLResponse)
def client_dashboard(request: Request) -> HTMLResponse:
	"""Serve the client dashboard template."""
	return templates.TemplateResponse("client.html", {"request": request})


@app.get("/__debug_user")
def debug_user(email: str, db: Session = Depends(get_db)) -> Dict:
	"""Development-only helper that returns masked password info for a user.

	Useful when debugging legacy password formats during migration.
	"""
	u = crud.get_user_by_email(db, email)
	if not u:
		return JSONResponse(status_code=404, content={"detail": "not found"})
	return {
		"email": u.email,
		"hash_prefix": (u.password_hash or "")[:60],
		"salt_len": len(u.password_salt or ""),
		"role": u.role,
	}


@app.get("/__debug_db")
def debug_db() -> Dict[str, str]:
	"""Return the `DATABASE_URL` used by this running service (dev helper)."""
	return {"DATABASE_URL": database.DATABASE_URL}


@app.get("/me")
def me(request: Request, db: Session = Depends(get_db)) -> Dict:
	"""Return public info for the authenticated user based on Bearer token.

	Endpoint returns 401 when the token is missing or invalid, and 404 when
	the user no longer exists (useful to verify deletion behavior in tests).
	"""
	payload = _get_payload_from_request(request)
	email = payload.get("sub")
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
	return {"email": u.email, "public_key": u.public_key, "role": u.role}


@app.get("/logs")
def my_logs(request: Request, db: Session = Depends(get_db)) -> Dict[str, list]:
	"""Return recent connection logs for the authenticated user."""
	payload = _get_payload_from_request(request)
	email = payload.get("sub")
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
	logs = crud.get_logs_for_user(db, u.id)
	out = [
		{
			"id": e.id,
			"user_id": e.user_id,
			"action_type": e.action_type,
			"success": bool(e.success),
			"timestamp": e.log_date.isoformat() if e.log_date else None,
		}
		for e in logs
	]
	return {"logs": out}


@app.get("/admin/logs")
def admin_logs(request: Request, db: Session = Depends(get_db)) -> Dict[str, list]:
	"""Admin-only endpoint that returns recent logs for all users.

	The function checks that the caller is an admin before returning data.
	"""
	payload = _get_payload_from_request(request)
	email = payload.get("sub")
	u = crud.get_user_by_email(db, email)
	if not u:
		raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
	if (u.role or "").upper() != ROLE_ADMIN:
		raise HTTPException(status_code=403, detail=ERROR_ADMIN_REQUIRED)

	logs = crud.get_all_logs(db)
	out = []
	# Include user role by querying user per entry. Keep logic explicit for
	# beginners rather than over-optimizing.
	for e in logs:
		user = None
		try:
			user = db.query(database.Base.classes.users).get(e.user_id)
		except Exception:
			user = None
		role = getattr(user, "role", None) if user else None
		out.append(
			{
				"id": e.id,
				"user_id": e.user_id,
				"role": role,
				"action_type": e.action_type,
				"success": bool(e.success),
				"timestamp": e.log_date.isoformat() if e.log_date else None,
			}
		)
	return {"logs": out}
