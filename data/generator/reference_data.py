"""
Static reference/lookup data used by the synthetic ICSR generator.

These lists are intentionally small and clearly synthetic. Drug names and
adverse event terms are NOT real product names or real MedDRA terminology --
they are illustrative, made-up values styled to resemble the *shape* of
real pharmacovigilance reference data for learning purposes only.
"""

from __future__ import annotations

# Synthetic "generic-style" drug names -- not real marketed drug names.
DRUGS: list[dict[str, str]] = [
    {"drug_id": "DRG-001", "drug_name": "Synthovan", "drug_class": "Analgesic (synthetic)"},
    {"drug_id": "DRG-002", "drug_name": "Cardiazolan", "drug_class": "Cardiovascular (synthetic)"},
    {"drug_id": "DRG-003", "drug_name": "Neurotrapin", "drug_class": "CNS agent (synthetic)"},
    {"drug_id": "DRG-004", "drug_name": "Glucoprine", "drug_class": "Antidiabetic (synthetic)"},
    {"drug_id": "DRG-005", "drug_name": "Respiraxol", "drug_class": "Respiratory agent (synthetic)"},
    {"drug_id": "DRG-006", "drug_name": "Dermacillin", "drug_class": "Dermatological (synthetic)"},
    {"drug_id": "DRG-007", "drug_name": "Hepatozan", "drug_class": "Hepatic support (synthetic)"},
    {"drug_id": "DRG-008", "drug_name": "Immunexa", "drug_class": "Immunomodulator (synthetic)"},
    {"drug_id": "DRG-009", "drug_name": "Renalprin", "drug_class": "Renal agent (synthetic)"},
    {"drug_id": "DRG-010", "drug_name": "Oncovera", "drug_class": "Oncology support (synthetic)"},
]

# Synthetic "Preferred Term"-styled adverse event descriptions -- NOT real MedDRA terms.
ADVERSE_EVENTS: list[dict[str, str]] = [
    {"event_id": "AE-001", "event_term": "Headache (synthetic term)", "event_category": "Nervous system"},
    {"event_id": "AE-002", "event_term": "Nausea (synthetic term)", "event_category": "Gastrointestinal"},
    {"event_id": "AE-003", "event_term": "Skin rash (synthetic term)", "event_category": "Skin"},
    {"event_id": "AE-004", "event_term": "Dizziness (synthetic term)", "event_category": "Nervous system"},
    {"event_id": "AE-005", "event_term": "Elevated liver enzymes (synthetic term)", "event_category": "Hepatobiliary"},
    {"event_id": "AE-006", "event_term": "Fatigue (synthetic term)", "event_category": "General disorders"},
    {"event_id": "AE-007", "event_term": "Palpitations (synthetic term)", "event_category": "Cardiac"},
    {"event_id": "AE-008", "event_term": "Shortness of breath (synthetic term)", "event_category": "Respiratory"},
    {"event_id": "AE-009", "event_term": "Injection site reaction (synthetic term)", "event_category": "General disorders"},
    {"event_id": "AE-010", "event_term": "Anaphylactic reaction (synthetic term)", "event_category": "Immune system"},
]

INDICATIONS: list[str] = [
    "Hypertension (synthetic)", "Type 2 diabetes (synthetic)", "Chronic pain (synthetic)",
    "Asthma (synthetic)", "Depression (synthetic)", "Bacterial infection (synthetic)",
    "Rheumatoid arthritis (synthetic)", "Migraine (synthetic)",
]

COUNTRY_CODES: list[str] = ["IN", "US", "GB", "DE", "FR", "JP", "BR", "AU", "CA", "ZA"]

REPORTER_TYPES: list[str] = ["PHYSICIAN", "PHARMACIST", "CONSUMER", "OTHER_HCP", "NURSE"]

REPORT_SOURCES: list[str] = [
    "SPONTANEOUS", "CLINICAL_TRIAL", "LITERATURE", "CALL_CENTER", "REGULATORY_AUTHORITY",
]

ROUTES: list[str] = ["ORAL", "IV", "TOPICAL", "SUBCUTANEOUS", "INTRAMUSCULAR"]

OUTCOMES: list[str] = ["RECOVERED", "RECOVERING", "NOT_RECOVERED", "FATAL", "UNKNOWN"]

SERIOUSNESS_CRITERIA_OPTIONS: list[str] = [
    "HOSPITALIZATION", "LIFE_THREATENING", "DEATH", "DISABILITY", "CONGENITAL_ANOMALY",
    "OTHER_MEDICALLY_IMPORTANT",
]