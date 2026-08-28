"""
Entry point: generates the full synthetic ICSR dataset and writes it out
split across XML, CSV, and JSON files, matching each record's assigned
source_system. Also writes a summary report of the known defect distribution
for later verification against the data-quality framework (Phase 13).

Usage:
    python -m data.generator.generate_all --output-dir data/generated --batch-id batch0001
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from data.generator.case_generator import GeneratorConfig, generate_dataset
from data.generator.format_writers import write_csv, write_json, write_xml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic PV ICSR data.")
    parser.add_argument("--output-dir", type=str, default="data/generated")
    parser.add_argument("--batch-id", type=str, default="batch0001")
    parser.add_argument("--num-cases", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = GeneratorConfig(num_base_cases=args.num_cases, seed=args.seed)
    dataset = generate_dataset(cfg)

    output_dir = Path(args.output_dir)

    json_records = [r for r in dataset if r["source_system"] == "JSON_FEED"]
    csv_records = [r for r in dataset if r["source_system"] == "CSV_FEED"]
    xml_records = [r for r in dataset if r["source_system"] == "XML_FEED"]

    write_json(json_records, output_dir / "icsr_json", args.batch_id)
    write_csv(csv_records, output_dir / "icsr_csv", args.batch_id)
    write_xml(xml_records, output_dir / "icsr_xml", args.batch_id)

    defect_summary = Counter(r["_defect_type"] for r in dataset)
    summary_path = output_dir / f"defect_summary_{args.batch_id}.json"
    with summary_path.open("w") as f:
        json.dump(dict(defect_summary), f, indent=2)

    logger.info("=== Generation Summary ===")
    for defect_type, count in defect_summary.items():
        logger.info("  %-28s %d", defect_type, count)
    logger.info("Total records: %d", len(dataset))
    logger.info("Summary written to %s", summary_path)


if __name__ == "__main__":
    main()