# Phase 1 Report: Application Simulation & Docker Orchestration

**Status:** Completed  
**Date:** 2026-09-16  
**Environment:** Local Docker Engine (Linux containers on WSL2)  

---

## 1. Executive Summary
Phase 1 focused on building the core microservices, network segmentation, and local container orchestration for the simulated AI-powered healthcare platform. All target services have been packaged into hardened, non-root Docker images, wired into segmented private/public virtual networks, and verified through live end-to-end transaction flows.

---

## 2. Implemented Components & Microservices

| Service Name | Technology / Framework | Role & Scope | Network Placement | Security Hardening |
|---|---|---|---|---|
| **NGINX Ingress** | NGINX 1.25 Alpine | Reverse proxy, public entry point, Blue-Green traffic routing | `frontend-net` (Exposes port `8080` to host) | Read-only configuration, JSON structured access logging |
| **API Service (Blue)** | Python 3.11, FastAPI, Uvicorn | Public gateway for patients, jobs, and diagnostics | `frontend-net`, `backend-net` | Non-root (`appuser:10001`), Multi-stage minimal build |
| **AI Service** | Python 3.11, FastAPI | Internal AI / LLM diagnostic simulation | `backend-net` (Private) | Non-root (`appuser:10001`), Not exposed to host |
| **Background Worker** | Python 3.11, Redis Client, psycopg2 | Asynchronous queue consumer, EHR sync, DB state persistence | `backend-net` (Private) | Non-root (`appuser:10001`), Independent metric exporter |
| **Redis Queue** | Redis 7.2 Alpine | In-memory asynchronous job queue | `backend-net` (Private) | Internal bridge, No host port binding |
| **PostgreSQL DB** | PostgreSQL 16 Alpine | Relational persistence for patients, jobs, and audit logs | `backend-net` (Private) | Isolated from public, initialization scripts mounted read-only |
| **Mock EHR** | Python 3.11, FastAPI | External EHR dependency simulator with runtime failure modes | `backend-net` (Private) | Non-root (`appuser:10001`), Configurable via `EHR_MODE` |

---

## 3. Files Created & Modified

### Services & Application Code
* [`services/api/app/main.py`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/api/app/main.py): FastAPI endpoints (`/health`, `/ready`, `/metrics`, `/api/v1/patients`, `/api/v1/jobs`, `/api/v1/diagnose`), DB & Redis connection pools, and request instrumentation.
* [`services/api/requirements.txt`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/api/requirements.txt): API dependencies (FastAPI, Redis, Psycopg2, Prometheus-client).
* [`services/api/Dockerfile`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/api/Dockerfile): Multi-stage hardened build with unprivileged `appuser:10001`.
* [`services/ai-service/app/main.py`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/ai-service/app/main.py): AI diagnostic simulation endpoint (`/generate`) with synthetic inference latency.
* [`services/ai-service/requirements.txt`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/ai-service/requirements.txt): Minimal dependencies for AI mock.
* [`services/ai-service/Dockerfile`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/ai-service/Dockerfile): Hardened non-root image.
* [`services/worker/app/main.py`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/worker/app/main.py): Worker consumer loop, exponential retry backoff, database state updating, and Prometheus metrics server on port `9100`.
* [`services/worker/requirements.txt`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/worker/requirements.txt): Worker runtime dependencies.
* [`services/worker/Dockerfile`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/worker/Dockerfile): Hardened non-root image.
* [`services/mock-ehr/app/main.py`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/mock-ehr/app/main.py): External EHR integration simulation supporting `normal`, `slow`, `timeout`, `error_500`, `auth_error`, and `unavailable`.
* [`services/mock-ehr/requirements.txt`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/mock-ehr/requirements.txt): Mock EHR dependencies.
* [`services/mock-ehr/Dockerfile`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/services/mock-ehr/Dockerfile): Hardened non-root image.

