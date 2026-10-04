# Warsaw Parking Data Collector & ETL Pipeline

Automated service designed to continuously ingest, process, and persist real-time parking availability across Warsaw using the Warsaw Open Data API. Built with a containerized PostgreSQL backend and pgAdmin web monitoring interface.

---

## Architecture Overview

- **Collector Service (`vacum.py`)**: Python worker polling the municipal API every 5 minutes with resilient JSON parsing, adaptive fallback matching, and automated retry mechanisms.
- **Relational Database (`PostgreSQL 15`)**: Relational storage separated into a static registry table and an append-only time-series log table.
- **Web UI (`pgAdmin 4`)**: Integrated browser dashboard for ad-hoc SQL querying and occupancy visualization.
- **Orchestration (`Docker Compose`)**: Complete stack managed via containerized networks and persistent volumes.

---

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed.

### 2. Configure Environment
Create your local environment file from the template:
```bash
cp .env.example .env

3. Deploy the Stack
Spin up the entire pipeline in background mode:

Bash
docker compose up --build -d
To inspect collector logs:

Bash
docker compose logs -f collector

Database Schema
The database parking_db initializes two primary entities via init.sql:

parkings (Dimension Table)

Tracks unique parking assets (name as primary key).

Stores capacity, geographical coordinates (latitude, longitude), operator metadata, and address.

Updates idempotently on incoming payloads via ON CONFLICT (name) DO UPDATE.

parking_occupancy_logs (Time-Series Fact Table)

Stores periodic measurements: free_public, free_disabled, free_electric, and total_free.

Records timestamped occupancy changes (recorded_at).

Retains full raw payload snapshot in jsonb format (raw_payload) for auditing and future schema evolution.

Web UI Access (pgAdmin)
URL: http://localhost:5050

Default Login: admin@admin.com

Default Password: admin

Connecting to the database in pgAdmin:

Host name/address: db (or parking_postgres)

Port: 5432

Maintenance database: parking_db

Username: postgres

Password: postgres (or value set in .env)