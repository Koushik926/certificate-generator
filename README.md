# Bulk Certificate Generator

Production-ready backend API for bulk certificate generation with background processing, progress tracking, and professional PDF output.

## Tech Stack

- **FastAPI** - Async web framework with auto-generated OpenAPI docs
- **SQLAlchemy 2.0** + **Alembic** - Async ORM with migrations
- **Redis** + **Celery** - Background task queue with result backend
- **ReportLab** - Professional PDF certificate generation
- **Pillow** - Image compositing for certificate templates
- **Pydantic v2** - Request/response validation
- **pytest + httpx** - Test suite with async client

## Architecture Highlights

- **Background processing** - Jobs run asynchronously; API returns immediately with job ID
- **Per-recipient error isolation** - One failure doesn't block others; detailed per-item status
- **Template engine** - Jinja2-based certificate template with dynamic fields
- **Idempotent submissions** - Duplicate requests handled gracefully
- **Pagination + filtering** - List endpoints support pagination
- **Health checks** - `/health` endpoint for container orchestration

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis (required for Celery)
redis-server

# 3. Run migrations
alembic upgrade head

# 4. Start the API
uvicorn app.main:app --reload

# 5. Start Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# 6. Run tests
pytest tests/ -v
```

## API Usage

### Create a certificate generation job

```bash
curl -X POST http://localhost:8000/api/v1/certificates/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Annual Conference 2025",
    "issue_date": "2025-06-15",
    "recipients": [
      {"name": "Alice Johnson", "email": "alice@example.com", "certificate_id": "CERT-001"},
      {"name": "Bob Smith", "email": "bob@example.com", "certificate_id": "CERT-002"}
    ],
    "template_style": "modern"
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "total_recipients": 2,
  "created_at": "2025-06-15T10:30:00Z"
}
```

### Check job status

```bash
curl http://localhost:8000/api/v1/certificates/jobs/{job_id}/status
```

### Download generated certificates (ZIP)

```bash
curl -O http://localhost:8000/api/v1/certificates/jobs/{job_id}/download
```

### List all jobs (paginated)

```bash
curl "http://localhost:8000/api/v1/certificates/jobs?page=1&size=20"
```

## Project Structure

```
certificate-generator/
├── app/
│   ├── api/v1/endpoints/     # Route handlers
│   ├── core/                 # Config, security, middleware
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic
│   ├── template/             # Certificate templates (HTML/CSS)
│   ├── tasks/                # Celery background tasks
│   └── utils/                # Helpers (PDF gen, validation)
├── migrations/               # Alembic migrations
├── tests/                    # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Design Decisions

1. **Celery + Redis** for background processing - decouples API from CPU-intensive PDF generation
2. **Per-recipient error isolation** - individual failures recorded, job continues
3. **ZIP download** - single archive of all certificates reduces client round trips
4. **UUID job IDs** - prevents enumeration, supports distributed systems
5. **Async FastAPI** - handles concurrent requests efficiently

## Optional Features Added

- Template style selection (modern/classic)
- ZIP download endpoint
- Health check endpoint
- Request idempotency via client-provided idempotency key
- Rate limiting
- Structured logging with correlation IDs
