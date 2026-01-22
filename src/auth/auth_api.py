from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from .database import SessionLocal, init_db
from . import crud, security

app = FastAPI(title="Auth Service")

# serve UI folder mounted at /ui
if os.path.isdir('ui'):
    app.mount('/ui', StaticFiles(directory='ui', html=True), name='ui')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8002", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=['*']
)

@app.on_event('startup')
def startup():
    init_db()
    print('Auth service started')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'auth-service'}


@app.post('/signup_admin')
async def signup_admin(request: Request, firstname: str = Form(...), lastname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user, private_key = crud.create_user_with_keys(db, firstname, lastname, email, password, role='ADMIN')
    token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
    return {'user': {'id': user.id, 'email': user.email, 'role': user.role, 'public_key': user.public_key}, 'private_key': private_key, 'access_token': token, 'token_type': 'bearer'}


@app.post('/signup_client')
async def signup_client(request: Request, firstname: str = Form(...), lastname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user, private_key = crud.create_user_with_keys(db, firstname, lastname, email, password, role='USER')
    token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
    return {'user': {'id': user.id, 'email': user.email, 'role': user.role, 'public_key': user.public_key}, 'private_key': private_key, 'access_token': token, 'token_type': 'bearer'}


@app.post('/login')
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user or not security.verify_password(password, user.password_hash):
        if user:
            crud.log_event(db, 'login', user_id=user.id, success=False)
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
    crud.log_event(db, 'login', user_id=user.id, success=True)
    return {'access_token': token, 'token_type': 'bearer', 'role': user.role}


@app.get('/me')
async def me(token: str = Depends(lambda: None), request: Request = None, db: Session = Depends(get_db)):
    # Extract bearer token from Authorization header
    auth = request.headers.get('authorization', '') if request else ''
    if not auth.lower().startswith('bearer'):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = auth.split(' ', 1)[1]
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = crud.get_user_by_email(db, payload.get('sub'))
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return {'email': user.email, 'public_key': user.public_key, 'role': user.role}


@app.get('/logs')
async def my_logs(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get('authorization', '')
    if not auth.lower().startswith('bearer'):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = auth.split(' ', 1)[1]
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = crud.get_user_by_email(db, payload.get('sub'))
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    logs = crud.get_logs_for_user(db, user.id)
    return {'logs': [ {'id': l.id, 'user_id': l.user_id, 'action_type': l.action_type, 'success': l.success, 'timestamp': l.log_date.isoformat()} for l in logs ]}


@app.get('/admin/logs')
async def admin_logs(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get('authorization', '')
    if not auth.lower().startswith('bearer'):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = auth.split(' ', 1)[1]
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = crud.get_user_by_email(db, payload.get('sub'))
    if not user or (user.role or '').upper() != 'ADMIN':
        raise HTTPException(status_code=403, detail='Admin access required')
    logs = crud.get_all_logs(db)
    return {'logs': [ {'id': l.id, 'user_id': l.user_id, 'action_type': l.action_type, 'success': l.success, 'timestamp': l.log_date.isoformat()} for l in logs ]}
