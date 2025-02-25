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