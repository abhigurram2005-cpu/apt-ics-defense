# Phase 3 Report: Observability Plane (Prometheus, Alerting & Grafana)

**Status:** Completed  
**Date:** 2026-09-16  
**Stack Components:** Prometheus v2.50.1, Grafana 10.3.3, Terraform `modules/monitoring`  

---

## 1. Executive Summary
Phase 3 established the end-to-end **Observability Plane** for the simulated healthcare platform. 

Prometheus is configured to continuously scrape all core services (`api-service`, `worker-1`, `worker-2`, `ai-service`, `mock-ehr`) on a 5-second interval. Five actionable operational alerting rules were installed to monitor service availability, error rates, worker availability, queue backlogs, and upstream EHR failures. Additionally, Grafana was provisioned with an automated Prometheus datasource and a pre-built **Operational Overview Dashboard** (`healthcare-overview`).

Both Prometheus and Grafana are fully managed as code via the Terraform `modules/monitoring` module.

---

## 2. Implemented Architecture & Scrape Topography

```text
               PROMETHEUS (Port 9090)
                       │
       ┌───────────────┼───────────────┬───────────────┐
       ▼               ▼               ▼               ▼
  api-blue:8000   worker-1:9100   worker-2:9100   ai-service:8082
  (API Metrics)   (Worker #1)     (Worker #2)     (AI Latency)
       │
       ▼
  mock-ehr:8083 (EHR Health & Latency)

                       │
                       ▼  (Datasource proxy)
               GRAFANA (Port 3000)
             Pre-provisioned Dashboard:
     "Healthcare Platform - Operational Overview"
```

---

## 3. Files Created & Configured

### Monitoring & Alerting Configurations
* [`monitoring/prometheus/prometheus.yml`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/monitoring/prometheus/prometheus.yml): Global 5s scrape interval, scrape jobs for API, workers, AI service, and Mock EHR.
* [`monitoring/prometheus/alerts.yml`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/monitoring/prometheus/alerts.yml): Prometheus alerting rules:
  1. `APIServiceDown`: Triggers if `up{job="api-service"} == 0` for >10s.
  2. `HighHTTP5xxErrorRate`: Triggers if HTTP 5xx rate > 0.1 req/s for >15s.
  3. `WorkerUnavailable`: Triggers if active worker count drops to 0 for >10s.
  4. `QueueBacklogSpike`: Triggers if Redis queue depth exceeds 10 jobs for >15s.
  5. `EHRFailureRateHigh`: Triggers if Mock EHR returns 5xx/504 errors for >10s.
* [`monitoring/grafana/provisioning/datasources/prometheus.yml`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/monitoring/grafana/provisioning/datasources/prometheus.yml): Automatically registers Prometheus datasource in Grafana (`http://prometheus:9090`).
* [`monitoring/grafana/provisioning/dashboards/dashboard.yml`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/monitoring/grafana/provisioning/dashboards/dashboard.yml): Automatic dashboard loader provider.
* [`monitoring/grafana/provisioning/dashboards/healthcare_overview.json`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/monitoring/grafana/provisioning/dashboards/healthcare_overview.json): Pre-configured production dashboard containing:
  - API Service Status (Stat panel with UP/DOWN color mapping)
  - Active Workers Count (Stat panel tracking worker health)
  - Live Queue Depth (Stat panel with color thresholds)
  - Mock EHR Status (Stat panel)
  - HTTP Request Rate & 5xx Rate (Time-series)
  - API Latency p95 (Time-series)
  - Worker Processing Throughput vs Failure Rate (Time-series)
  - Live Queue Backlog History (Time-series)

### Infrastructure as Code (Terraform)
* [`infrastructure/terraform/modules/monitoring/main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/monitoring/main.tf): Defines `prom/prometheus:v2.50.1` and `grafana/grafana:10.3.3` containers attached to the internal `backend-net`, mounting config files read-only and exposing ports 9090 and 3000.
* [`infrastructure/terraform/modules/monitoring/variables.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/monitoring/variables.tf) & [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/monitoring/outputs.tf): Parameterized ports and outputs for `prometheus_url` and `grafana_url`.
* [`infrastructure/terraform/modules/monitoring/versions.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/modules/monitoring/versions.tf): Declares `kreuzwerker/docker` provider.
* [`infrastructure/terraform/main.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/main.tf) & [`outputs.tf`](file:///c:/Users/yadid/OneDrive/Desktop/projects/Cloud-Infra-Simulation-for-HealthCare-Platform/infrastructure/terraform/outputs.tf): Connected monitoring module to root Terraform plan.

---

## 4. Verification & Validation Evidence

### 1. Prometheus Scrape Target Verification (`/api/v1/targets`)
All 5 target jobs are actively discovered and reporting **`health: "up"`**:
- `api-service` (`http://api-blue:8000/metrics`) -> **UP**
- `worker-service` (`http://worker-1:9100/metrics`) -> **UP**
- `worker-service` (`http://worker-2:9100/metrics`) -> **UP**
- `ai-service` (`http://ai-service:8082/metrics`) -> **UP**
- `mock-ehr` (`http://mock-ehr:8083/metrics`) -> **UP**
- `prometheus` (`http://localhost:9090/metrics`) -> **UP**

### 2. Prometheus Alert Rule Engine Verification (`/api/v1/rules`)
Queried `http://localhost:9090/api/v1/rules`:
- Rule group `healthcare_platform_alerts` loaded successfully.
- 5 rules registered: `APIServiceDown`, `HighHTTP5xxErrorRate`, `WorkerUnavailable`, `QueueBacklogSpike`, `EHRFailureRateHigh`.
- Alert evaluation engine is running cleanly every 5 seconds (`health: "ok"`).

### 3. Grafana Automated Provisioning Verification (`/api/dashboards/uid/healthcare-overview`)
Queried `http://localhost:3000/api/dashboards/uid/healthcare-overview`:
- Prometheus data source is connected and functional.
- Dashboard `Healthcare Platform - Operational Overview` loaded automatically with `provisioned: true`.
- Anonymous Viewer access is enabled by default so dashboards can be viewed immediately in any browser at `http://localhost:3000`.

---

## 5. Next Steps
Proceeding to **Phase 4 / Phase 5**: CI/CD Automation, Security Scanning (Trivy & Gitleaks), and the automated **Zero-Downtime Blue-Green Deployment** controller.
