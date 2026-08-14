#!/usr/bin/env python3
"""
共识管线 v2 分歧量化原型 — 影子模式采集器
==========================================

【测试版本】v2.2 — 校准阈值 + 解析失败率门
-------------------------------------------------
测试预期：
  • 收敛判定：CV < 0.07 判收敛（ε1=0.07，v1校准方案B）
  • 僵局判定：|ΔCV| < 0.01 视为走平（ε2=0.01）
  • 复合僵局：(flat+up)/总论点 ≥ 0.75 且 CV ≥ ε1 → 高位僵持
  • 解析失败率门：最新轮失败率 ≥ 20% 时跳过一切判定，防止 CV 假低信号
  • 校准依据：10场实验（3真收敛+4真僵局+3假收敛），9/10正确率

状态：待主人在 qian 本机集成
配套文档：v2原型实现spec_20260804.md
依赖：仅 Python 标准库（json / re / ast / statistics / datetime / pathlib / logging）

用法：
  1. 将此文件放到与 debate_engine.py 同目录
  2. 在 debate_engine.py 中 import 需要的函数（见 spec §12 适配点索引）
  3. 辩论运行时自动写 debate_stance_log.jsonl（与原 debate_log 并存，不改原日志）

函数速查：
  extract_arguments()      → §3 R1后抽取核心论点清单（需传入LLM调用函数）
  render_stance_block()    → §4 渲染表态块prompt文本（R2起追加到辩手prompt末尾）
  parse_stance()           → §5 解析单个辩手一轮的表态块（容错，永不抛异常）
  argument_cv()            → §6 单论点CV
  round_cv()               → §6 轮级CV聚合
  check_termination()      → §8 终止判定（影子模式）v2.2：轨道1收敛 / 轨道2a连续平台 /
                             轨道2b高位僵持（复合僵局）+ 解析失败率门
  write_stance_log()       → §7 写JSONL日志
  StanceTracker            → 便捷封装：串联以上全部，维护状态

作者：小夏 | 2026-08-07 | v2.1 修订 2026-08-09 | v2.2 校准+失败率门 2026-08-12
"""

import json
import re
import ast
import logging
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev, mean
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 默认参数（待校准）
# ─────────────────────────────────────────────
EPS1 = 0.07        # 收敛阈值：CV < ε1 判收敛（v1校准 08-11，方案B，9/10正确）
EPS2 = 0.01        # 僵局阈值：|ΔCV| < ε2 视为走平（v1校准 08-11）
N_PLATEAU = 2      # 连续 N 轮满足即判僵局（3轮制下N=2是上限）
# v2.1（2026-08-09→08-11 校准）：复合僵局阈值。最近间隔 (flat+up)/总论点 ≥ 0.75 且 CV > ε1
# → 判「高位僵持」。依据 08-08 实验C实证：高位震荡型僵局会被一次显著下降打破
# 连续性后反升，连续平台轨道（轨道2a）对其不敏感；flat计数 A/B/C = 1/3/5 单调可辨。
# ✅ v1校准完成 08-11：从占位 0.6 上调至 0.75（方案B，ε1=0.07/ε2=0.01/flat_th=0.75）
FLAT_UP_RATIO_TH = 0.75
MAX_PARSE_FAIL_RATE = 0.20  # 解析失败率门：最新轮失败率 ≥ 此值时，CV 信号不可信，跳过一切判定（b1_6 教训）

# ─────────────────────────────────────────────
# §3 核心论点清单抽取
# ─────────────────────────────────────────────

ARGUMENT_EXTRACT_PROMPT = """\
【核心论点抽取】
基于以下第 1 轮全部辩手发言，抽取本场辩论的 3-7 条核心论点。

要求：
1. 每条论点是一句可判断对错的命题（陈述句），不要问题、不要泛泛主题。
2. 论点之间尽量不重叠；合并同义表述。
3. 既覆盖主要分歧点，也保留 1-2 条明显共识点（共识点在后续量化中充当对照组）。
4. 用稳定 ID 编号：P1, P2, P3……一旦确定，后续轮次沿用不变。

输出格式（严格输出一个 JSON 代码块，不要任何其他内容）：
```json
{{
  "arguments": [
    {{"id": "P1", "text": "……"}},
    {{"id": "P2", "text": "……"}}
  ]
}}
```

第 1 轮发言全文：
{round1_transcript}
"""

