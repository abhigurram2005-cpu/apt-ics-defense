# Phase 2 Report: Infrastructure as Code (IaC) with Terraform

**Status:** Completed  
**Date:** 2026-09-16  
**Environment:** Terraform v1.16.2 with `kreuzwerker/docker` provider v3.0.2  

---

## 1. Executive Summary
Phase 2 transformed the entire simulated healthcare cloud infrastructure into declarative, reproducible, and parameterized Infrastructure as Code (IaC) using Terraform. 

The Docker Compose configuration was completely replaced with a clean modular Terraform architecture capable of managing multiple environments (`dev` and `prod`) with independent variable overrides (such as worker count, port mappings, and credentials).

---

## 2. Implemented Architecture & Module Structure

```text
infrastructure/terraform/
├── environments/
│   ├── dev/
│   │   └── dev.tfvars            # Lightweight config: 1 worker instance
│   └── prod/
│       └── prod.tfvars           # Production-like config: 2 worker instances
├── modules/
│   ├── network/                  # Creates frontend and backend Docker bridges
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── storage/                  # Creates persistent postgres_data volume
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   └── services/                 # Deploys containers, DNS aliases, mounts, and healthchecks
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── versions.tf
├── main.tf                       # Root module tying network, storage, and services together
├── variables.tf                  # Root input variables
├── outputs.tf                    # Ingress URL, container names
├── providers.tf                  # Docker provider configuration via Windows named pipe
└── versions.tf                   # Root Terraform requirements
```

---

## 3. Files Created & Configured

### Modules
1. **Network Module** (`modules/network/`):
   - [`main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/network/main.tf): Defines `${var.environment}-frontend-net` and `${var.environment}-backend-net`.
   - [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/network/outputs.tf): Exports network IDs and names.
   - [`versions.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/network/versions.tf): Declares `kreuzwerker/docker`.
2. **Storage Module** (`modules/storage/`):
   - [`main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/storage/main.tf): Defines persistent Docker volume `${var.environment}-postgres-data`.
   - [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/storage/outputs.tf): Exports volume name and ID.
   - [`versions.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/storage/versions.tf): Declares `kreuzwerker/docker`.
3. **Services Module** (`modules/services/`):
   - [`main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/services/main.tf): Configures all 7 containers with DNS aliases (`postgres`, `redis`, `ai-service`, `mock-ehr`, `api-blue`), healthchecks, dependencies (`depends_on`), persistent database volume, schema initialization mount (`init.sql`), and parameterized horizontal worker scaling (`count = var.worker_count`).
   - [`variables.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/services/variables.tf): Configures images, credentials, port, and worker counts.
   - [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/services/outputs.tf): Exports container names.
   - [`versions.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/services/versions.tf): Declares `kreuzwerker/docker`.

### Root & Environments
* [`infrastructure/terraform/providers.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/providers.tf): Points to `npipe:////./pipe/docker_engine`.
* [`infrastructure/terraform/main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/main.tf): Root orchestrator passing network IDs, volume name, and variables down to child modules.
* [`infrastructure/terraform/variables.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/variables.tf) & [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/outputs.tf): Exposes `ingress_url`, `postgres_container_name`, and `redis_container_name`.
* [`environments/dev/dev.tfvars`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/environments/dev/dev.tfvars): Development profile (`worker_count = 1`).
* [`environments/prod/prod.tfvars`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/environments/prod/prod.tfvars): Production profile (`worker_count = 2`).

---

## 4. Verification & Validation Evidence

### 1. Terraform Code Validation & Formatting
- `terraform fmt -recursive` passed cleanly.
- `terraform validate` returned:
  ```text
  Success! The configuration is valid.
  ```

### 2. Live Environment Deployment via Terraform Apply
The entire Docker Compose stack was cleanly torn down, and Terraform provisioned the production environment (`prod.tfvars`):
```text
Apply complete! Resources: 11 added, 0 changed, 10 destroyed.

Outputs:
ingress_url = "http://localhost:8080"
postgres_container_name = "prod-postgres"
redis_container_name = "prod-redis"
```

### 3. Container Status & Horizontal Worker Scaling
Running `docker ps` confirms that **two** background workers (`prod-worker-1` and `prod-worker-2`) are running alongside all other microservices:
```text
CONTAINER ID   NAMES            STATUS
9431aee0e92a   prod-nginx       Up 3 minutes (healthy)
cae44809a8cb   prod-worker-2    Up 3 minutes (healthy)
f46bacd9d973   prod-api-blue    Up 3 minutes (healthy)
63924901fb0e   prod-worker-1    Up 3 minutes (healthy)
1b9c41475d0a   prod-postgres    Up 3 minutes (healthy)
f8b2deda58d2   prod-redis       Up 3 minutes (healthy)
c6072102ab39   prod-mock-ehr    Up 3 minutes (healthy)
2f066945fee9   prod-ai-service  Up 3 minutes (healthy)
```

### 4. Database Schema Auto-Initialization
Verified schema creation inside `prod-postgres`:
```text
Schema |    Name    | Type  |  Owner   
--------+------------+-------+----------
 public | audit_logs | table | postgres
 public | jobs       | table | postgres
 public | patients   | table | postgres
(3 rows)
```

### 5. Ingress & End-to-End Transaction Flow
* **Health & Readiness**:
  ```json
  GET http://localhost:8080/ready
  {"ready": true, "database": "connected", "redis": "connected", "version": "v1.0.0", "color": "blue"}
  ```
* **Job Submission & Asynchronous Worker Consumption**:
  Submitted job `job-66627dd7` through Ingress (`dev-nginx`), which was immediately dispatched by `prod-worker-2`, synced against `prod-mock-ehr`, and marked completed:
  ```json
  GET http://localhost:8080/api/v1/jobs/job-66627dd7
  {
    "id": "job-66627dd7",
    "patient_id": "pat-003",
    "job_type": "ehr_sync",
    "status": "completed",
    "result": {
      "ehr_sync": {
        "external_record_id": "EXT-EHR-207715",
        "mrn": "MRN-1001",
        "status": "synchronized"
      },
      "processed_by": "cae44809a8cb",
      "latency_seconds": 0.015
    },
    "retry_count": 0
  }
  ```

---

## 5. Next Steps
Proceeding to **Phase 3 / Phase 4**: Observability Plane (Prometheus metrics scraping, alert rules, and pre-provisioned Grafana operational dashboards).
