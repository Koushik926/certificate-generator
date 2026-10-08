# Bulk Certificate Generator

Production-ready backend API for bulk certificate generation with background processing, progress tracking, and professional PDF output.

## Tech Stack

- **FastAPI** - Async web framework with auto-generated OpenAPI docs
- **SQLAlchemy 2.0** + **aiosqlite** - Async ORM (SQLite default, PostgreSQL-ready via connection string)
- **ReportLab** - Professional PDF certificate generation
- **Pydantic v2** - Request/response validation
- **pytest + httpx** - Test suite with async client

## Architecture Highlights

- **Background processing** - Jobs run in a thread pool; API returns immediately with job ID
- **Per-recipient error isolation** - One failure doesn't block others; detailed per-item status
- **Idempotent submissions** - Duplicate requests handled via idempotency key
- **Pagination** - List endpoints support pagination
- **Health checks** - `/health` endpoint for container orchestration
- **No external broker required** - Default uses `ThreadPoolExecutor`; Celery/Redis path documented in code

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the API
uvicorn app.main:app --reload

# 3. Open API docs
open http://localhost:8000/docs

# 4. Run tests
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
│   ├── api/v1/__init__.py       # API router
│   ├── config/settings.py       # Pydantic settings (env-based)
│   ├── core/background.py       # Background task dispatcher (ThreadPoolExecutor)
│   ├── db/session.py            # Async SQLAlchemy engine + session factory
│   ├── endpoints/               # REST endpoint handlers
│   ├── models/                  # SQLAlchemy ORM models (Job, Recipient)
│   ├── pdf/template.py          # ReportLab certificate renderer
│   ├── schemas/                 # Pydantic request/response models
│   ├── services/                # Business logic (job_service, pdf_service)
│   └── utils/validation.py      # Input validation utilities
├── tests/                       # Test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Design Decisions

1. **ThreadPoolExecutor for background processing** - Decouples API from CPU-intensive PDF generation. The API returns immediately with a job_id; generation runs in background threads. No Redis/Celery required for the default path (optional Celery path documented in `app/core/background.py`).

2. **Per-recipient error isolation** - Each recipient is processed independently. A failure on one recipient records an error and continues with the next. The job status aggregates per-recipient results.

3. **ZIP download** - Single archive of all generated certificates reduces client round trips.

4. **UUID job IDs** - Prevents enumeration, supports distributed systems.

5. **Async FastAPI** - Handles concurrent requests efficiently with async SQLAlchemy sessions.

6. **Separable business logic** - Service functions accept `AsyncSession` explicitly, making them trivially testable by overriding the `get_db` dependency.

## Testing

```bash
pytest tests/ -v
```

Covers:
- Creating a generation job
- Input validation
- Certificate generation (PDF)
- Job status/progress
- Handling individual certificate failure
- Retrieving generated certificates (ZIP download)

## Optional Features Added

- Template style selection (modern/classic)
- ZIP download endpoint
- Health check endpoint
- Request idempotency via client-provided idempotency key
- Pagination on job listing
- CORS middleware configured