ARGUMENT_EXTRACT_PROMPT_LENIENT = """You are extracting core debate arguments from a transcript.

Transcript:
{round1_transcript}

Please identify the main distinct arguments (up to 5). For each argument provide:
- "id": label like P1, P2, P3 etc.
- "text": one-sentence summary of the argument

Return ONLY valid JSON:
{{"arguments": [{{"id": "P1", "text": "..."}}, {{"id": "P2", "text": "..."}}]}}

If no clear arguments are found, return: {{"arguments": []}}
Do NOT include any explanation outside the JSON.
"""




def _try_parse_arguments(raw: str) -> list:
    """Multi-strategy fallback parser for argument extraction."""
    import json as _json

    # Strategy 1: use extract_json_block from same module
    try:
        data = extract_json_block(raw, '"arguments"')
        if isinstance(data, dict) and isinstance(data.get("arguments"), list):
            cleaned = []
            for item in data["arguments"]:
                if isinstance(item, dict) and "id" in item and "text" in item:
                    cleaned.append({"id": str(item["id"]), "text": str(item["text"])})
            if cleaned:
                return cleaned
    except Exception:
        pass

    # Strategy 2: find any JSON object in the raw text
    try:
        for m in re.finditer(r'\{[^{}]{20,}?"arguments"\s*:\s*\[.*?\].*?\}', raw, re.DOTALL):
            try:
                data = _json.loads(m.group())
                if isinstance(data, dict) and isinstance(data.get("arguments"), list):
                    cleaned = []
                    for item in data["arguments"]:
                        if isinstance(item, dict) and "id" in item and "text" in item:
                            cleaned.append({"id": str(item["id"]), "text": str(item["text"])})
                    if cleaned:
                        return cleaned
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 3: P1/P2/P3 regex fallback
    try:
        pattern = r'(?:P1|P2|P3)\s*[:\.)]\s*(.+?)(?=\n(?:P1|P2|P3)\s*[:\.)]|$)'
        matches = re.findall(pattern, raw, re.DOTALL)
        if matches:
            cleaned = []
            for i, m in enumerate(matches[:10], 1):
                text = m.strip()
                if text and len(text) > 5:
                    cleaned.append({"id": f"P{i}", "text": text})
            if cleaned:
                return cleaned
    except Exception:
        pass

    return []


def extract_arguments(
    round1_transcript: str,
    llm_call_fn,
    run_id: str = "",
    topic: str = "",
    log_path: Optional[Path] = None,
) -> list[dict]:
    """
    R1后抽取核心论点清单。

    参数：
      round1_transcript: R1全部辩手发言拼接文本
      llm_call_fn: LLM调用函数，签名 fn(prompt: str) -> str（返回纯文本）
      run_id: 实验运行ID（写入日志）
      topic: 辩题文本（写入日志）
      log_path: JSONL日志路径，None则不写日志

    返回：
      [{"id": "P1", "text": "..."}, ...] 或 空列表（抽取失败时）
    """
    # === Attempt 1: standard prompt with multi-strategy parsing ===
    prompt = ARGUMENT_EXTRACT_PROMPT.format(round1_transcript=round1_transcript)
    result = {"ok": False, "arguments": [], "error": None}

    try:
        raw = llm_call_fn(prompt)
        data = extract_json_block(raw, '"arguments"')
        if isinstance(data, dict) and isinstance(data.get("arguments"), list):
            args = data["arguments"]
            cleaned = []
            for item in args:
                if isinstance(item, dict) and "id" in item and "text" in item:
                    cleaned.append({"id": str(item["id"]), "text": str(item["text"])})
            if cleaned:
                result["ok"] = True
                result["arguments"] = cleaned
            else:
                result["error"] = "no_valid_arguments_in_response"
        else:
            fallback = _try_parse_arguments(raw)
            if fallback:
                result["ok"] = True
                result["arguments"] = fallback
            else:
                result["error"] = "no_valid_arguments_block"
    except Exception as e:
        result["error"] = f"exception: {e}"

    # === Attempt 2: lenient prompt retry if Attempt 1 failed ===
    if not result["ok"]:
        try:
            lenient_prompt_text = ARGUMENT_EXTRACT_PROMPT_LENIENT.format(round1_transcript=round1_transcript)
            raw2 = llm_call_fn(lenient_prompt_text)
            fallback2 = _try_parse_arguments(raw2)
            if fallback2:
                result["ok"] = True
                result["arguments"] = fallback2
                result["error"] = None
        except Exception:
            pass  # Keep original error from Attempt 1




