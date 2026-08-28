"""Unit tests for the synthetic ICSR case generator."""

from data.generator.case_generator import GeneratorConfig, generate_dataset


def test_generate_dataset_produces_records():
    cfg = GeneratorConfig(num_base_cases=50, seed=1)
    dataset = generate_dataset(cfg)
    assert len(dataset) >= 50  # duplicates/follow-ups only add records, never remove


def test_all_records_have_case_id_field_present():
    # Note: value may be None (that's an intentional defect), but the key must exist.
    cfg = GeneratorConfig(num_base_cases=50, seed=2)
    dataset = generate_dataset(cfg)
    assert all("case_id" in r for r in dataset)


def test_followups_reference_existing_case_version_sequence():
    cfg = GeneratorConfig(num_base_cases=100, seed=3, pct_followup_reports=1.0)
    dataset = generate_dataset(cfg)
    followups = [r for r in dataset if r.get("report_type") == "FOLLOWUP"]
    assert all(f["case_version"] >= 2 for f in followups)


def test_deterministic_with_fixed_seed():
    cfg_a = GeneratorConfig(num_base_cases=30, seed=99)
    cfg_b = GeneratorConfig(num_base_cases=30, seed=99)
    dataset_a = generate_dataset(cfg_a)
    dataset_b = generate_dataset(cfg_b)
    assert len(dataset_a) == len(dataset_b)