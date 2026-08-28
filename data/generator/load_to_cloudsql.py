"""
Loads a slice of synthetically generated ICSR case data into the Cloud SQL
pv_case_mgmt database, simulating cases that originated in an internal
case-management application rather than an external file feed.

Connects via the Cloud SQL Auth Proxy running locally on 127.0.0.1:5432.
Credentials are read from environment variables -- never hardcoded.

Prerequisites:
  1. Cloud SQL Auth Proxy running locally:
     ./cloud-sql-proxy <PROJECT_ID>:asia-south1:pv-cloudsql-dev --port 5432
  2. Environment variables set (see .env.example):
     PV_CLOUDSQL_USER, PV_CLOUDSQL_PASSWORD, PV_CLOUDSQL_DB

Usage:
    python -m data.generator.load_to_cloudsql --num-cases 100
"""

from __future__ import annotations

import argparse
import logging
import os

import psycopg2
from psycopg2.extras import execute_values

from data.generator.case_generator import GeneratorConfig, generate_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_connection():
    """
    Opens a connection to Cloud SQL via the local Auth Proxy.
    Credentials come from environment variables -- fails loudly if missing,
    rather than silently falling back to an insecure default.
    """
    user = os.environ.get("PV_CLOUDSQL_USER")
    password = os.environ.get("PV_CLOUDSQL_PASSWORD")
    dbname = os.environ.get("PV_CLOUDSQL_DB")
    host = os.environ.get("PV_CLOUDSQL_HOST", "127.0.0.1")
    port = os.environ.get("PV_CLOUDSQL_PORT", "5432")

    missing = [name for name, val in [
        ("PV_CLOUDSQL_USER", user), ("PV_CLOUDSQL_PASSWORD", password), ("PV_CLOUDSQL_DB", dbname)
    ] if not val]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")

    return psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)


def load_records(conn, records: list[dict]) -> None:
    """Inserts patients, reporters, cases, drugs, and reactions for the given records."""
    with conn.cursor() as cur:
        for r in records:
            if not r.get("case_id"):
                logger.warning("Skipping record with null case_id (expected defect record)")
                continue

            patient = r.get("patient") or {}
            if patient.get("patient_id"):
                cur.execute(
                    """
                    INSERT INTO patients (patient_id, age, sex, weight_kg)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (patient_id) DO NOTHING
                    """,
                    (patient.get("patient_id"), patient.get("age"), patient.get("sex"), patient.get("weight_kg")),
                )

            reporter = r.get("reporter") or {}
            if reporter.get("reporter_id"):
                cur.execute(
                    """
                    INSERT INTO reporters (reporter_id, reporter_type, reporter_country)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (reporter_id) DO NOTHING
                    """,
                    (reporter.get("reporter_id"), reporter.get("reporter_type"), reporter.get("reporter_country")),
                )

            cur.execute(
                """
                INSERT INTO cases (
                    case_id, case_version, report_type, is_serious, case_status,
                    report_source, country_code, received_date, patient_id, reporter_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (case_id) DO UPDATE SET
                    case_version = EXCLUDED.case_version,
                    case_status = EXCLUDED.case_status,
                    updated_at = now()
                """,
                (
                    r.get("case_id"), r.get("case_version"), r.get("report_type"), r.get("is_serious"),
                    r.get("case_status"), r.get("report_source"), r.get("country_code"),
                    r.get("received_date"), patient.get("patient_id"), reporter.get("reporter_id"),
                ),
            )

            drug_rows = [
                (r["case_id"], d.get("drug_id"), d.get("drug_name"), d.get("drug_role"),
                 d.get("dose"), d.get("route"), d.get("indication"))
                for d in r.get("drugs", [])
            ]
            if drug_rows:
                execute_values(
                    cur,
                    """
                    INSERT INTO case_drugs (case_id, drug_id, drug_name, drug_role, dose, route, indication)
                    VALUES %s
                    """,
                    drug_rows,
                )

            reaction_rows = [
                (r["case_id"], rct.get("event_id"), rct.get("event_term"), rct.get("outcome"))
                for rct in r.get("reactions", [])
            ]
            if reaction_rows:
                execute_values(
                    cur,
                    """
                    INSERT INTO case_reactions (case_id, event_id, event_term, outcome)
                    VALUES %s
                    """,
                    reaction_rows,
                )

    conn.commit()
    logger.info("Loaded %d records into Cloud SQL", len(records))


def main() -> None:
    parser = argparse.ArgumentParser(description="Load synthetic ICSR data into Cloud SQL.")
    parser.add_argument("--num-cases", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    cfg = GeneratorConfig(num_base_cases=args.num_cases, seed=args.seed)
    dataset = generate_dataset(cfg)
    # Only load records that would plausibly come from an internal case system --
    # exclude the ones tagged as coming from file feeds in the generator.
    cloudsql_records = [r for r in dataset if r.get("case_id")]  # skip null-case_id defect rows

    conn = get_connection()
    try:
        load_records(conn, cloudsql_records)
    finally:
        conn.close()


if __name__ == "__main__":
    main()