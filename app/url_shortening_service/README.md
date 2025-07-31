# URL Shortening Service

A FastAPI-based microservice for shortening URLs with Redis caching and PostgreSQL storage.

## Quick Start

### 1. Setup
```bash
cd url_shortening_service
cp .env.example .env
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Verify
```bash
curl http://localhost:8010/health
```

## API Endpoints

### Health Check
```
GET /health
```
Check service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "URL Shortening Service", 
  "version": "1.0.0",
  "environment": "development"
}
```

### Shorten URL
```
POST /api/v1/urls/shorten
```
Create a shortened URL.

**Request:**
```json
{
  "url": "https://example.com/very/long/url",
  "custom_code": "my-link",        // optional
  "expires_in_hours": 24           // optional, default 168 (7 days)
}
```

**Response:**
```json
{
  "short_code": "abc123",
  "short_url": "http://localhost:8010/abc123",
  "original_url": "https://example.com/very/long/url",
  "expires_at": "2025-07-05T10:00:00",
  "created_at": "2025-07-04T10:00:00"
}
```

### Redirect
```
GET /{short_code}
```
Redirects to the original URL and tracks analytics.

**Example:**
```bash
curl -I http://localhost:8010/abc123
# Returns: 302 redirect to original URL
```

### Get Statistics
```
GET /api/v1/urls/stats/{short_code}
```
Get URL statistics and click count.

**Response:**
```json
{
  "short_code": "abc123",
  "original_url": "https://example.com/very/long/url",
  "click_count": 42,
  "created_at": "2025-07-04T10:00:00",
  "is_active": true,
  "expires_at": "2025-07-05T10:00:00"
}
```

### Deactivate URL
```
DELETE /api/v1/urls/{short_code}
```
Deactivate a shortened URL.

**Response:**
```json
{
  "message": "URL deactivated successfully"
}
```

## Example Usage

```bash
# 1. Create short URL
curl -X POST "http://localhost:8010/api/v1/urls/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com", "expires_in_hours": 24}'

# 2. Use the short URL (redirects to original)
curl -I "http://localhost:8010/abc123"

# 3. Check statistics
curl "http://localhost:8010/api/v1/urls/stats/abc123"

# 4. Deactivate if needed
curl -X DELETE "http://localhost:8010/api/v1/urls/abc123"
```

## Service URLs

- **API**: http://localhost:8010
- **API Documentation**: http://localhost:8010/docs
- **Redis Commander**: http://localhost:8091 (admin/admin123)
- **pgAdmin**: http://localhost:5060 (admin@admin.com/admin123)


### Stop Services
```bash
docker-compose down
```

### Database Access
```bash
# PostgreSQL
docker-compose exec url-shortener-db psql -U postgres -d url_shortener

# Redis
docker-compose exec url-shortener-redis redis-cli
```

## Configuration

Edit `.env` file for configuration:

```bash
# Application
BASE_URL=http://localhost:8010
DEBUG=true

# Database (internal Docker network)
DATABASE_URL=postgresql://postgres:password@url-shortener-db:5432/url_shortener

# Redis (internal Docker network)
REDIS_URL=redis://url-shortener-redis:6379

# URL Shortener
SHORT_CODE_LENGTH=6
DEFAULT_EXPIRATION_HOURS=168
```

## Error Responses

All errors return JSON with detail message:

```json
{
  "detail": "Error description"
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid URL, duplicate custom code)
- `404` - Not Found (short code doesn't exist)
- `410` - Gone (URL expired)
- `422` - Validation Error (invalid request format)