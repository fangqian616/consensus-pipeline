#!/usr/bin/env python3
"""
Consensus Pipeline MCP Server — Zero-dependency Edition
========================================================
Pure Python MCP JSON-RPC 2.0 over stdio.
No pip packages required (no `pip install mcp`).

Exposes consensus pipeline phases as MCP tools for:
  - DeepSeek Harness
  - Claude Code / Codex
  - Any MCP-compatible AI agent

Usage:
    python mcp_server.py

Pipeline mapping:
  - run_search / run_search_review / run_summary → v1 pipeline (run_pipeline.py)
  - run_verify → v2 pipeline with stance quantification (run_pipeline_v2.py)
  - run_full_pipeline → v2 full pipeline (run_pipeline_v2.py)

Configuration (Harness setup prompt — see harness-integration/setup-prompt.md):
    The Harness Agent reads the setup prompt and configures MCP automatically.

For manual MCP clients that read mcp.json:
    {
        "mcpServers": {
            "consensus-pipeline": {
                "command": "python",
                "args": ["C:/path/to/mcp_server.py"]
            }
        }
    }
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from typing import Any

# ── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ══════════════════════════════════════════════════════════════════════════
#  MCP JSON-RPC 2.0 Protocol (zero-dependency)
# ══════════════════════════════════════════════════════════════════════════

SERVER_INFO = {
    "name": "consensus-pipeline",
    "version": "2.1.0",
}

PROTOCOL_VERSION = "2024-11-05"


def _make_result(req_id: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}, ensure_ascii=False)


def _make_error(req_id: Any, code: int, message: str, data: Any = None) -> str:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": err}, ensure_ascii=False)


# ── Tool registry ────────────────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = []


def _register_tool(name: str, description: str, input_schema: dict, handler):
    TOOLS.append({
        "name": name,
        "description": description,
        "inputSchema": input_schema,
        "_handler": handler,
    })


# ── Protocol dispatcher ──────────────────────────────────────────────────

async def handle_request(msg: dict) -> str | None:
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {}) or {}

    if method == "initialize":
        return _make_result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        tool_defs = [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in TOOLS
        ]
        return _make_result(req_id, {"tools": tool_defs})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {}) or {}
        tool = next((t for t in TOOLS if t["name"] == tool_name), None)
        if tool is None:
            return _make_result(req_id, {
                "content": [{"type": "text", "text": json.dumps({
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": [t["name"] for t in TOOLS],
                }, ensure_ascii=False, indent=2)}],
                "isError": True,
            })
        try:
            result_text = await tool["_handler"](arguments)
            return _make_result(req_id, {"content": [{"type": "text", "text": result_text}]})
        except Exception as e:
            return _make_result(req_id, {
                "content": [{"type": "text", "text": json.dumps({
                    "status": "error", "error": str(e),
                    "traceback": traceback.format_exc(),
                }, ensure_ascii=False)}],
                "isError": True,
            })

    if method == "ping":
        return _make_result(req_id, {})

    if req_id is not None:
        return _make_error(req_id, -32601, f"Method not found: {method}")
    return None


# ══════════════════════════════════════════════════════════════════════════
#  Pipeline Subprocess Helpers
# ══════════════════════════════════════════════════════════════════════════

async def _subprocess_run(cmd: list[str], timeout: int = 1800) -> dict:
    """Run a subprocess command and return structured result."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=PROJECT_ROOT,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return {
            "status": "error",
            "error": f"Timeout after {timeout}s",
            "command": " ".join(cmd),
        }

    return {
        "status": "success" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout_tail": stdout.decode("utf-8", errors="replace")[-6000:],
        "stderr_tail": stderr.decode("utf-8", errors="replace")[-3000:],
        "command": " ".join(cmd),
    }


async def _run_v1_pipeline(topic: str, lang: str = "zh", timeout: int = 1800) -> str:
    """Run v1 pipeline (Phases 0–7: requirement → search → debate → summary)."""
    cmd = [sys.executable, "run_pipeline.py", "--topic", topic, "--lang", lang]
    r = await _subprocess_run(cmd, timeout=timeout)
    r["pipeline_version"] = "v1"
    r["phases"] = "0 → 0.5 → 1 → 2 → 3 → 3.5 → 4 → 5 → 6 → 7"
    return json.dumps(r, ensure_ascii=False, indent=2)


