# E-Commerce Backend

Production-ready E-commerce API built with **FastAPI** and **strict Clean Architecture** principles.

## Architecture

This project follows **Clean Architecture** with strict layer boundaries:

```
Domain ← Application ← Infrastructure & Presentation
```

- **Domain**: Pure Python entities, value objects, repository interfaces, and business policies
- **Application**: Use cases, DTOs, and port interfaces (no framework dependencies)
- **Infrastructure**: SQLAlchemy, JWT, cryptography, caching implementations
- **Presentation**: FastAPI routes, dependencies, middleware, DI container


## Tech Stack

- **Python 3.12**
- **FastAPI** + Uvicorn
- **SQLAlchemy 2.0** (async) + asyncpg
- **PostgreSQL**
- **Alembic** (migrations)
- **PyJWT** with RS256
- **argon2-cffi** (password hashing)
- **pytest** + httpx (testing)
- **ruff** (linting/formatting)
- **mypy** (type checking)

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- UV package manager (or pip/poetry)

## Setup

### 1. Clone and Install Dependencies

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. Setup PostgreSQL

#### Option A: Using Docker Compose

```bash
docker-compose up -d
```

#### Option B: Manual Setup

```bash
# Create database
createdb ecom_auth
createdb ecom_auth_test  # For testing
```

### 3. Generate JWT Keys

```bash
# Generate RSA key pair for JWT signing
mkdir -p keys
ssh-keygen -t rsa -b 2048 -m PEM -f keys/jwtRS256.key -N ""
ssh-keygen -e -m PEM -f keys/jwtRS256.key.pub > keys/jwtRS256.key.pub.pem
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

**Important**: Update the following in `.env`:

- `DATABASE_URL`: Your PostgreSQL connection string
- `REFRESH_TOKEN_HMAC_SECRET`: Generate a secure random secret (min 32 chars)
- `JWT_PRIVATE_KEY_PATH` / `JWT_PUBLIC_KEY_PATH`: Paths to generated keys
- `COOKIE_SECURE=true` in production (requires HTTPS)

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Seed Initial Data (Optional)

```bash
python scripts/seed_data.py
```

This creates:
- Admin role with `rbac:assign` permission
- User role (no permissions)
- Admin user: `admin@example.com` / `Admin123!`

## Running the Server

### Development

```bash
uvicorn app.presentation.api.main:app --reload
```

Server runs at `http://localhost:8000`

API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Production

```bash
uvicorn app.presentation.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_endpoints.py -v
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login | No |
| POST | `/auth/refresh` | Refresh access token | Refresh cookie |
| POST | `/auth/logout` | Logout current session | Refresh cookie |
| POST | `/auth/logout-all` | Logout all sessions | Bearer token |
| POST | `/auth/change-password` | Change password | Bearer token |
| GET | `/auth/me` | Get current user info | Bearer token |

### RBAC

| Method | Endpoint | Description | Auth Required | Permission |
|--------|----------|-------------|---------------|------------|
| POST | `/rbac/assign-role` | Assign role to user | Bearer token | `rbac:assign` |

## Security Features

### Authentication Flow

1. **Registration**: User registers with email + password
2. **Login**: Returns access token (JWT) + sets HttpOnly refresh token cookie
3. **Access**: Client sends `Authorization: Bearer <access_token>` for protected routes
4. **Refresh**: When access token expires, use `/auth/refresh` endpoint
5. **Logout**: Revokes refresh token

### Token Security

**Access Token (JWT)**:
- Short-lived (10 minutes default)
- Contains: `sub` (user_id), `roles`, `ver` (token_version), `jti`, `iss`, `aud`, `iat`, `exp`
- Header contains `kid` for key rotation support
- Verified on every request

**Refresh Token**:
- Long-lived (14 days default)
- Stored as HttpOnly cookie (not accessible to JavaScript)
- Raw token hashed with HMAC-SHA256 before storage
- Implements rotation: each refresh issues new token
- Supports reuse detection for theft prevention

### CSRF Protection

Since refresh token is HttpOnly cookie, CSRF protection is critical:

1. On login/refresh, server sets two cookies:
   - `refresh_token` (HttpOnly, Secure, SameSite=Lax)
   - `csrf_token` (NOT HttpOnly, Secure, SameSite=Lax)

2. Client must send `X-CSRF-Token` header matching `csrf_token` cookie

3. State-changing operations (`/auth/refresh`, `/auth/logout`) require CSRF validation

### Token Revocation

**Immediate Revocation** (access tokens):
- Increment user's `token_version`
- Token verification checks if `ver` claim matches current version
- Triggered by: password change, logout-all, reuse detection

**Refresh Token Revocation**:
- Mark token as `revoked_at`
- Delete entire token family on reuse detection

### Rate Limiting

In-memory rate limiting (per instance):
- `/auth/login`: 5 requests per 60 seconds per IP
- `/auth/refresh`: 10 requests per 60 seconds per IP

**Note**: For production multi-instance setup, use distributed rate limiter (Redis, etc.)

## 🗄️ Database Schema

```
users
  - id (UUID, PK)
  - email (VARCHAR, unique, indexed)
  - password_hash (TEXT)
  - is_active (BOOLEAN)
  - is_verified (BOOLEAN)
  - token_version (INTEGER)
  - created_at, updated_at (TIMESTAMP)

