Auth module scaffolding

Endpoints (minimal):
- `GET /` : login page
- `POST /signup_admin` : create admin (returns private key PEM once)
- `POST /signup_client` : create client (returns private key PEM once)
- `POST /login` : login -> returns JWT access token and role
- `POST /delete_account` : delete by email (form)

Env vars:
- `DATABASE_URL` : SQLAlchemy URL (default sqlite ./dev.db)
- `JWT_SECRET` : secret for JWT (dev default provided)

Notes:
- Private key is returned once after account creation and not stored.
- Password hashing uses `passlib` bcrypt; a salt field is stored.
