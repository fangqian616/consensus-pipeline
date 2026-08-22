#!/usr/bin/env python3
"""
run_atomic_verify.py — Standalone citation-grounded atomic fact verification (原子校验).

Decomposes the final report into atomic factual claims and verifies each against
the abstract of its cited paper via NLI (entail / contradict / neutral), producing
a CitationVerificationReport (verified / partially / contradicted / unverified
counts + overall confidence).

Usage:
    python run_atomic_verify.py --report <final_report.md> [--out <result.json>] [--lang zh]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env (API key / model)
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except Exception:
    pass

import requests  # noqa: E402

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")


def llm_call(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    if not API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set — cannot run atomic verification")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": 8192,
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="path to final report markdown")
    ap.add_argument("--out", default=None, help="output JSON path")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--max-claims", type=int, default=20)
    ap.add_argument("--max-contexts", type=int, default=15)
    args = ap.parse_args()

    from requirement.citation_verifier import CitationVerifier

    with open(args.report, encoding="utf-8") as f:
        report_text = f.read()

    verifier = CitationVerifier(
        llm_call_fn=llm_call,
        language=args.lang if args.lang in ("zh", "en") else "zh",
        max_claims=args.max_claims,
        max_contexts=args.max_contexts,
    )
    cv = verifier.verify(report_text)

    out_path = args.out or (os.path.splitext(args.report)[0] + ".verification.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cv.to_dict(), f, ensure_ascii=False, indent=2)

    result = {
        "status": "done",
        "total_references": cv.total_references,
        "resolved_references": cv.resolved_references,
        "total_citations": cv.total_citations,
        "total_claims": cv.total_claims,
        "verified": cv.verified,
        "partially_verified": cv.partially_verified,
        "contradicted": cv.contradicted,
        "unverified": cv.unverified,
        "insufficient_evidence": cv.insufficient_evidence,
        "needs_fulltext": cv.needs_fulltext,
        "overall_confidence": cv.overall_confidence,
        "summary": cv.summary,
        "output": out_path,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
