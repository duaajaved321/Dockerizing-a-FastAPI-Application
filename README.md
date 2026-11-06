# Dockerizing a FastAPI Application

A containerized REST API for collecting, validating, storing, retrieving, and summarizing fictional patient vital signs. The API is built with **FastAPI**, **Pydantic**, and **SQLite**, and packaged with **Docker**.

This project focuses on taking a local Python API and running it consistently inside a container, while keeping SQLite data outside the container's writable layer through a Docker named volume.

## Features

- Health-check endpoint.
- Submit patient vitals with nested blood-pressure fields.
- Strict request validation with Pydantic.
- Store records in SQLite using parameterized SQL.
- Retrieve patient history, with an optional record limit.
- Calculate average blood pressure, average glucose, and total record count.
- Custom validation-error responses.
- Docker image built from the official Python slim image.
- Non-root container user.
- Docker health check.
- Persistent SQLite storage through a named volume.
- Automated API tests using pytest and FastAPI TestClient.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Application runtime |
| FastAPI | REST API framework |
| Pydantic | Request validation |
| SQLite | Local data store |
| Uvicorn | ASGI server |
| Docker | Container image and runtime |
| Docker Compose | Local orchestration |
| pytest / HTTPX | Automated API tests |

## Project Structure

```text
Dockerizing-a-FastAPI-Application/
├── main.py
├── database.py
├── test_api.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── requirements-dev.txt
├── .dockerignore
├── .gitignore
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Returns API status and UTC timestamp |
| POST | `/vitals` | Validates and stores a vital-sign record |
| GET | `/patients/{patient_id}/vitals` | Returns patient records |
| GET | `/patients/{patient_id}/summary` | Returns averages and record count |

### Example request

`POST /vitals`

```json
{
  "patient_id": "P001",
  "age": 25,
  "blood_pressure": {"systolic": 120, "diastolic": 80},
  "glucose_level": 95
}
```

## Run Locally (Without Docker)

### 1. Clone the repository

```bash
git clone https://github.com/duaajaved321/Dockerizing-a-FastAPI-Application.git
cd Dockerizing-a-FastAPI-Application
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

For the API:

```bash
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

### 4. Start the API

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to use Swagger UI.

## Run with Docker

### Prerequisites

- Docker Engine or Docker Desktop.
- Docker Compose.

### Option 1: Docker Compose (recommended)

Build and start the service:

```bash
docker compose up --build -d
```

Check the service:

```bash
docker compose ps
docker compose logs -f api
```

The API is available at:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

Stop the service:

```bash
docker compose down
```

The named volume is retained after `docker compose down`, so the SQLite database remains available when the service starts again.

**Warning:** To remove the database volume and its records too:

```bash
docker compose down -v
```

### Option 2: Docker commands

Build the image:

```bash
docker build -t patient-vitals-api .
```

Create a named volume:

```bash
docker volume create patient-vitals-data
```

Run the container:

```bash
docker run -d --name patient-vitals-api -p 8000:8000 -e DB_PATH=/data/patient_vitals.db -v patient-vitals-data:/data patient-vitals-api
```

View logs:

```bash
docker logs -f patient-vitals-api
```

Stop and remove the container:

```bash
docker stop patient-vitals-api
docker rm patient-vitals-api
```

The named volume remains until explicitly removed.

## Data Persistence

The container stores SQLite at `/data/patient_vitals.db`. Docker Compose mounts the named volume `patient_vitals_data` at `/data`.

- Rebuilding the image does not package the local database.
- Removing and recreating the container does not remove the named volume.
- Removing the named volume deletes the stored records.

For local development, the database defaults to a file beside `database.py`. Set `DB_PATH` to use another location.

## Validation Rules

| Field | Rule |
|---|---|
| `patient_id` | Non-empty string |
| `age` | Integer from 0 to 120 |
| `blood_pressure.systolic` | Integer from 50 to 300 |
| `blood_pressure.diastolic` | Integer from 30 to 200 |
| `glucose_level` | Positive integer or float |

Invalid request bodies return HTTP `400` with a `detail` array. This project deliberately uses `400` through a custom exception handler.

## Automated Tests

Install development dependencies and run:

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use a temporary SQLite database and cover the health endpoint, saving records, patient history, limits, summaries, invalid field values, and empty summaries.

## Docker Design Choices

- **Small base image:** `python:3.11-slim`.
- **Layer caching:** install dependencies before copying source files.
- **Non-root execution:** run the API as an unprivileged user.
- **Persistent volume:** keep SQLite data under `/data`.
- **Health check:** Docker checks the `/health` endpoint.
- **Build context hygiene:** `.dockerignore` excludes Git metadata, local databases, virtual environments, caches, and archives.

## Limitations and Responsible Use

- SQLite is suitable for this learning project, not a high-availability production database.
- No authentication, authorization, encryption, audit logging, or backups are implemented.
- Use fictional patient data only.
- Do not deploy with identifiable patient health information without appropriate security, privacy, and compliance safeguards.

This is an educational containerization project, not a production-ready clinical system or medical device.

## Author

**Dua Javed**
