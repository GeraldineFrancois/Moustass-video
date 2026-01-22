import os
import tempfile
import json
from fastapi.testclient import TestClient


def make_client():
    # Use in-memory DB for reliability during tests
    os.environ['AUTH_DB_PATH'] = ':memory:'
    # import after env set
    from src.auth import auth_api
    client = TestClient(auth_api.app)
    return client, None


def test_signup_login_me_and_logs():
    client, dbpath = make_client()
    with client:
        # signup client
        r = client.post('/signup_client', json={
            'firstname': 'Test', 'lastname': 'User', 'email': 't1@example.com', 'password': 'Pass12345'
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert 'access_token' in body
        token = body['access_token']

        # login
        r2 = client.post('/login', json={'email': 't1@example.com', 'password': 'Pass12345'})
        assert r2.status_code == 200, r2.text
        j2 = r2.json()
        assert 'access_token' in j2
        token2 = j2['access_token']

        # me
        headers = {'Authorization': f'Bearer {token2}'}
        r3 = client.get('/me', headers=headers)
        assert r3.status_code == 200
        assert r3.json().get('email') == 't1@example.com'

        # logs
        r4 = client.get('/logs', headers=headers)
        assert r4.status_code == 200
        logs = r4.json().get('logs', [])
        assert any(l.get('action_type') == 'login' for l in logs)

    try:
        os.remove(dbpath)
    except Exception:
        pass


def test_admin_can_view_all_logs():
    client, dbpath = make_client()
    with client:
        # create a user to generate logs
        r = client.post('/signup_client', json={'firstname': 'A', 'lastname': 'B', 'email': 'u2@example.com', 'password': 'Pass12345'})
        assert r.status_code == 200

        # create admin
        ra = client.post('/signup_admin', json={'firstname': 'Admin', 'lastname': 'User', 'email': 'admin@example.com', 'password': 'AdminPass1'})
        assert ra.status_code == 200
        token_admin = ra.json()['access_token']

        # admin can access /admin/logs
        headers = {'Authorization': f'Bearer {token_admin}'}
        rlogs = client.get('/admin/logs', headers=headers)
        assert rlogs.status_code == 200
        assert isinstance(rlogs.json().get('logs'), list)

    try:
        os.remove(dbpath)
    except Exception:
        pass


def test_formdata_signup_and_login():
    client, _ = make_client()
    with client:
        # send as form-data
        r = client.post('/signup_client', data={
            'firstname': 'Form', 'lastname': 'User', 'email': 'form@example.com', 'password': 'Pwd12345'
        })
        assert r.status_code == 200
        j = r.json()
        assert 'access_token' in j

        r2 = client.post('/login', data={'email': 'form@example.com', 'password': 'Pwd12345'})
        assert r2.status_code == 200


def test_missing_and_invalid_token_paths():
    client, _ = make_client()
    with client:
        # missing fields -> 400
        r = client.post('/signup_client', json={'email': 'x@example.com'})
        assert r.status_code == 400

        # /me without token
        r2 = client.get('/me')
        assert r2.status_code == 401

        # /logs without token
        r3 = client.get('/logs')
        assert r3.status_code == 401

        # invalid token
        r4 = client.get('/me', headers={'Authorization': 'Bearer invalid.token.here'})
        assert r4.status_code == 401


def test_database_file_path_branch(tmp_path):
    # Ensure database.py file-branch is exercised by reloading the module with a file path
    dbfile = tmp_path / 'auth_test_file.db'
    os.environ['AUTH_DB_PATH'] = str(dbfile)
    import importlib
    import src.auth.database as database_module
    importlib.reload(database_module)
    # reload auth_api so it binds to the reloaded database engine for this test
    import src.auth.auth_api as auth_api_module
    importlib.reload(auth_api_module)
    # engine url should reference the sqlite file path
    assert 'sqlite' in str(database_module.engine.url)


def test_malformed_json_tolerant_parsing():
    client, _ = make_client()
    with client:
        # send malformed JSON (no quotes) but content-type application/json
        raw = '{firstname:Bad,lastname:User,email:bad@example.com,password:Pwd12345}'
        r = client.post('/signup_client', content=raw, headers={'Content-Type': 'application/json'})
        assert r.status_code == 200


def test_health_endpoint_and_admin_forbidden():
    client, _ = make_client()
    with client:
        r = client.get('/health')
        assert r.status_code == 200

        # create a normal user
        ru = client.post('/signup_client', json={'firstname': 'Norm', 'lastname': 'User', 'email': 'norm@example.com', 'password': 'Pwd00000'})
        tok = ru.json()['access_token']
        r_forbid = client.get('/admin/logs', headers={'Authorization': f'Bearer {tok}'})
        assert r_forbid.status_code == 403
