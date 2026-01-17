Auth module scaffolding

Endpoints (minimal):
- `GET /` : login page
- `POST /signup_admin` : create admin (returns private key PEM once)
- `POST /signup_client` : create client (returns private key PEM once)
- `POST /login` : login -> returns JWT access token and role
- `POST /delete_account` : delete by email (form)

Env vars (MySQL-only):
- `AUTH_DB_HOST`, `AUTH_DB_USER`, `AUTH_DB_PASSWORD`, `AUTH_DB_PORT`, `AUTH_DB_NAME` : MySQL connection settings used by the service (no SQLite fallback). The service builds the SQLAlchemy URL from these variables.
- `DATABASE_URL` : optional full SQLAlchemy URL (preferred for local overrides). Must point to a MySQL-compatible URI (e.g. `mysql+pymysql://user:password@host:3306/auth_db`).
- `JWT_SECRET` : secret for JWT (dev default provided)

Notes:
- Private key is returned once after account creation and not stored.
- Password hashing uses `passlib` bcrypt; a salt field is stored.
- This project no longer supports SQLite. Always use MySQL (via the Docker Compose `mysql` service or an external MySQL instance).