async def _run_v2_pipeline(topic: str, lang: str = "zh",
                           shadow: bool = True, max_rounds: int = 8,
                           timeout: int = 3600) -> str:
    """Run v2 pipeline (v1 + stance quantification + dynamic termination)."""
    cmd = [
        sys.executable, "run_pipeline_v2.py",
        "--topic", topic, "--lang", lang,
        "--max-rounds", str(max_rounds),
    ]
    if shadow:
        cmd.append("--shadow")
    r = await _subprocess_run(cmd, timeout=timeout)
    r["pipeline_version"] = "v2"
    r["phases"] = "0 → 0.5 → 1 → 2 → 3 → 3.5 → 4 → 5(v2) → 6 → 7"
    r["v2_features"] = "StanceTracker + CV quantification + shadow/true termination"
    return json.dumps(r, ensure_ascii=False, indent=2)


async def _run_v2_department(topic: str, dept_key: str, lang: str = "zh",
                             max_rounds: int = 3, timeout: int = 1800) -> str:
    """Run a single department's v2 debate (isolation/resume, skips Phase 0-4.5+QC)."""
    # 找到已有输出目录(按 topic tag 匹配, 不依赖日期, 跨天 resume 也能命中)
    topic_tag = topic[:20].replace(" ", "_").replace("/", "_")
    v2_root = os.path.join(PROJECT_ROOT, "v2_run_output")
    output_dir = None
    if os.path.isdir(v2_root):
        candidates = [
            d for d in os.listdir(v2_root)
            if os.path.isdir(os.path.join(v2_root, d)) and d.endswith(topic_tag)
        ]
        if candidates:
            candidates.sort(
                key=lambda d: os.path.getmtime(os.path.join(v2_root, d)),
                reverse=True,
            )
            output_dir = os.path.join(v2_root, candidates[0])

    cmd = [
        sys.executable, "run_pipeline_v2.py",
        "--topic", topic, "--lang", lang,
        "--resume", "--only-dept", dept_key,
        "--max-rounds", str(max_rounds),
    ]
    if output_dir:
        cmd += ["--output-dir", output_dir]
    r = await _subprocess_run(cmd, timeout=timeout)
    r["pipeline_version"] = "v2"
    r["mode"] = f"single_dept:{dept_key}"
    if output_dir:
        r["output_dir"] = output_dir
    return json.dumps(r, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════
#  Tool Implementations
# ══════════════════════════════════════════════════════════════════════════

# ── Tool: run_search ─────────────────────────────────────────────────────

async def _handle_run_search(params: dict) -> str:
    topic = params.get("topic", "")
    lang = params.get("lang", "zh")
    if not topic:
        return json.dumps({"status": "error", "error": "topic is required"}, ensure_ascii=False)
    return await _run_v1_pipeline(topic, lang)

_register_tool(
    name="run_search",
    description=(
        "Run the v1 pipeline starting from paper search. Executes the full v1 pipeline "
        "(Phases 0-7: requirement analysis → literature search → department debate → "
        "cross-debate → summary report). Output files are written to run_output/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic (Chinese or English)"},
            "lang": {"type": "string", "description": "Output language: zh (default) or en", "default": "zh"},
        },
        "required": ["topic"],
    },
    handler=_handle_run_search,
)


# ── Tool: run_search_review ──────────────────────────────────────────────

async def _handle_run_search_review(params: dict) -> str:
    topic = params.get("topic", "")
    lang = params.get("lang", "zh")
    if not topic:
        return json.dumps({"status": "error", "error": "topic is required"}, ensure_ascii=False)
    return await _run_v1_pipeline(topic, lang)

_register_tool(
    name="run_search_review",
    description=(
        "Run the v1 pipeline with focus on search quality review. Includes "
        "Phase 3.5 QC quality gate (hard_filter → llm_classify → tag_layer + supplemental search). "
        "Executes full v1 pipeline (Phases 0-7)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic"},
            "lang": {"type": "string", "description": "Output language: zh or en", "default": "zh"},
        },
        "required": ["topic"],
    },
    handler=_handle_run_search_review,
)


# ── Tool: run_summary ────────────────────────────────────────────────────

async def _handle_run_summary(params: dict) -> str:
    topic = params.get("topic", "")
    lang = params.get("lang", "zh")
    if not topic:
        return json.dumps({"status": "error", "error": "topic is required"}, ensure_ascii=False)
    return await _run_v1_pipeline(topic, lang)

_register_tool(
    name="run_summary",
    description=(
        "Run the v1 pipeline to generate consensus summary. Produces a final "
        "report (Phase 7) with citation constraints and confidence annotations. "
        "Executes full v1 pipeline (Phases 0-7)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic"},
            "lang": {"type": "string", "description": "Output language: zh or en", "default": "zh"},
        },
        "required": ["topic"],
    },
    handler=_handle_run_summary,
)


# ── Tool: run_verify ─────────────────────────────────────────────────────

async def _handle_run_verify(params: dict) -> str:
    topic = params.get("topic", "")
    lang = params.get("lang", "zh")
    max_rounds = int(params.get("max_rounds", 8))
    if not topic:
        return json.dumps({"status": "error", "error": "topic is required"}, ensure_ascii=False)
    return await _run_v2_pipeline(topic, lang, shadow=True, max_rounds=max_rounds)