# ─────────────────────────────────────────────
# §4 表态块 prompt 渲染
# ─────────────────────────────────────────────

STANCE_BLOCK_TEMPLATE = """\
【结构化表态要求】
在本轮发言正文结束之后，你必须另起一段，输出一个 JSON 代码块，表达你当前对各核心论点的独立态度。

核心论点清单：
{argument_list_rendered}

评分标尺（Likert 1-5 级，整数）：
1 = 强烈反对（有明确证据反驳）
2 = 反对（倾向不同意，但证据不够充分）
3 = 中立 / 证据不足，无法判断
4 = 支持（倾向同意）
5 = 强烈支持（有明确证据支撑）

输出格式（严格遵守）：
```json
{{
  "stance": {{
{stance_example_lines}
  }}
}}
```

规则：
1. 必须对清单中的每一个论点打分，不得遗漏，也不得新增论点 ID。
2. 分数必须是 1-5 的整数。
3. JSON 代码块放在本轮发言的最后；代码块之后不要再写任何内容。
4. 评分基于你听完本轮全部发言后的最新判断；允许与上轮不同——立场变化本身是重要信号，不要为显得"一致"而维持旧分。
"""


def render_stance_block(arguments: list[dict]) -> str:
    """
    渲染表态块prompt文本。R2起拼在每个辩手每轮prompt末尾。

    参数：
      arguments: [{"id": "P1", "text": "..."}, ...]

    返回：
      追加文本（str）
    """
    if not arguments:
        return ""

    # 渲染论点清单
    lines = []
    for arg in arguments:
        lines.append(f"{arg['id']}: {arg['text']}")
    argument_list_rendered = "\n".join(lines)

    # 渲染示例行
    example_lines = []
    for arg in arguments:
        example_lines.append(f'    "{arg["id"]}": 3,')
    # 去掉最后一个逗号（让它看起来更自然）
    if example_lines:
        example_lines[-1] = example_lines[-1].rstrip(",") + ","
    stance_example_lines = "\n".join(example_lines)

    return STANCE_BLOCK_TEMPLATE.format(
        argument_list_rendered=argument_list_rendered,
        stance_example_lines=stance_example_lines,
    )


# ─────────────────────────────────────────────
# §5 stance 解析（JSON 提取 + 容错）
# ─────────────────────────────────────────────

FENCED_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _balance_braces(text: str, start: int) -> Optional[str]:
    """从 start 处的 '{' 开始做括号配对，返回完整 JSON 子串；失败返回 None。"""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _loose_parse(s: str):
    """宽松解析：去尾逗号后用 ast.literal_eval（容忍单引号）。"""
    s2 = re.sub(r",\s*([}\]])", r"\1", s)
    return ast.literal_eval(s2)


def extract_json_block(raw_text: str, required_key: str = '"stance"') -> Optional[dict]:
    """
    通用 JSON 块提取：优先最后一个含 required_key 的 fenced block，
    退化到裸文本括号配对（同时容忍单/双引号 key）。返回 dict 或 None。
    """
    keys = [required_key, required_key.replace('"', "'")]
    candidate = None

    # 策略1：找最后一个包含 required_key 的 fenced block
    for blk in reversed(FENCED_RE.findall(raw_text)):
        if any(k in blk for k in keys):
            candidate = blk
            break

    # 策略2：裸文本括号配对
    if candidate is None:
        idx = max(raw_text.rfind(k) for k in keys)
        if idx != -1:
            start = raw_text.rfind('{', 0, idx)
            if start != -1:
                candidate = _balance_braces(raw_text, start)

    if candidate is None:
        return None

    # 尝试解析
    for parser in (json.loads, _loose_parse):
        try:
            return parser(candidate)
        except Exception:
            continue
    return None


