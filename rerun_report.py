#!/usr/bin/env python3
"""Re-run Phase 6-7 (report) from saved artifacts — for report bug fixes without re-running the whole pipeline."""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import run_pipeline as v1
import run_pipeline_v2 as v2

_TOPIC = "用能权交易政策对工业企业绿色转型的影响"
_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "v2_run_output", "20260821_用能权交易政策对工业企业绿色转型的影响",
)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Re-run Phase 6-7 (report) from saved artifacts")
    ap.add_argument("--output-dir", default=_DEFAULT_DIR, help="run output dir")
    ap.add_argument("--topic", default=_TOPIC)
    ap.add_argument("--lang", default="zh")
    args = ap.parse_args()

    v1.TOPIC = args.topic
    v1.OUTPUT_LANG = args.lang if args.lang in ("zh", "en") else "zh"
    v1.OUTPUT_DIR = args.output_dir

    config = v2._load_config(v1.OUTPUT_DIR)
    papers = v2._load_papers(v1.OUTPUT_DIR)
    preprints = v2._load_preprints(v1.OUTPUT_DIR)
    if config is None or papers is None:
        print("ERROR: missing config/papers")
        return 1

    papers = v1.merge_seed_papers(papers)
    print(f"papers after seed merge: {len(papers)}")

    dept_outputs = {}
    for fp in sorted(glob.glob(os.path.join(v1.OUTPUT_DIR, "phase5_dept_*.json"))):
        key = os.path.basename(fp)[len("phase5_dept_"):-len(".json")]
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            dept_outputs[data.get("department_key", key)] = data
    print(f"loaded dept_outputs: {len(dept_outputs)} departments")

    relevance_log = {"domain_config_driven": True, "resumed": True}

    report = v2._run_phases_6_to_7(config, papers, preprints, dept_outputs, relevance_log)
    print(f"DONE. report length: {len(report)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
