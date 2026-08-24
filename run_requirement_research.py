#!/usr/bin/env python3
"""
run_requirement_research.py — Standalone Phase 0-3 runner.

需求调研 → 需求结构化 → 讨论组 → 工作组配置推荐。

Takes a research topic + a free-text requirements summary (collected by the
DSH agent during a conversational interview), runs the requirement pipeline,
and prints the recommended department configuration as JSON.

Usage:
    python run_requirement_research.py --topic "..." --requirements "..." --lang zh
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

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def llm_call(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    if not API_KEY:
        print("[WARN] DEEPSEEK_API_KEY not set — requirement extraction will fall back to rule-based", file=sys.stderr)
        return ""
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
        print(f"  [LLM ERROR] {e}", file=sys.stderr)
        return ""


def save_json(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--requirements", default="")
    ap.add_argument("--lang", default="zh")
    args = ap.parse_args()

    topic = args.topic.strip()
    requirements = args.requirements.strip()
    lang = args.lang if args.lang in ("zh", "en") else "zh"

    from requirement.interviewer import RequirementInterviewer
    from requirement.structurer import RequirementStructurer
    from requirement.discussion_group import DiscussionGroup
    from requirement.config_recommender import ConfigRecommender

    # ── Phase 0: requirement interview ────────────────────────────────────
    interviewer = RequirementInterviewer(
        llm_call_fn=llm_call,
        domain_hint="academic_research",
        max_rounds=8,
        language=lang,
    )
    interviewer.start(f"I want to research {topic}")
    if requirements:
        interviewer.chat(requirements)
    doc = interviewer.force_complete()
    # 修正 topic：start() 会把整句 "I want to research ..." 当作 doc.topic
    doc.topic = topic
    save_json(doc.to_dict(), "phase0_requirement_doc.json")

    # ── Phase 1: structure ────────────────────────────────────────────────
    structurer = RequirementStructurer(llm_call_fn=llm_call)
    structured = structurer.structure(doc)
    save_json(structured.to_dict(), "phase1_structured_requirement.json")

    # ── Phase 2: discussion group ─────────────────────────────────────────
    group = DiscussionGroup(llm_call_fn=llm_call)
    discussion = group.discuss(structured)
    save_json(discussion.to_dict(), "phase2_discussion_result.json")

    # ── Phase 3: config recommendation ────────────────────────────────────
    recommender = ConfigRecommender(llm_call_fn=llm_call)
    config = recommender.recommend(structured, discussion)
    config["topic_directions"] = getattr(structured, "department_hints", None) or []
    config_path = save_json(config, "phase3_recommended_config.json")

    # ── Emit a compact, machine-readable result ───────────────────────────
    result = {
        "status": "done",
        "topic": doc.topic,
        "domain": doc.domain,
        "domain_code": getattr(structured, "domain_code", None),
        "objectives": list(doc.objectives or []),
        "key_questions": list(doc.key_questions or []),
        "deliverable_type": doc.deliverable_type or "",
        "department_hints": list(getattr(structured, "department_hints", None) or []),
        "departments": list((config.get("departments") or {}).keys()),
        "department_count": len(config.get("departments") or {}),
        "config_path": config_path,
        "note": "完整配置已保存到 phase3_recommended_config.json",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
