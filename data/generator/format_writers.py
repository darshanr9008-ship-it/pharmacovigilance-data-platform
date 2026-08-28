"""
Serializes generated case records (from case_generator.py) into
XML, CSV, and JSON files, matching the naming convention defined
in config/gcs_config.yaml.
"""

from __future__ import annotations

import csv
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(records: list[dict], output_dir: Path, batch_id: str) -> Path:
    """Write records as a single JSON array file (simulates a JSON feed export)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"icsr_json_{batch_id}_{_timestamp()}.json"
    path = output_dir / filename
    # Strip internal bookkeeping field before writing -- downstream pipelines
    # should not see our test-harness metadata.
    clean_records = [{k: v for k, v in r.items() if k != "_defect_type"} for r in records]
    with path.open("w", encoding="utf-8") as f:
        json.dump(clean_records, f, indent=2)
    logger.info("Wrote %d records to %s", len(records), path)
    return path


def write_csv(records: list[dict], output_dir: Path, batch_id: str) -> Path:
    """
    Write records as a flat CSV (one row per case, suspect drug + primary
    reaction only -- CSV is inherently flat, so multi-drug/multi-reaction
    detail is necessarily simplified here, which is realistic: CSV feeds
    from legacy systems often only carry the primary suspect drug/reaction.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"icsr_csv_{batch_id}_{_timestamp()}.csv"
    path = output_dir / filename

    fieldnames = [
        "case_id", "case_version", "report_type", "is_serious", "case_status",
        "report_source", "country_code", "received_date", "source_system",
        "patient_id", "patient_age", "patient_sex", "patient_weight_kg",
        "reporter_id", "reporter_type", "reporter_country",
        "suspect_drug_name", "suspect_drug_dose", "suspect_drug_route", "suspect_drug_indication",
        "primary_reaction_term", "primary_reaction_outcome",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            suspect = next((d for d in r.get("drugs", []) if d.get("drug_role") == "SUSPECT"), {})
            primary_reaction = r.get("reactions", [{}])[0] if r.get("reactions") else {}
            patient = r.get("patient") or {}
            reporter = r.get("reporter") or {}

            writer.writerow(
                {
                    "case_id": r.get("case_id"),
                    "case_version": r.get("case_version"),
                    "report_type": r.get("report_type"),
                    "is_serious": r.get("is_serious"),
                    "case_status": r.get("case_status"),
                    "report_source": r.get("report_source"),
                    "country_code": r.get("country_code"),
                    "received_date": r.get("received_date"),
                    "source_system": r.get("source_system"),
                    "patient_id": patient.get("patient_id"),
                    "patient_age": patient.get("age"),
                    "patient_sex": patient.get("sex"),
                    "patient_weight_kg": patient.get("weight_kg"),
                    "reporter_id": reporter.get("reporter_id"),
                    "reporter_type": reporter.get("reporter_type"),
                    "reporter_country": reporter.get("reporter_country"),
                    "suspect_drug_name": suspect.get("drug_name"),
                    "suspect_drug_dose": suspect.get("dose"),
                    "suspect_drug_route": suspect.get("route"),
                    "suspect_drug_indication": suspect.get("indication"),
                    "primary_reaction_term": primary_reaction.get("event_term"),
                    "primary_reaction_outcome": primary_reaction.get("outcome"),
                }
            )
    logger.info("Wrote %d records to %s", len(records), path)
    return path


def write_xml(records: list[dict], output_dir: Path, batch_id: str) -> Path:
    """
    Write records as an XML file, structured loosely in the spirit of
    case-exchange XML formats used in real PV systems (nested case/patient/
    reporter/drug/reaction elements) -- this is an illustrative, simplified
    schema for learning purposes, not a reproduction of any real regulatory
    XML standard or DTD.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"icsr_xml_{batch_id}_{_timestamp()}.xml"
    path = output_dir / filename

    root = ET.Element("ICSRBatch")
    for r in records:
        case_el = ET.SubElement(root, "Case")
        for key in [
            "case_id", "case_version", "report_type", "is_serious",
            "case_status", "report_source", "country_code",
            "received_date", "source_system",
        ]:
            el = ET.SubElement(case_el, key)
            el.text = str(r.get(key)) if r.get(key) is not None else ""

        patient = r.get("patient") or {}
        patient_el = ET.SubElement(case_el, "Patient")
        for k, v in patient.items():
            el = ET.SubElement(patient_el, k)
            el.text = str(v) if v is not None else ""

        reporter = r.get("reporter") or {}
        reporter_el = ET.SubElement(case_el, "Reporter")
        for k, v in reporter.items():
            el = ET.SubElement(reporter_el, k)
            el.text = str(v) if v is not None else ""

        drugs_el = ET.SubElement(case_el, "Drugs")
        for drug in r.get("drugs", []):
            drug_el = ET.SubElement(drugs_el, "Drug")
            for k, v in drug.items():
                el = ET.SubElement(drug_el, k)
                el.text = str(v) if v is not None else ""

        reactions_el = ET.SubElement(case_el, "Reactions")
        for reaction in r.get("reactions", []):
            reaction_el = ET.SubElement(reactions_el, "Reaction")
            for k, v in reaction.items():
                el = ET.SubElement(reaction_el, k)
                el.text = str(v) if v is not None else ""

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    logger.info("Wrote %d records to %s", len(records), path)
    return path