roles
  - id (UUID, PK)
  - name (VARCHAR, unique, indexed)

permissions
  - id (UUID, PK)
  - code (VARCHAR, unique, indexed)

user_roles
  - id (UUID, PK)
  - user_id (UUID, FK)
  - role_id (UUID, FK)
  - UNIQUE(user_id, role_id)

role_permissions
  - id (UUID, PK)
  - role_id (UUID, FK)
  - permission_id (UUID, FK)
  - UNIQUE(role_id, permission_id)

refresh_tokens
  - id (UUID, PK)
  - user_id (UUID, FK)
  - token_hash (VARCHAR, unique, indexed)
  - family_id (UUID, indexed)
  - issued_at, expires_at (TIMESTAMP, expires_at indexed)
  - revoked_at (TIMESTAMP, nullable)
  - replaced_by_token_id (UUID, FK, nullable)
  - ip, user_agent (optional metadata)
```

## Development

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy app/

# Run all checks
ruff check . && ruff format . && mypy app/
```

### Creating New Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Project Structure

```
app/
  domain/           # Pure business logic (no external deps)
  application/      # Use cases, DTOs, ports
  infrastructure/   # SQLAlchemy, JWT, crypto implementations
  presentation/     # FastAPI routes, deps, middleware
config/             # Settings
alembic/            # Database migrations
tests/              # Unit & integration tests
```

## Use Case Examples

### Register and Login

```python
import httpx

# Register
response = httpx.post(
    "http://localhost:8000/auth/register",
    json={"email": "user@example.com", "password": "SecurePass123"}
)
user_id = response.json()["user_id"]

# Login
response = httpx.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "SecurePass123"}
)
access_token = response.json()["access_token"]
# refresh_token and csrf_token are in cookies
```

### Access Protected Endpoint

```python
response = httpx.get(
    "http://localhost:8000/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(response.json())
```

### Refresh Token

```python
# Client must send both cookies and CSRF header
response = httpx.post(
    "http://localhost:8000/auth/refresh",
    cookies={"refresh_token": refresh_token, "csrf_token": csrf_token},
    headers={"X-CSRF-Token": csrf_token}
)
new_access_token = response.json()["access_token"]
```

## Important Notes

### Production Checklist

- [ ] Set `COOKIE_SECURE=true` (requires HTTPS)
- [ ] Use strong JWT keys (4096-bit RSA or better)
- [ ] Rotate `REFRESH_TOKEN_HMAC_SECRET` periodically
- [ ] Use distributed cache (Redis) instead of in-memory
- [ ] Use distributed rate limiter
- [ ] Configure proper CORS origins
- [ ] Enable audit log forwarding to centralized system
- [ ] Set up JWT key rotation strategy
- [ ] Use secrets manager for sensitive config (not .env files)
- [ ] Configure database connection pooling
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

### Limitations

1. **In-memory cache**: Not suitable for multi-instance deployment
2. **In-memory rate limiter**: Only protects single instance
3. **No email verification**: Users created with `is_verified=False` (implement separately)
4. **Basic audit logging**: Logs to stdout (integrate with proper system)

## Further Reading

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation)