### Infrastructure, Ingress & Orchestration
* [`infrastructure/database/init.sql`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/database/init.sql): Schema definition (`patients`, `jobs`, `audit_logs`), indexes, and mock seed records.
* [`deployment/nginx/nginx.conf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/deployment/nginx/nginx.conf): Reverse proxy setup with structured JSON logging and upstream inclusion.
* [`deployment/nginx/conf.d/upstream.conf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/deployment/nginx/conf.d/upstream.conf): Upstream pool routing to active `api-blue:8000`.
* [`docker-compose.yml`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/docker-compose.yml): Multi-tier composition defining health checks, volumes, dual networks, and dependency ordering.
* [`.env`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/.env) & [`.env.example`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/.env.example): Environment variable templates.
* [`.gitignore`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/.gitignore): Security-oriented ignore patterns (preventing `.env`, credentials, and Terraform states from leaking).

---

## 4. Verification & Validation Evidence

### 1. Container Health Status (`docker compose ps`)
All 7 services are running and verified **healthy** via Docker healthchecks:
```text
NAME                     SERVICE      STATUS                    PORTS
healthcare-nginx         nginx        Up (healthy)              0.0.0.0:8080->80/tcp
healthcare-api-blue      api-blue     Up (healthy)              8000/tcp (internal)
healthcare-ai-service    ai-service   Up (healthy)              8082/tcp (internal)
healthcare-mock-ehr      mock-ehr     Up (healthy)              8083/tcp (internal)
healthcare-worker-1      worker       Up (healthy)              9100/tcp (internal)
healthcare-postgres      postgres     Up (healthy)              5432/tcp (internal)
healthcare-redis         redis        Up (healthy)              6379/tcp (internal)
```

### 2. Public Ingress & Dependency Readiness Checks
* Ingress Health:
  ```json
  GET http://localhost:8080/health
  {"status": "healthy", "service": "api", "version": "v1.0.0", "color": "blue"}
  ```
* Readiness Check (verifying PostgreSQL and Redis connectivity through API):
  ```json
  GET http://localhost:8080/ready
  {"ready": true, "database": "connected", "redis": "connected", "version": "v1.0.0", "color": "blue"}
  ```

### 3. Database State Query
* Seed data loaded correctly from `init.sql`:
  ```json
  GET http://localhost:8080/api/v1/patients
  {"count": 3, "patients": [{"id": "pat-001", "mrn": "MRN-1001", "first_name": "Alice", ...}]}
  ```

### 4. Private AI Inference Routing
* Successfully called internal `ai-service` via API proxy:
  ```json
  POST http://localhost:8080/api/v1/diagnose
  Payload: {"patient_id": "pat-001", "symptoms": ["headache", "mild fever", "cough"]}
  Response: {
    "patient_id": "pat-001",
    "model": "clinical-bert-v2",
    "inference_duration_sec": 0.151,
    "confidence_score": 0.942
  }
  ```

### 5. Asynchronous Job & Worker Lifecycle
* Submitted asynchronous job -> Enqueued in Redis -> Worker consumed job -> Worker called Mock EHR -> Database state updated:
  ```json
  GET http://localhost:8080/api/v1/jobs/job-159defc8
  {
    "id": "job-159defc8",
    "patient_id": "pat-001",
    "job_type": "ehr_sync",
    "status": "completed",
    "result": {
      "processed_by": "48b31826fb7d",
      "latency_seconds": 0.017,
      "ehr_sync": {
        "external_record_id": "EXT-EHR-759547",
        "mrn": "MRN-1001",
        "status": "synchronized"
      }
    },
    "retry_count": 0
  }
  ```

### 6. Network Isolation Verification
* Port 8080 is accessible from host.
* Port 5432 (PostgreSQL) and Port 6379 (Redis) are strictly blocked from external/host access (`Connection refused`).

---

## 5. Next Steps
Proceeding to **Phase 2 / Phase 3**: Container Security Hardening, Automated Security Scanning (Trivy/Gitleaks), and Infrastructure as Code (IaC) with Terraform modularization.
