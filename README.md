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

### Docker Compose (Recommended)

The easiest way to run the full stack (API + PostgreSQL) is with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

This starts:

- **PostgreSQL** on port `5432`
- **API** on port `8000` with hot-reload enabled

> **Note**: Ensure your `.env` file is configured before starting. The `DATABASE_URL` is automatically overridden to point to the containerized PostgreSQL instance.

After the containers are up, run migrations inside the container:

```bash
docker-compose exec api alembic upgrade head
```

Optionally seed initial data:

```bash
docker-compose exec api python scripts/seed_data.py
```

### Development (Local)

```bash
uvicorn app.presentation.api.main:app --reload
```

Server runs at `http://localhost:8000`

API docs available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_endpoints.py -v
```

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