_register_tool(
    name="run_verify",
    description=(
        "Run the v2 pipeline with enhanced verification via stance quantification. "
        "Uses StanceTracker + CV metrics to verify debate convergence. "
        "Supports shadow mode and configurable max rounds. "
        "Executes full v2 pipeline with enhanced Phase 5."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic"},
            "lang": {"type": "string", "description": "Output language: zh or en", "default": "zh"},
            "max_rounds": {"type": "integer", "description": "Max debate rounds per department (default 8)", "default": 8},
        },
        "required": ["topic"],
    },
    handler=_handle_run_verify,
)


# ── Tool: run_full_pipeline ──────────────────────────────────────────────

async def _handle_run_full_pipeline(params: dict) -> str:
    topic = params.get("topic", "")
    lang = params.get("lang", "zh")
    use_v2 = bool(params.get("use_v2", True))
    max_rounds = int(params.get("max_rounds", 8))
    if not topic:
        return json.dumps({"status": "error", "error": "topic is required"}, ensure_ascii=False)

    if use_v2:
        return await _run_v2_pipeline(topic, lang, shadow=True, max_rounds=max_rounds, timeout=3600)
    else:
        return await _run_v1_pipeline(topic, lang, timeout=1800)

_register_tool(
    name="run_full_pipeline",
    description=(
        "Run the complete pipeline end-to-end. Default uses v2 (stance quantification "
        "+ dynamic termination). Set use_v2=false for v1 (simpler, faster)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic"},
            "lang": {"type": "string", "description": "Output language: zh or en", "default": "zh"},
            "use_v2": {"type": "boolean", "description": "Use v2 pipeline (default true)", "default": True},
            "max_rounds": {"type": "integer", "description": "Max debate rounds (v2 only, default 8)", "default": 8},
        },
        "required": ["topic"],
    },
    handler=_handle_run_full_pipeline,
)


# ── Tool: run_debate_department ───────────────────────────────────────────

async def _handle_run_debate_department(params: dict) -> str:
    topic = params.get("topic", "")
    dept_key = params.get("dept_key", "")
    lang = params.get("lang", "zh")
    max_rounds = int(params.get("max_rounds", 3))
    if not topic or not dept_key:
        return json.dumps({"status": "error", "error": "topic and dept_key are required"}, ensure_ascii=False)
    return await _run_v2_department(topic, dept_key, lang, max_rounds)

_register_tool(
    name="run_debate_department",
    description=(
        "Run a single department's v2 debate in isolation/resume mode. Skips "
        "Phase 0-4.5+QC by loading intermediate artifacts from disk (requires a "
        "prior run that produced phase3_recommended_config.json + phase3.5_qc_papers.json). "
        "Useful for incremental runs and testing a single department's stance scoring."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research topic"},
            "dept_key": {"type": "string", "description": "Department key, e.g. literature_search / methodology_review / counter_evidence"},
            "lang": {"type": "string", "description": "Output language: zh or en", "default": "zh"},
            "max_rounds": {"type": "integer", "description": "Max debate rounds (default 3)", "default": 3},
        },
        "required": ["topic", "dept_key"],
    },
    handler=_handle_run_debate_department,
)


# ── Tool: get_pipeline_status ────────────────────────────────────────────

async def _handle_get_pipeline_status(params: dict) -> str:
    status: dict[str, Any] = {
        "project_root": PROJECT_ROOT,
        "output_files": [],
        "api_key_configured": False,
    }

    for dirname in ["run_output", "v2_run_output"]:
        output_dir = os.path.join(PROJECT_ROOT, dirname)
        if os.path.isdir(output_dir):
            for f in os.listdir(output_dir):
                fpath = os.path.join(output_dir, f)
                if os.path.isfile(fpath):
                    status["output_files"].append({
                        "dir": dirname,
                        "name": f,
                        "size_bytes": os.path.getsize(fpath),
                        "modified": os.path.getmtime(fpath),
                    })

    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    key_val = line.split("=", 1)[1].strip().strip("\"'")
                    status["api_key_configured"] = bool(key_val)
                    if len(key_val) >= 4:
                        status["api_key_suffix"] = "****" + key_val[-4:]
                    break

    status["v1_pipeline_exists"] = os.path.isfile(os.path.join(PROJECT_ROOT, "run_pipeline.py"))
    status["v2_pipeline_exists"] = os.path.isfile(os.path.join(PROJECT_ROOT, "run_pipeline_v2.py"))

    # 断点续跑状态: 扫描 v2_run_output/*/v2_run_state.json
    status["runs"] = []
    v2_root = os.path.join(PROJECT_ROOT, "v2_run_output")
    if os.path.isdir(v2_root):
        for run_name in sorted(os.listdir(v2_root)):
            run_dir = os.path.join(v2_root, run_name)
            if not os.path.isdir(run_dir):
                continue
            state_path = os.path.join(run_dir, "v2_run_state.json")
            if not os.path.isfile(state_path):
                continue
            try:
                with open(state_path, "r", encoding="utf-8") as fh:
                    state = json.load(fh)
                status["runs"].append({
                    "run": run_name,
                    "phases_completed": state.get("phases_completed", []),
                    "phase5_depts_completed": state.get("phase5_depts_completed", []),
                    "current_phase": state.get("current_phase"),
                    "current_dept": state.get("current_dept"),
                })
            except (json.JSONDecodeError, OSError):
                continue

    return json.dumps(status, ensure_ascii=False, indent=2)