def parse_stance(raw_text: str, expected_ids: list[str]) -> dict:
    """
    解析单个辩手一轮的表态块。返回结构化结果，永不抛异常。

    参数：
      raw_text: 辩手原始输出文本
      expected_ids: 预期的论点ID列表，如 ["P1", "P2", "P3"]

    返回：
      {
        "ok": bool,           # 至少解析到一个有效分数
        "stance": {arg_id: int_score, ...},
        "missing": [arg_id, ...],   # 缺失或无法解析的论点
        "fixes": [str, ...],        # 钳制/修正记录
        "error": str or None,       # 错误描述（仅当ok=False时有意义）
      }
    """
    res = {"ok": False, "stance": {}, "missing": [], "fixes": [], "error": None}

    data = extract_json_block(raw_text, '"stance"')
    if not isinstance(data, dict) or not isinstance(data.get("stance"), dict):
        res["error"] = "no_valid_stance_block"
        res["missing"] = list(expected_ids)
        return res

    raw_stance = data["stance"]

    for aid in expected_ids:
        v = raw_stance.get(aid)
        if v is None:
            res["missing"].append(aid)
            continue
        try:
            v = int(round(float(v)))  # 容忍 4.0 / "4"
        except (TypeError, ValueError):
            res["missing"].append(aid)  # 无法解析视为缺失
            continue
        if not 1 <= v <= 5:
            res["fixes"].append(f"{aid}:{v}->clamped")
            v = max(1, min(5, v))  # 越界钳制到 [1,5]
        res["stance"][aid] = v

    extra = set(raw_stance) - set(expected_ids)
    if extra:
        res["fixes"].append(f"extra_ids_ignored:{sorted(extra)}")

    res["ok"] = len(res["stance"]) > 0  # 部分成功也算成功
    return res


# ─────────────────────────────────────────────
# §6 CV 计算（σ/μ 变异系数）
# ─────────────────────────────────────────────


def argument_cv(scores: list) -> Optional[float]:
    """
    单论点：本轮全部辩手评分的变异系数 CV = σ/μ。
    有效样本 <2 或 μ=0 时返回 None。
    """
    vals = [s for s in scores if s is not None]
    if len(vals) < 2:
        return None
    mu = mean(vals)
    if mu == 0:
        return None
    return pstdev(vals) / mu  # 总体标准差：n=辩手数(通常2-4)，用pstdev


def round_cv(stance_by_debater: dict[str, dict[str, int]], arg_ids: list[str]) -> dict:
    """
    计算一轮的CV聚合。

    参数：
      stance_by_debater: {debater_id: {arg_id: score}}
      arg_ids: 论点ID列表

    返回：
      {
        "overall": float or None,     # 轮级CV = 各论点CV的简单均值
        "per_argument": {arg_id: float or None, ...}
      }
    """
    per_arg = {}
    for aid in arg_ids:
        scores = [s.get(aid) for s in stance_by_debater.values()]
        per_arg[aid] = argument_cv(scores)

    valid = [v for v in per_arg.values() if v is not None]
    return {
        "overall": mean(valid) if valid else None,
        "per_argument": per_arg,
    }


# ─────────────────────────────────────────────
# §7 JSONL 日志写入
# ─────────────────────────────────────────────


