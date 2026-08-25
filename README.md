# Pharmacovigilance Data Platform
 
An end-to-end, production-patterned **Pharmacovigilance (PV) Safety Data Platform** built on
Google Cloud Platform, developed as a portfolio project to demonstrate data engineering,
cloud architecture, and DevOps practices applied to a realistic pharma safety-data use case.
 
> ⚠️ **This project uses only synthetic/de-identified data.** No real patient, reporter, or
> confidential pharmaceutical company data is used anywhere in this repository.
 
## What this project does
 
Ingests synthetic Individual Case Safety Report (ICSR) data from multiple simulated sources
(XML, CSV, JSON, REST API, an operational database, and near-real-time event streams),
validates and standardizes it, detects duplicates without losing legitimate follow-up reports,
enriches it with reference data, and loads it into a layered BigQuery warehouse for
pharmacovigilance analytics.
 
## Architecture
 
See [`architecture/`](./architecture) for diagrams and design docs.
 
High-level flow:
 
Sources → GCS / Pub/Sub / Cloud SQL → Dataflow (Apache Beam) → validation → standardization
→ deduplication → enrichment → BigQuery (Bronze/Silver/Gold) → analytics marts
 
Orchestrated by Cloud Composer (batch) and Pub/Sub + Dataflow (streaming).
Secured with IAM, Secret Manager, and VPC. Observed via Cloud Logging/Monitoring.
Deployed via GitHub + Cloud Build CI/CD, provisioned with Terraform.
 
## Repository structure
 
| Folder | Contents |
|---|---|
| `architecture/` | Architecture diagrams, design decisions |
| `beam/` | Apache Beam pipeline source (batch + streaming) |
| `airflow/` | Cloud Composer / Airflow DAGs |
| `sql/` | BigQuery DDL, views, data marts, data-quality queries |
| `cloud_run/` | Cloud Run service source |
| `cloud_functions/` | Cloud Function source |
| `terraform/` | Infrastructure as Code |
| `tests/` | Unit and integration tests |
| `config/` | Non-secret environment configuration |
| `data/` | Synthetic data and generation scripts |
 
## Status
 
🚧 Actively being built phase-by-phase. See commit history for progress.
 
## Disclaimer
 
This is an educational/portfolio project. It does not implement, and should not be
interpreted as implementing, actual regulatory reporting compliance for any jurisdiction.
Regulatory concepts referenced are for illustrative/learning purposes only.