_register_tool(
    name="get_pipeline_status",
    description="Check pipeline status: output files, API key configuration, script availability.",
    input_schema={"type": "object", "properties": {}},
    handler=_handle_get_pipeline_status,
)


# ── Tool: get_phase_description ──────────────────────────────────────────

_PHASE_DESCRIPTIONS = {
    "search": {
        "name": "Phase 4 — Literature Search",
        "description": "Search academic databases for papers matching the research topic. Includes supplemental search via QC Phase 3.5.",
        "input": "Research topic text",
        "output": "Paper metadata → run_output/",
        "pipeline": "v1 and v2",
    },
    "search_review": {
        "name": "Phase 3.5 — QC Quality Gate",
        "description": "Hard-filter → LLM-classify → tag-layer + supplemental search if coverage insufficient.",
        "input": "Search results from Phase 4",
        "output": "Filtered paper list + QC report",
        "pipeline": "v1 and v2",
    },
    "summary": {
        "name": "Phase 7 — Consensus Summary Report",
        "description": "Generate final summary with citation hard constraints and confidence annotations.",
        "input": "Cross-debate results from Phase 6",
        "output": "Summary report (Markdown + optional DOCX)",
        "pipeline": "v1 and v2",
    },
    "verify": {
        "name": "Phase 5 (v2) — Stance Quantification & Termination",
        "description": "StanceTracker vectorizes debate positions, computes CV to detect convergence. Shadow mode + configurable max rounds.",
        "input": "Department debate transcripts",
        "output": "Stance vectors + CV metrics + termination decision",
        "pipeline": "v2 only",
    },
    "full_v1": {
        "name": "Full v1 Pipeline",
        "description": "Phases 0→0.5→1→2→3→3.5→4→5→6→7",
        "input": "Research topic",
        "output": "Full report + intermediate artifacts",
        "pipeline": "v1",
        "typical_duration": "10-20 minutes",
    },
    "full_v2": {
        "name": "Full v2 Pipeline",
        "description": "v1 + StanceTracker + CV convergence detection + configurable termination",
        "input": "Research topic",
        "output": "Full report + stance metrics + convergence analysis",
        "pipeline": "v2",
        "typical_duration": "15-30 minutes",
    },
}


async def _handle_get_phase_description(params: dict) -> str:
    phase_name = params.get("phase_name", "")
    desc = _PHASE_DESCRIPTIONS.get(phase_name)
    if desc:
        return json.dumps(desc, ensure_ascii=False, indent=2)
    return json.dumps({
        "error": f"Unknown phase: {phase_name}",
        "available_phases": list(_PHASE_DESCRIPTIONS.keys()),
    }, ensure_ascii=False)

_register_tool(
    name="get_phase_description",
    description="Get detailed description of a pipeline phase.",
    input_schema={
        "type": "object",
        "properties": {
            "phase_name": {
                "type": "string",
                "description": "Phase: search / search_review / summary / verify / full_v1 / full_v2",
            },
        },
        "required": ["phase_name"],
    },
    handler=_handle_get_phase_description,
)


# ══════════════════════════════════════════════════════════════════════════
#  Main I/O Loop
# ══════════════════════════════════════════════════════════════════════════

async def main():
    if sys.platform == "win32":
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    loop = asyncio.get_event_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                sys.stdout.write(_make_error(None, -32700, f"Parse error: {e}") + "\n")
                sys.stdout.flush()
                continue
            response = await handle_request(msg)
            if response is not None:
                sys.stdout.write(response + "\n")
                sys.stdout.flush()
        except Exception:
            traceback.print_exc(file=sys.stderr)
            continue


if __name__ == "__main__":
    print(
        f"[consensus-pipeline-mcp] v{SERVER_INFO['version']} starting — {len(TOOLS)} tools registered",
        file=sys.stderr,
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[consensus-pipeline-mcp] shutting down", file=sys.stderr)
