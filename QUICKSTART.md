# Quick Start Guide

Get the auth system running in 5 minutes.

## Prerequisites

- Python 3.12+
- PostgreSQL (or Docker)
- UV package manager

## Setup Steps

### 1. Install UV (if needed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Setup Project

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 3. Start PostgreSQL

```bash
# Using Docker (recommended for quick start)
docker-compose up -d

# Wait for Postgres to be ready
docker-compose ps
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Generate JWT keys
python scripts/generate_keys.py

# The script will output what to add to .env - keys are generated in keys/ folder
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Seed Initial Data (Optional)

```bash
python scripts/seed_data.py
```

This creates:
- **Admin user**: `admin@example.com` / `Admin123!`
- Roles: admin, user
- Permissions: rbac:assign, rbac:view, users:read, users:write

### 7. Start Server

```bash
uvicorn app.presentation.api.main:app --reload
```

Server runs at: http://localhost:8000

API Docs: http://localhost:8000/docs

## First API Call

### Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }' \
  -c cookies.txt
```

Save the `access_token` from response.

### Get Current User

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Running Tests

```bash
# Create test database (if using Docker)
docker exec -it ecom_auth_postgres psql -U postgres -c "CREATE DATABASE ecom_auth_test;"

# Run tests
pytest

# With coverage
pytest --cov=app
```

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Review security considerations for production
3. Explore API docs at `/docs`
4. Customize domain entities for your use case

## Troubleshooting

### Database connection fails

- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in `.env`

### JWT key errors

- Ensure keys exist in `keys/` folder
- Run `python scripts/generate_keys.py`
- Verify paths in `.env`

### Import errors

- Ensure virtual environment is activated
- Reinstall dependencies: `uv pip install -e ".[dev]"`

### Tests fail

- Ensure test database exists
- Check test database connection in `tests/conftest.py`

## Clean Up

```bash
# Stop containers
docker-compose down

# Remove volumes (deletes data)
docker-compose down -v
```

---

**You're ready to build! 🚀**