def write_stance_log(log_path: Path, event_data: dict):
    """
    追加写一行到 debate_stance_log.jsonl。

    参数：
      log_path: 日志文件路径
      event_data: 事件字典，必须包含 "event" 字段
    """
    # 自动补时间戳
    if "ts" not in event_data:
        event_data["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_data, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────
# §8 软性僵局检测：双轨终止条件
# ─────────────────────────────────────────────


def _interval_down_flat_up(prev: dict, cur: dict, eps2: float) -> tuple[int, int, int, int]:
    """
    逐论点相邻轮转移分类计数（v2.1）。
    ΔCV < -eps2 = down（收敛中）；|ΔCV| <= eps2 = flat（持平）；ΔCV > +eps2 = up（反升）。
    返回 (down, flat, up, total)。
    """
    down = flat = up = total = 0
    for aid, v_cur in cur.items():
        v_prev = prev.get(aid)
        if v_prev is None or v_cur is None:
            continue
        total += 1
        d = v_cur - v_prev
        if d > eps2:
            up += 1
        elif d < -eps2:
            down += 1
        else:
            flat += 1
    return down, flat, up, total


def check_termination(
    cv_history: list[Optional[float]],
    eps1: float = EPS1,
    eps2: float = EPS2,
    n: int = N_PLATEAU,
    per_arg_history: Optional[list[dict]] = None,
    flat_up_ratio_th: float = FLAT_UP_RATIO_TH,
    fail_rate: float = None,
) -> tuple[bool, Optional[str]]:
    """
    双轨终止判定 v2.1（2026-08-09 修订）。返回 (should_stop, reason)。

    轨道1  收敛：最新一轮 CV < ε1
    轨道2a 软性僵局（连续平台，旧规则保留）：最近 n 个 |ΔCV| 全部 < ε2
    轨道2b 软性僵局（高位僵持，v2.1 新增）：当前 CV > ε1 且最近间隔
           (flat+up)/总论点 ≥ flat_up_ratio_th —— 多数论点无收敛动作且总体
           分歧仍高位。解决 08-08 实验C 暴露的问题：高位震荡型僵局会被一次
           显著下降打破连续性后反升，连续平台轨道对其不敏感。

    参数：
      cv_history: 各轮CV列表（从R2开始，长度=rounds-1）
      eps1: 收敛阈值
      eps2: 显著性带宽（|ΔCV| 小于此值视为走平）
      n: 连续轮次数（轨道2a）
      per_arg_history: 每轮 cv_per_argument 字典列表（轨道2b 需要；缺省则跳过2b）
      flat_up_ratio_th: 轨道2b 占比阈值（已校准 0.75，v1 08-11）
      fail_rate: 最新轮解析失败率（0~1）。≥ MAX_PARSE_FAIL_RATE 时 CV 信号不可信，
                 跳过一切判定返回 (False, "blocked_by_parse_fail_gate")

    返回：
      (should_stop: bool, reason: str or None)
    """
    hist = [c for c in cv_history if c is not None]
    if not hist:
        return False, None

    # 解析失败率门：最新轮失败率过高时 CV 信号不可信，一律不判（b1_6 教训）
    if fail_rate is not None and fail_rate >= MAX_PARSE_FAIL_RATE:
        return False, f"blocked_by_parse_fail_gate: fail_rate={fail_rate:.2%} >= {MAX_PARSE_FAIL_RATE:.0%}"

    # 轨道1：收敛
    if hist[-1] < eps1:
        return True, f"converged: CV={hist[-1]:.4f} < eps1={eps1}"

    # 轨道2b：高位僵持（复合僵局，优先于 2a —— 实验C 实证其覆盖 2a 抓不到的形态）
    if per_arg_history is not None and len(per_arg_history) >= 2 and hist[-1] > eps1:
        prev, cur = per_arg_history[-2], per_arg_history[-1]
        down, flat, up, total = _interval_down_flat_up(prev, cur, eps2)
        if total and (flat + up) / total >= flat_up_ratio_th:
            ratio = (flat + up) / total
            return True, (f"composite_deadlock: CV={hist[-1]:.4f} > eps1={eps1} "
                          f"and (flat+up)/total={flat + up}/{total}={ratio:.2f} "
                          f">= {flat_up_ratio_th}")

    # 轨道2a：软性僵局（连续平台）
    if len(hist) >= n + 1:
        deltas = [abs(hist[i] - hist[i - 1]) for i in range(len(hist) - n, len(hist))]
        if all(d < eps2 for d in deltas):
            return True, f"soft_deadlock: |dCV| < eps2={eps2} for {n} consecutive rounds"

    return False, None


# ─────────────────────────────────────────────
# 便捷封装：StanceTracker
# ─────────────────────────────────────────────


class StanceTracker:
    """
    串联全部v2逻辑的状态管理器。

    用法：
      tracker = StanceTracker(run_id="v2proto_20260807_A", topic="...", log_dir="./")

      # R1后：抽取论点
      args = tracker.extract_arguments(round1_transcript, llm_call_fn)

      # R2起每轮：
      prompt_suffix = tracker.get_stance_block()  # 追加到辩手prompt
      # ... 收集各辩手输出后 ...
      for debater_id, raw_output in debater_outputs.items():
          tracker.record_debater_stance(debater_id, raw_output)
      cv_result = tracker.finish_round(round_num)
      # cv_result 包含 cv_overall, termination_shadow 等
    """

    def __init__(self, run_id: str, topic: str, log_dir: str | Path = "."):
        self.run_id = run_id
        self.topic = topic
        self.log_path = Path(log_dir) / "debate_stance_log.jsonl"
        self.arguments: list[dict] = []
        self.arg_ids: list[str] = []
        self.cv_history: list[Optional[float]] = []
        self.per_arg_history: list[dict] = []  # v2.1：每轮 cv_per_argument，供轨道2b
        self.round_fail_rates: list[float] = []  # 每轮解析失败率（供失败率门）
        self.current_round_stances: dict[str, dict[str, int]] = {}
        self.round_results: list[dict] = []

    def extract_arguments(self, round1_transcript: str, llm_call_fn) -> list[dict]:
        """R1后抽取论点清单。"""
        self.arguments = extract_arguments(
            round1_transcript=round1_transcript,
            llm_call_fn=llm_call_fn,
            run_id=self.run_id,
            topic=self.topic,
            log_path=self.log_path,
        )
        self.arg_ids = [a["id"] for a in self.arguments]
        return self.arguments

    def get_stance_block(self) -> str:
        """获取表态块prompt文本（R2起用）。"""
        return render_stance_block(self.arguments)

    def record_debater_stance(self, debater_id: str, raw_output: str,
                               prompt_tokens: int = 0, completion_tokens: int = 0):
        """记录单个辩手一轮的表态解析结果。"""
        if not self.arg_ids:
            return  # 论点清单未就绪

        parsed = parse_stance(raw_output, self.arg_ids)
        self.current_round_stances[debater_id] = parsed["stance"]

        # 写轮次stance日志
        write_stance_log(self.log_path, {
            "event": "round_stance",
            "run_id": self.run_id,
            "debater": debater_id,
            "stance": parsed["stance"],
            "parse_ok": parsed["ok"],
            "missing": parsed["missing"],
            "fixes": parsed["fixes"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        })

    def finish_round(self, round_num: int, fail_rate: float = None) -> dict:
        """
        一轮收齐后调用：计算CV + 影子判定 + 写日志。
        返回该轮的CV结果和终止判定。
        """
        if not self.arg_ids or not self.current_round_stances:
            return {"overall": None, "per_argument": {}, "termination": (False, None)}

        cv_result = round_cv(self.current_round_stances, self.arg_ids)
        self.cv_history.append(cv_result["overall"])
        self.per_arg_history.append(cv_result["per_argument"])
        if fail_rate is not None:
            self.round_fail_rates.append(fail_rate)

        # 影子判定（v2.1：传入 per_arg_history 启用轨道2b 高位僵持；传入 fail_rate 启用失败率门）
        latest_fail_rate = self.round_fail_rates[-1] if self.round_fail_rates else None
        should_stop, reason = check_termination(
            self.cv_history, per_arg_history=self.per_arg_history,
            fail_rate=latest_fail_rate)

        # 写轮次CV日志
        write_stance_log(self.log_path, {
            "event": "round_cv",
            "run_id": self.run_id,
            "round": round_num,
            "cv_overall": cv_result["overall"],
            "cv_per_argument": cv_result["per_argument"],
            "termination_shadow": {
                "should_stop": should_stop,
                "reason": reason,
            },
        })

        result = {
            "round": round_num,
            "overall": cv_result["overall"],
            "per_argument": cv_result["per_argument"],
            "cv_history": list(self.cv_history),
            "termination": (should_stop, reason),
        }
        self.round_results.append(result)

        # 清空当前轮状态
        self.current_round_stances = {}

        return result

    def get_summary(self) -> str:
        """生成ASCII格式的CV曲线摘要（实验后快速查看）。"""
        lines = [f"=== StanceTracker Summary: {self.run_id} ==="]
        lines.append(f"Topic: {self.topic}")
        lines.append(f"Arguments: {len(self.arguments)} ({', '.join(self.arg_ids)})")
        lines.append(f"CV history: {[f'{c:.4f}' if c else 'None' for c in self.cv_history]}")

        if self.cv_history:
            valid = [c for c in self.cv_history if c is not None]
            if valid:
                lines.append(f"  min={min(valid):.4f}  max={max(valid):.4f}  last={valid[-1]:.4f}")

                # 趋势判断
                if len(valid) >= 2:
                    trend = valid[-1] - valid[0]
                    lines.append(f"  trend={trend:+.4f} ({'↓收敛' if trend < -0.05 else '↑发散' if trend > 0.05 else '→走平'})")

        # 最终判定（v2.1：传入 per_arg_history + fail_rate）
        latest_fail_rate = self.round_fail_rates[-1] if self.round_fail_rates else None
        should_stop, reason = check_termination(
            self.cv_history, per_arg_history=self.per_arg_history,
            fail_rate=latest_fail_rate)
        lines.append(f"Shadow verdict: {'STOP' if should_stop else 'CONTINUE'} — {reason or 'no trigger'}")

        return "\n".join(lines)


# ─────────────────────────────────────────────
# 自测（python stance_quant_v2.py 可直接运行）
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== stance_quant_v2.py 自测 ===\n")

    # 测试 parse_stance
    mock_output = """
这是一段辩论发言正文...

```json
{
  "stance": {
    "P1": 4,
    "P2": 2,
    "P3": 5
  }
}
```
"""
    result = parse_stance(mock_output, ["P1", "P2", "P3"])
    print(f"parse_stance test: ok={result['ok']}, stance={result['stance']}")
    assert result["ok"] is True
    assert result["stance"] == {"P1": 4, "P2": 2, "P3": 5}

    # 测试缺失字段
    mock_partial = """
```json
{"stance": {"P1": 3}}
```
"""
    result2 = parse_stance(mock_partial, ["P1", "P2", "P3"])
    print(f"parse_stance partial: ok={result2['ok']}, stance={result2['stance']}, missing={result2['missing']}")
    assert result2["ok"] is True
    assert result2["missing"] == ["P2", "P3"]

    # 测试越界钳制
    mock_clamp = """
```json
{"stance": {"P1": 7, "P2": -1, "P3": 3}}
```
"""
    result3 = parse_stance(mock_clamp, ["P1", "P2", "P3"])
    print(f"parse_stance clamp: ok={result3['ok']}, stance={result3['stance']}, fixes={result3['fixes']}")
    assert result3["stance"]["P1"] == 5
    assert result3["stance"]["P2"] == 1

    # 测试 round_cv
    stance_data = {
        "debater_1": {"P1": 4, "P2": 3, "P3": 5},
        "debater_2": {"P1": 3, "P2": 3, "P3": 2},
        "debater_3": {"P1": 5, "P2": 4, "P3": 4},
    }
    cv = round_cv(stance_data, ["P1", "P2", "P3"])
    print(f"round_cv: overall={cv['overall']:.4f}, per_arg={cv['per_argument']}")

    # 测试 check_termination
    hist_converge = [0.35, 0.22, 0.12, 0.05]
    stop, reason = check_termination(hist_converge)
    print(f"termination (converge): stop={stop}, reason={reason}")
    assert stop is True

    hist_deadlock = [0.40, 0.39, 0.385, 0.381]
    stop2, reason2 = check_termination(hist_deadlock)
    print(f"termination (deadlock 2a): stop={stop2}, reason={reason2}")
    assert stop2 is True

    hist_ongoing = [0.40, 0.30, 0.20]
    stop3, reason3 = check_termination(hist_ongoing)
    print(f"termination (ongoing): stop={stop3}, reason={reason3}")
    assert stop3 is False

    # 解析失败率门：CV 很低但失败率高 → 应被拦截
    hist_low_cv = [0.35, 0.10, 0.05]
    stop4, reason4 = check_termination(hist_low_cv, fail_rate=0.30)
    print(f"termination (fail_rate gate): stop={stop4}, reason={reason4}")
    assert stop4 is False and "blocked_by_parse_fail_gate" in reason4

    # 失败率门边缘：刚好 < 20% → 不拦截
    stop5, reason5 = check_termination(hist_low_cv, fail_rate=0.19)
    print(f"termination (fail_rate 0.19, pass): stop={stop5}, reason={reason5}")
    assert stop5 is True and "converged" in reason5

    # 无 fail_rate（默认 None）→ 不过门，正常判定
    stop6, reason6 = check_termination(hist_low_cv)
    assert stop6 is True and "converged" in reason6

    # ── v2.1 轨道2b 复合僵局：用 08-08 真实实验 A/B/C 数据回放 ──

    # C 题（真僵局，高位震荡）：连续平台轨道全程抓不到，2b 应在 R3 即触发
    c_cv = [0.4698, 0.4606, 0.3900, 0.4177]
    c_per_arg = [
        {"P1": 0.637, "P2": 0.510, "P3": 0.510, "P4": 0.354, "P5": 0.808, "P6": 0.000},
        {"P1": 0.637, "P2": 0.354, "P3": 0.510, "P4": 0.354, "P5": 0.808, "P6": 0.101},
        {"P1": 0.471, "P2": 0.354, "P3": 0.354, "P4": 0.354, "P5": 0.808, "P6": 0.000},
        {"P1": 0.637, "P2": 0.354, "P3": 0.354, "P4": 0.354, "P5": 0.808, "P6": 0.000},
    ]
    # 旧规则（无 per_arg）：全程不触发（实证还原）
    stop_c_old, _ = check_termination(list(c_cv))
    assert stop_c_old is False, "旧轨道2a 对高位震荡型僵局应抓不到（还原实验C实证）"
    # v2.1 逐轮回放：R3 起应触发 composite_deadlock
    fired_at = None
    for i in range(len(c_cv)):
        s, r = check_termination(c_cv[:i + 1], per_arg_history=c_per_arg[:i + 1])
        if s:
            fired_at, fired_reason = i, r
            break
    print(f"termination (C题真僵局 v2.1): fired_at_index={fired_at}, reason={fired_reason}")
    assert fired_at == 1, f"C题应在第2个CV点(R3)触发，实际 {fired_at}"
    assert "composite_deadlock" in fired_reason

    # A 题：R3 CV=0.1312 > ε1=0.07 → 不再判收敛（v1校准修正：旧 ε1=0.15 时误判 converged）
    a_cv = [0.2475, 0.1312]
    a_per_arg = [
        {"P1": 0.340, "P2": 0.374, "P3": 0.354, "P4": 0.109, "P5": 0.354, "P6": 0.101, "P7": 0.101},
        {"P1": 0.204, "P2": 0.129, "P3": 0.283, "P4": 0.101, "P5": 0.202, "P6": 0.000, "P7": 0.000},
    ]
    s_a1, _ = check_termination(a_cv[:1], per_arg_history=a_per_arg[:1])
    assert s_a1 is False, "A题R1 不应触发（仍在移动）"
    s_a2, r_a2 = check_termination(a_cv, per_arg_history=a_per_arg)
    print(f"termination (A题 v1校准后): stop={s_a2}, reason={r_a2}")
    assert s_a2 is False, "v1校准后 ε1=0.07，A题 CV=0.1312 > ε1，不再假收敛"

    # B 题：R2 CV=0.1353 > ε1=0.07 → 轨道1 不再判收敛（v1校准修正：旧 ε1=0.15 时误判 converged）
    b_cv = [0.1627, 0.1353]
    b_per_arg = [
        {"P1": 0.129, "P2": 0.141, "P3": 0.202, "P4": 0.283, "P5": 0.101, "P6": 0.283, "P7": 0.000},
        {"P1": 0.129, "P2": 0.177, "P3": 0.000, "P4": 0.141, "P5": 0.109, "P6": 0.283, "P7": 0.109},
    ]
    s_b, r_b = check_termination(b_cv, per_arg_history=b_per_arg)
    print(f"termination (B题 v1校准后): stop={s_b}, reason={r_b}")
    assert s_b is False, "v1校准后 ε1=0.07，B题 CV=0.1353 > ε1，不再假收敛"

    # 合成用例：高位健康移动不应触发 2b（多数论点 down）
    h_cv = [0.4500, 0.3300]
    h_per_arg = [
        {"P1": 0.500, "P2": 0.500, "P3": 0.500, "P4": 0.400},
        {"P1": 0.300, "P2": 0.300, "P3": 0.300, "P4": 0.350},
    ]
    s_h, r_h = check_termination(h_cv, per_arg_history=h_per_arg)
    print(f"termination (高位移动中 v2.1): stop={s_h}, reason={r_h}")
    assert s_h is False, "高位但多数论点在收敛中，不应判僵局"

    print("\n✓ 全部自测通过（含 v2.1 复合僵局 A/B/C 真实数据回放）")
