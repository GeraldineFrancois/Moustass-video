""" FastAPI endpoints for authentication and minimal admin/client UI. """
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from . import schemas, crud, security, auth_service
from .database import init_db, get_db
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


@app.post('/signup_admin')
async def signup_admin(request: Request, db: Session = Depends(get_db)):
	# accept either JSON body or HTML form posts
	if request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
		form = await request.form()
		data = {k: form.get(k) for k in ('firstname', 'lastname', 'email', 'password', 'confirm_password')}
	else:
		data = await request.json()
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as e:
		raise HTTPException(status_code=422, detail=str(e))
	try:
		if user_in.password != user_in.confirm_password:
			raise HTTPException(status_code=400, detail='Passwords do not match')
		if not security.validate_password_strength(user_in.password):
			raise HTTPException(status_code=400, detail='Password does not meet strength requirements')
		existing = crud.get_user_by_email(db, user_in.email)
		if existing:
			raise HTTPException(status_code=400, detail='Email already registered')
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role='ADMIN')
		return {'user': schemas.UserOut.from_orm(user_obj), 'private_key': private_key}
	except Exception:
		import traceback
		tb = traceback.format_exc()
		from fastapi.responses import JSONResponse
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post('/signup_client')
async def signup_client(request: Request, db: Session = Depends(get_db)):
	# accept either JSON body or HTML form posts
	if request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
		form = await request.form()
		data = {k: form.get(k) for k in ('firstname', 'lastname', 'email', 'password', 'confirm_password')}
	else:
		data = await request.json()
	try:
		user_in = schemas.UserCreate(**data)
	except Exception as e:
		raise HTTPException(status_code=422, detail=str(e))
	try:
		if user_in.password != user_in.confirm_password:
			raise HTTPException(status_code=400, detail='Passwords do not match')
		if not security.validate_password_strength(user_in.password):
			raise HTTPException(status_code=400, detail='Password does not meet strength requirements')
		existing = crud.get_user_by_email(db, user_in.email)
		if existing:
			raise HTTPException(status_code=400, detail='Email already registered')
		user_obj, private_key = auth_service.create_user_with_keys(db, user_in, role='USER')
		return {'user': schemas.UserOut.from_orm(user_obj), 'private_key': private_key}
	except Exception:
		import traceback
		tb = traceback.format_exc()
		from fastapi.responses import JSONResponse
		return JSONResponse(status_code=500, content={"detail": tb})


@app.post('/login')
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
	user = crud.get_user_by_email(db, payload.email)
	if not user:
		raise HTTPException(status_code=401, detail='Invalid credentials')
	# Verify using the stored bcrypt hash. Do not append our app-level salt to the
	# password before verification because bcrypt/passlib manage salting internally.
	if not security.verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=401, detail='Invalid credentials')
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
