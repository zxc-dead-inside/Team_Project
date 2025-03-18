# Running the Service

Start the service with Docker Compose:

```bash
docker-compose up --build
```

- The service will be available at http://localhost:8100
- API documentation: http://localhost:8100/api/docs
- Health check: http://localhost:8100/api/health

Development
For development, we can use the following commands:

```bash
# Start the services in development mode
docker-compose up --build

# Apply migrations
docker-compose exec api alembic upgrade head

# Generate a new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Stop the services
docker-compose down
```

# API Endpoints

- `GET /`: Root endpoint with welcome message
- `GET /api/health`: Health check endpoint
### To do
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login with username/email and password
- `POST /api/auth/refresh`: Refresh access token
- `GET /api/users/me`: Get current user profile

# Setup Commands

Follow these commands in order to set up and test authentication service.

## 1. Initialize Migrations Structure

First, initialize the Alembic migrations structure:

```bash
docker-compose exec api python scripts/init_migrations.py
```

This will create the necessary Alembic files if they don't exist.

## 2. Create Initial Migration

Generate the initial migration based on the models:

```bash
docker-compose exec api python scripts/create_migration.py "Initial migration"
```

## 3. Apply Migrations

Apply the migrations to create the database tables:

```bash
docker-compose exec api python scripts/apply_migrations.py
```

## 4. Seed Initial Data

Populate the database with initial roles, permissions, and restrictions:

```bash
docker-compose exec api python scripts/seed_data.py
```

## 5. Create seed permissions

Run the seed permissions script:

```bash
docker-compose exec api python scripts/seed_permissions.py
```

## 6. Create Superuser

Create an admin superuser:

```bash
docker-compose exec api python scripts/create_superuser.py
```

## 7. Create anonymous_role

Create an admin superuser:

```bash
docker-compose exec api python scripts/create_anonymous_userrole.py
```

## Verifying Setup

To verify that everything is working, use these commands:

### Check Database Tables

```bash
docker-compose exec db psql -U postgres -d auth_db -c "\dt"
```

### Check Users Table

```bash
docker-compose exec db psql -U postgres -d auth_db -c "SELECT * FROM users;"
```

### Check Roles

```bash
docker-compose exec db psql -U postgres -d auth_db -c "SELECT * FROM roles;"
```

### Check User-Role Associations

```bash
docker-compose exec db psql -U postgres -d auth_db -c "SELECT u.username, r.name FROM users u JOIN user_role ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id;"
```

### Create Database Migration (optional)

1. Create a migration script for the new AuditLog table
```bash
docker compose exec api alembic revision --autogenerate -m "add_audit_log_table"
```

2. Upgrade model
```bash
docker compose exec api alembic upgrade head
```