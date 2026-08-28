"""
Core synthetic ICSR case generator.

Produces a list of case "records" (as plain Python dicts) representing:
  - valid initial reports
  - valid follow-up reports
  - records with missing required fields
  - records with invalid enum/date values
  - exact duplicate records
  - business-key duplicate records (same case_id + version, minor field differs)

This module has NO knowledge of output file format (XML/CSV/JSON) --
see format_writers.py for that. Keeping generation and serialization
separate makes it easy to add new source formats later without touching
the domain logic.
"""

from __future__ import annotations

import copy
import logging
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from data.generator.reference_data import (
    ADVERSE_EVENTS,
    COUNTRY_CODES,
    DRUGS,
    INDICATIONS,
    OUTCOMES,
    REPORT_SOURCES,
    REPORTER_TYPES,
    ROUTES,
    SERIOUSNESS_CRITERIA_OPTIONS,
)

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Controls the shape and known-defect distribution of generated data."""

    num_base_cases: int = 500
    seed: int = 42

    pct_missing_required_fields: float = 0.08
    pct_invalid_enum_values: float = 0.05
    pct_invalid_dates: float = 0.03
    pct_exact_duplicates: float = 0.04
    pct_business_key_duplicates: float = 0.04
    pct_followup_reports: float = 0.06

    source_systems: tuple[str, ...] = ("XML_FEED", "CSV_FEED", "JSON_FEED")


def _random_date(start_year: int = 2024, end_year: int = 2026) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def _generate_base_case(case_index: int, cfg: GeneratorConfig) -> dict:
    """Generate one clean, valid case record."""
    case_id = f"CASE-{case_index:06d}"
    patient_id = f"PT-{case_index:06d}"
    reporter_id = f"RPT-{case_index:06d}"

    suspect_drug = random.choice(DRUGS)
    num_concomitant = random.randint(0, 2)
    concomitant_drugs = random.sample(
        [d for d in DRUGS if d["drug_id"] != suspect_drug["drug_id"]], num_concomitant
    )

    num_reactions = random.randint(1, 3)
    reactions = random.sample(ADVERSE_EVENTS, num_reactions)

    is_serious = random.random() < 0.25  # ~25% of clean cases are serious
    seriousness_criteria = (
        random.sample(SERIOUSNESS_CRITERIA_OPTIONS, random.randint(1, 2)) if is_serious else []
    )

    record = {
        "case_id": case_id,
        "case_version": 1,
        "report_type": "INITIAL",
        "is_serious": is_serious,
        "seriousness_criteria": seriousness_criteria,
        "case_status": "OPEN",
        "report_source": random.choice(REPORT_SOURCES),
        "country_code": random.choice(COUNTRY_CODES),
        "received_date": _random_date().isoformat(),
        "source_system": random.choice(cfg.source_systems),
        "patient": {
            "patient_id": patient_id,
            "age": random.randint(1, 95),
            "sex": random.choice(["M", "F", "U"]),
            "weight_kg": round(random.uniform(4.0, 120.0), 1),
        },
        "reporter": {
            "reporter_id": reporter_id,
            "reporter_type": random.choice(REPORTER_TYPES),
            "reporter_country": random.choice(COUNTRY_CODES),
        },
        "drugs": [
            {
                "drug_id": suspect_drug["drug_id"],
                "drug_name": suspect_drug["drug_name"],
                "drug_role": "SUSPECT",
                "dose": f"{random.choice([5, 10, 20, 50, 100])} mg",
                "route": random.choice(ROUTES),
                "indication": random.choice(INDICATIONS),
            }
        ]
        + [
            {
                "drug_id": d["drug_id"],
                "drug_name": d["drug_name"],
                "drug_role": "CONCOMITANT",
                "dose": f"{random.choice([5, 10, 20, 50])} mg",
                "route": random.choice(ROUTES),
                "indication": random.choice(INDICATIONS),
            }
            for d in concomitant_drugs
        ],
        "reactions": [
            {
                "event_id": r["event_id"],
                "event_term": r["event_term"],
                "outcome": random.choice(OUTCOMES),
            }
            for r in reactions
        ],
    }
    return record


def _make_followup(base_case: dict) -> dict:
    """Create a legitimate follow-up report referencing the same case_id."""
    followup = copy.deepcopy(base_case)
    followup["case_version"] = base_case["case_version"] + 1
    followup["report_type"] = "FOLLOWUP"
    followup["case_status"] = random.choice(["UNDER_REVIEW", "CLOSED"])
    # Follow-ups commonly update outcome information as new facts emerge.
    for reaction in followup["reactions"]:
        reaction["outcome"] = random.choice(OUTCOMES)
    return followup


def _make_exact_duplicate(record: dict) -> dict:
    """Byte-identical resubmission (simulates a feed retry / duplicate transmission)."""
    return copy.deepcopy(record)


def _make_business_key_duplicate(record: dict) -> dict:
    """Same case_id + case_version, but a minor non-key field differs.

    Simulates a common real-world defect: the same case resubmitted with
    a trivial formatting difference, which naive exact-match dedup would miss.
    """
    dup = copy.deepcopy(record)
    dup["received_date"] = _random_date().isoformat()
    if dup["drugs"]:
        dup["drugs"][0]["dose"] = dup["drugs"][0]["dose"].replace(" mg", "mg")  # spacing quirk
    return dup


def _corrupt_missing_fields(record: dict) -> dict:
    """Null out one or more required fields."""
    corrupted = copy.deepcopy(record)
    field_choice = random.choice(["country_code", "case_id", "patient.sex", "reporter.reporter_type"])
    if field_choice == "country_code":
        corrupted["country_code"] = None
    elif field_choice == "case_id":
        corrupted["case_id"] = None
    elif field_choice == "patient.sex":
        corrupted["patient"]["sex"] = None
    elif field_choice == "reporter.reporter_type":
        corrupted["reporter"]["reporter_type"] = None
    return corrupted


def _corrupt_invalid_enum(record: dict) -> dict:
    """Substitute an invalid value into an enum field."""
    corrupted = copy.deepcopy(record)
    field_choice = random.choice(["sex", "route", "report_source"])
    if field_choice == "sex":
        corrupted["patient"]["sex"] = "X"
    elif field_choice == "route" and corrupted["drugs"]:
        corrupted["drugs"][0]["route"] = "UNKNOWN_ROUTE"
    elif field_choice == "report_source":
        corrupted["report_source"] = "NOT_A_REAL_SOURCE"
    return corrupted


def _corrupt_invalid_date(record: dict) -> dict:
    """Corrupt the received_date field -- future date or malformed string."""
    corrupted = copy.deepcopy(record)
    if random.random() < 0.5:
        corrupted["received_date"] = "2099-01-01"  # implausible future date
    else:
        corrupted["received_date"] = "NOT-A-DATE"
    return corrupted


def generate_dataset(cfg: GeneratorConfig | None = None) -> list[dict]:
    """
    Generate the full synthetic ICSR dataset per the configured defect distribution.

    Returns a flat list of case records (dicts) ready for serialization by
    format_writers.py. Each record includes an internal `_defect_type` tag
    for traceability (used only for logging / dataset documentation, not
    written into output files consumed by downstream pipelines).
    """
    cfg = cfg or GeneratorConfig()
    random.seed(cfg.seed)
    logger.info("Generating %d base cases with seed=%d", cfg.num_base_cases, cfg.seed)

    base_cases = [_generate_base_case(i, cfg) for i in range(1, cfg.num_base_cases + 1)]
    dataset: list[dict] = []

    for record in base_cases:
        roll = random.random()
        if roll < cfg.pct_missing_required_fields:
            corrupted = _corrupt_missing_fields(record)
            corrupted["_defect_type"] = "MISSING_REQUIRED_FIELD"
            dataset.append(corrupted)
        elif roll < cfg.pct_missing_required_fields + cfg.pct_invalid_enum_values:
            corrupted = _corrupt_invalid_enum(record)
            corrupted["_defect_type"] = "INVALID_ENUM"
            dataset.append(corrupted)
        elif roll < (
            cfg.pct_missing_required_fields + cfg.pct_invalid_enum_values + cfg.pct_invalid_dates
        ):
            corrupted = _corrupt_invalid_date(record)
            corrupted["_defect_type"] = "INVALID_DATE"
            dataset.append(corrupted)
        else:
            clean = copy.deepcopy(record)
            clean["_defect_type"] = "VALID"
            dataset.append(clean)

        # Independently decide on duplicates / follow-ups layered on top
        if random.random() < cfg.pct_exact_duplicates:
            dup = _make_exact_duplicate(record)
            dup["_defect_type"] = "EXACT_DUPLICATE"
            dataset.append(dup)

        if random.random() < cfg.pct_business_key_duplicates:
            dup = _make_business_key_duplicate(record)
            dup["_defect_type"] = "BUSINESS_KEY_DUPLICATE"
            dataset.append(dup)

        if random.random() < cfg.pct_followup_reports:
            followup = _make_followup(record)
            followup["_defect_type"] = "VALID_FOLLOWUP"
            dataset.append(followup)

    random.shuffle(dataset)
    logger.info("Generated %d total records (base + defects + duplicates + follow-ups)", len(dataset))
    return dataset