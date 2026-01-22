from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from .database import SessionLocal, init_db
from . import crud, security
import json

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


async def _parse_request_fields(request: Request, *fields):
    """Support both application/json and form-data for incoming requests."""
    content_type = (request.headers.get('content-type') or '').lower()
    data = {}
    # Try robust JSON parsing first when content-type suggests JSON
    if 'application/json' in content_type:
        try:
            # Prefer raw body parsing to avoid some edge cases
            raw = await request.body()
            if raw:
                try:
                    data = json.loads(raw.decode('utf-8'))
                except Exception:
                    # tolerant fallback for curl/fish odd formatting like {key:val,key2:val2}
                    try:
                        txt = raw.decode('utf-8', errors='replace').strip()
                        if txt.startswith('{') and ':' in txt:
                            obj = {}
                            for part in txt.strip('{}').split(','):
                                if ':' in part:
                                    k, v = part.split(':', 1)
                                    obj[k.strip().strip('"\'')] = v.strip().strip('"\'')
                            data = obj
                        else:
                            data = {}
                    except Exception:
                        data = {}
            else:
                data = {}
        except Exception:
            try:
                data = await request.json()
            except Exception:
                data = {}
    else:
        form = await request.form()
        data = dict(form)
    return [data.get(f) for f in fields]


@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'auth-service'}


@app.post('/signup_admin')
async def signup_admin(request: Request, db: Session = Depends(get_db)):
    firstname, lastname, email, password = await _parse_request_fields(request, 'firstname', 'lastname', 'email', 'password')
    if not (firstname and lastname and email and password):
        raise HTTPException(status_code=400, detail='Missing fields')
    existing = crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user, private_key = crud.create_user_with_keys(db, firstname, lastname, email, password, role='ADMIN')
    token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
    return {'user': {'id': user.id, 'email': user.email, 'role': user.role, 'public_key': user.public_key}, 'private_key': private_key, 'access_token': token, 'token_type': 'bearer'}


@app.post('/signup_client')
async def signup_client(request: Request, db: Session = Depends(get_db)):
    firstname, lastname, email, password = await _parse_request_fields(request, 'firstname', 'lastname', 'email', 'password')
    if not (firstname and lastname and email and password):
        raise HTTPException(status_code=400, detail='Missing fields')
    existing = crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user, private_key = crud.create_user_with_keys(db, firstname, lastname, email, password, role='USER')
    token = security.create_access_token({'sub': user.email, 'role': user.role, 'user_id': user.id})
    return {'user': {'id': user.id, 'email': user.email, 'role': user.role, 'public_key': user.public_key}, 'private_key': private_key, 'access_token': token, 'token_type': 'bearer'}


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    email, password = await _parse_request_fields(request, 'email', 'password')
    if not (email and password):
        raise HTTPException(status_code=400, detail='Missing credentials')
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
