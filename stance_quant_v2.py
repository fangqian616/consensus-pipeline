#!/usr/bin/env python3
"""
共识管线 v2 分歧量化模块 — 影子模式采集器
==========================================

收敛与僵局判定：
  • 收敛判定：CV < 0.07 判收敛（ε1=0.07）
  • 僵局判定：|ΔCV| < 0.01 视为走平（ε2=0.01）
  • 复合僵局：(flat+up)/总论点 ≥ 0.75 且 CV ≥ ε1 → 高位僵持
  • 解析失败率门：最新轮失败率 ≥ 20% 时跳过一切判定，防止 CV 假低信号

依赖：仅 Python 标准库（json / re / ast / statistics / datetime / pathlib / logging）

函数速查：
  extract_arguments()      → R1后抽取核心论点清单（需传入LLM调用函数）
  render_stance_block()    → 渲染表态块prompt文本（R2起追加到辩手prompt末尾）
  parse_stance()           → 解析单个辩手一轮的表态块（容错，永不抛异常）
  argument_cv()            → 单论点CV
  round_cv()               → 轮级CV聚合
  check_termination()      → 终止判定：轨道1收敛 / 轨道2a连续平台 / 轨道2b高位僵持 + 解析失败率门
  write_stance_log()       → 写JSONL日志
  StanceTracker            → 便捷封装：串联以上全部，维护状态
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
# 默认参数
# ─────────────────────────────────────────────
EPS1 = 0.07        # 收敛阈值：CV < ε1 判收敛
EPS2 = 0.01        # 僵局阈值：|ΔCV| < ε2 视为走平
N_PLATEAU = 2      # 连续 N 轮满足即判僵局（3轮制下N=2是上限）
# 复合僵局阈值：最近间隔 (flat+up)/总论点 ≥ 0.75 且 CV > ε1 → 判「高位僵持」。
FLAT_UP_RATIO_TH = 0.75
MAX_PARSE_FAIL_RATE = 0.20  # 解析失败率门：最新轮失败率 ≥ 此值时，CV 信号不可信，跳过一切判定
# v0.13.2: Kendall's W 联合收敛阈值（替代 α 作为交叉验证）。W 抗「打分高位压缩」，
# 与 CV 互补（CV 看离散度，W 看排序一致）。W 缺失(None)时退化为只看 CV。
W_THRESHOLD = 0.5   # W > 0.5 判「偏强一致」→ 与 CV<ε1 联合判收敛
W_STRONG = 0.7      # W > 0.7 判「强一致」→ 仅报告分档标注，不参与判定

# ─────────────────────────────────────────────
# §3 核心论点清单抽取
# ─────────────────────────────────────────────

ARGUMENT_EXTRACT_PROMPT = """\
【核心论点抽取】
基于以下第 1 轮全部辩手发言，抽取本场辩论的 3-7 条核心论点。

要求：
1. 每条论点必须是「可被论文证据支撑或反驳的学术主张」（有立场的判断），而不是「事实陈述/统计观察」。
   - 合格（可辩论）：如「LLM 驱动的 NPC 对话在长期交互中存在人设漂移问题」「基于检索增强的方法比端到端微调更适合游戏 NPC 生成」「当前评估过度依赖人工评判、缺乏自动化指标」
   - 不合格（纯事实）：如「20 篇论文覆盖了 6 个主题聚类」「80% 的论文发表于 2018 年后」「被引集中度较高」——这些是数据描述，不是主张
   判断标准：如果一个论点找不到「支撑它的论文」或「反驳它的论文」，它就不是合格论点，不要抽取。
2. 每条论点是一句可判断对错的命题（陈述句），不要问题、不要泛泛主题。
3. 论点之间尽量不重叠；合并同义表述。
4. 既覆盖主要分歧点，也保留 1-2 条明显共识点（共识点在后续量化中充当对照组）。
5. 用稳定 ID 编号：P1, P2, P3……一旦确定，后续轮次沿用不变。

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


def filter_debatable_arguments(arguments: list[dict], llm_call_fn) -> list[dict]:
    """
    后验过滤：剔除纯事实陈述/统计观察，只保留「可辩论的学术主张」。

    这是论点抽取的保险丝：第一步抽取可能有漏网之鱼（把数据描述当主张），
    这里再让 LLM 校验一遍，把事实陈述改写为可辩论主张，无法改写则丢弃。

    参数：
      arguments: [{"id": "P1", "text": "..."}, ...]
      llm_call_fn: 签名 fn(prompt: str) -> str

    返回：
      过滤/改写后的论点列表（失败则原样返回，宁可不滤不误删）。
    """
    if not arguments or not llm_call_fn:
        return arguments

    arg_list = "\n".join(f'{a["id"]}: {a["text"]}' for a in arguments)
    prompt = f"""判断以下每个论点是「可辩论的学术主张」还是「事实陈述/统计观察」。

只保留「可辩论的学术主张」。如果是事实陈述，尝试改写为可辩论的主张；如果无法改写，则丢弃。

判断标准：一个论点必须能被「论文证据」支撑或反驳。纯粹的数据描述（如"20篇论文覆盖6个聚类"）不是主张。

论点列表：
{arg_list}

输出 JSON（只保留合格/改写后的论点，沿用原 ID）：
{{"keep": [{{"id": "P1", "text": "改写后的主张"}}, ...]}}
"""
    try:
        raw = llm_call_fn(prompt)
        data = extract_json_block(raw, '"keep"')
        if isinstance(data, dict) and isinstance(data.get("keep"), list):
            kept = []
            for item in data["keep"]:
                if isinstance(item, dict) and item.get("id") and item.get("text"):
                    kept.append({"id": str(item["id"]), "text": str(item["text"])})
            if kept:
                return kept
    except Exception:
        pass
    return arguments


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

    # === 后验过滤: 只保留可辩论的学术主张(剔除纯事实陈述) ===
    if result["ok"] and result["arguments"]:
        try:
            result["arguments"] = filter_debatable_arguments(
                result["arguments"], llm_call_fn)
        except Exception:
            pass

    return result["arguments"]




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
# §6.5 一致性度量（Kendall's W）——影子对照指标（v0.13.2: α 已移除，改用 W）
# ─────────────────────────────────────────────


def kendall_w(stance_by_debater: dict, arg_ids: list) -> Optional[float]:
    """Kendall's W 协调系数（0-1，排序一致，带并列秩校正）。"""
    from collections import Counter
    debaters = list(stance_by_debater.keys())
    matrix = []
    for d in debaters:
        vals = [stance_by_debater[d].get(aid) for aid in arg_ids]
        if any(v is None for v in vals):
            return None
        matrix.append(vals)
    K, N = len(matrix), len(arg_ids)
    if K < 2 or N < 2:
        return None

    def _avg_rank(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    ranked = [_avg_rank(row) for row in matrix]
    R = [sum(ranked[j][i] for j in range(K)) for i in range(N)]
    Rbar = K * (N + 1) / 2
    S = sum((Ri - Rbar) ** 2 for Ri in R)
    T = 0
    for row in matrix:
        for t in Counter(row).values():
            T += t ** 3 - t
    denom = K ** 2 * (N ** 3 - N) - K * T
    if denom <= 0:
        all_same = len({v for row in matrix for v in row}) == 1
        return 1.0 if all_same else None
    return max(0.0, min(1.0, 12 * S / denom))


def mean_stance(stance_by_debater: dict, arg_ids: list) -> Optional[float]:
    """轮级平均表态分（非中立守卫用：离 3 足够远才是实质收敛）。"""
    vals = [s.get(aid) for s in stance_by_debater.values() for aid in arg_ids if s.get(aid) is not None]
    return sum(vals) / len(vals) if vals else None


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
    逐论点相邻轮转移分类计数。
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
    w: Optional[float] = None,
) -> tuple[bool, Optional[str]]:
    """
    双轨终止判定。返回 (should_stop, reason)。

    轨道1  收敛：最新一轮 CV < ε1
    轨道2a 软性僵局（连续平台）：最近 n 个 |ΔCV| 全部 < ε2
    轨道2b 软性僵局（高位僵持）：当前 CV > ε1 且最近间隔
           (flat+up)/总论点 ≥ flat_up_ratio_th —— 多数论点无收敛动作且总体
           分歧仍高位：高位震荡型僵局会被一次显著下降打破连续性后反升，
           连续平台轨道对其不敏感。

    参数：
      cv_history: 各轮CV列表（从R2开始，长度=rounds-1）
      eps1: 收敛阈值
      eps2: 显著性带宽（|ΔCV| 小于此值视为走平）
      n: 连续轮次数（轨道2a）
      per_arg_history: 每轮 cv_per_argument 字典列表（轨道2b 需要；缺省则跳过2b）
      flat_up_ratio_th: 轨道2b 占比阈值
      fail_rate: 最新轮解析失败率（0~1）。≥ MAX_PARSE_FAIL_RATE 时 CV 信号不可信，
                 跳过一切判定返回 (False, "blocked_by_parse_fail_gate")

    返回：
      (should_stop: bool, reason: str or None)
    """
    hist = [c for c in cv_history if c is not None]
    if not hist:
        return False, None

    # 解析失败率门：最新轮失败率过高时 CV 信号不可信，一律不判
    if fail_rate is not None and fail_rate >= MAX_PARSE_FAIL_RATE:
        return False, f"blocked_by_parse_fail_gate: fail_rate={fail_rate:.2%} >= {MAX_PARSE_FAIL_RATE:.0%}"

    # 轨道1：收敛（CV < ε1 且 W 达标；W 缺失退化为只看 CV）
    if hist[-1] < eps1:
        if w is None:
            # W 无法计算（LLM 表态缺失/网络波动）→ 退化为只看 CV，但标注缺失
            return True, (f"converged: CV={hist[-1]:.4f} < eps1={eps1} "
                          f"(W 无法计算: LLM 表态缺失/网络波动, 退化为只看 CV)")
        if w > W_THRESHOLD:
            return True, (f"converged: CV={hist[-1]:.4f} < eps1={eps1} "
                          f"且 W={w:.3f} > {W_THRESHOLD}")
        # CV 达标但 W 分歧 → 疑似假收敛，不判收敛，继续辩论
        return False, (f"cv_low_but_w_low: CV={hist[-1]:.4f} < eps1={eps1} "
                       f"但 W={w:.3f} <= {W_THRESHOLD}（疑似假收敛，继续）")

    # 轨道2b：高位僵持（复合僵局，优先于 2a）
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
        self.w_history: list[Optional[float]] = []  # v0.13.2: 影子 W 历史（联合收敛用）
        self.per_arg_history: list[dict] = []  # ：每轮 cv_per_argument，供轨道2b
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

    def ask_stance(self, debater_id: str, speech_text: str, llm_call_fn) -> dict:
        """独立表态采集：单独调 LLM 只问表态 JSON（短输出，不会被长发言截断）。

        替代"表态块追加在发言末尾"的老路径——代码/教程等长输出部门
        表态块会被 max_tokens 截断导致空表态。这里单独一问，稳。
        """
        if not self.arg_ids or not llm_call_fn:
            return {}
        arg_list = "\n".join(f"{a['id']}: {a['text']}" for a in self.arguments)
        prompt = (
            "你是本场辩论的一名辩手。以下是核心论点清单和你本轮发言。"
            "请只输出你对每条论点的表态 JSON，不要输出任何其他内容。\n\n"
            f"核心论点清单：\n{arg_list}\n\n"
            f"你本轮发言（节选）：\n{speech_text[:1500]}\n\n"
            "评分标尺（Likert 1-5，整数）：1=强烈反对 2=反对 3=中立/证据不足 4=支持 5=强烈支持\n\n"
            '输出格式（严格 JSON，不要任何其他内容）：\n{"stance": {"P1": 3, "P2": 4}}\n'
        )
        try:
            raw = llm_call_fn(prompt)
        except Exception as e:
            print(f"[shadow_cv] ask_stance LLM fail: {e}")
            return {}
        parsed = parse_stance(raw or "", self.arg_ids)
        # 重试一次：解析失败时用更严格提示再问，降低空表态率
        if not parsed["stance"]:
            retry_prompt = (
                "请只输出一行 JSON，不要任何解释、不要代码块围栏、不要多余文字。\n"
                f"论点 ID 列表：{self.arg_ids}\n"
                '格式示例：{"stance": {"P1": 3, "P2": 4}}\n'
                "现在请对每个论点打分（1-5 整数）并输出 JSON。"
            )
            try:
                raw2 = llm_call_fn(retry_prompt)
                parsed = parse_stance(raw2 or "", self.arg_ids)
            except Exception:
                pass
        self.current_round_stances[debater_id] = parsed["stance"]
        write_stance_log(self.log_path, {
            "event": "round_stance",
            "run_id": self.run_id,
            "debater": debater_id,
            "stance": parsed["stance"],
            "parse_ok": parsed["ok"],
            "missing": parsed["missing"],
            "fixes": parsed["fixes"],
            "prompt_tokens": 0,
            "completion_tokens": 0,
        })
        return parsed["stance"]

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

        # 影子一致性指标（W / 平均分）——W 参与联合收敛判定，mean_stance 只记录
        w = kendall_w(self.current_round_stances, self.arg_ids)
        mu = mean_stance(self.current_round_stances, self.arg_ids)
        self.w_history.append(w)

        # 影子判定（：轨道2b 高位僵持；v0.13.2：轨道1 用 CV+W 联合收敛；fail_rate 门）
        latest_fail_rate = self.round_fail_rates[-1] if self.round_fail_rates else None
        should_stop, reason = check_termination(
            self.cv_history, per_arg_history=self.per_arg_history,
            fail_rate=latest_fail_rate, w=w)

        # 写轮次CV日志
        write_stance_log(self.log_path, {
            "event": "round_cv",
            "run_id": self.run_id,
            "round": round_num,
            "cv_overall": cv_result["overall"],
            "cv_per_argument": cv_result["per_argument"],
            "kendall_w": w,
            "mean_stance": mu,
            "termination_shadow": {
                "should_stop": should_stop,
                "reason": reason,
            },
        })

        result = {
            "round": round_num,
            "overall": cv_result["overall"],
            "per_argument": cv_result["per_argument"],
            "kendall_w": w,
            "mean_stance": mu,
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

        # 最终判定（：传入 per_arg_history + fail_rate；v0.13.2：加 W 联合判定）
        latest_fail_rate = self.round_fail_rates[-1] if self.round_fail_rates else None
        latest_w = self.w_history[-1] if self.w_history else None
        should_stop, reason = check_termination(
            self.cv_history, per_arg_history=self.per_arg_history,
            fail_rate=latest_fail_rate, w=latest_w)
        lines.append(f"Shadow verdict: {'STOP' if should_stop else 'CONTINUE'} — {reason or 'no trigger'}")

        return "\n".join(lines)


def render_convergence_diagnostic(log_path: str) -> str:
    """v0.13.2: 从 debate_stance_log.jsonl 生成「辩论收敛诊断」markdown 文本。

    展示最终收敛状态（CV / W / 平均表态分）+ 最近轮次轨迹 + W 分档解读。
    W=None 时标注「LLM 表态缺失（网络波动/解析失败），该轮退化为只看 CV」。
    供报告生成时追加到报告末尾。
    """
    try:
        with open(log_path, encoding="utf-8") as f:
            raw = f.read().strip().split("\n")
    except (OSError, IOError):
        return ""
    rounds = []
    for line in raw:
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        if j.get("event") == "round_cv":
            rounds.append(j)
    if not rounds:
        return ""

    last = rounds[-1]
    cv = last.get("cv_overall")
    w = last.get("kendall_w")
    mu = last.get("mean_stance")
    term = (last.get("termination_shadow") or {}).get("reason", "")

    def w_label(wv):
        if wv is None:
            return "N/A（LLM 表态缺失，退化为只看 CV）"
        if wv > W_STRONG:
            return f"{wv:.3f}（强一致）"
        if wv > W_THRESHOLD:
            return f"{wv:.3f}（偏强一致）"
        return f"{wv:.3f}（不一致）"

    lines = ["## 辩论收敛诊断", ""]
    lines.append("辩论收敛由两个独立指标联合判定：**CV（变异系数，看打分离散度）** 与 **Kendall's W（协调系数，看排序一致性）**。")
    lines.append("")
    lines.append("| 指标 | 最终值 | 判定标准 |")
    lines.append("|------|--------|---------|")
    cv_cell = f"{cv:.4f}" if cv is not None else "N/A"
    lines.append(f"| CV（变异系数） | {cv_cell} | < 0.07 判收敛 |")
    lines.append(f"| W（Kendall's W） | {w_label(w)} | > 0.5 偏强一致，> 0.7 强一致 |")
    mu_cell = f"{mu:.3f}" if mu is not None else "N/A"
    lines.append(f"| 平均表态分 | {mu_cell} | 远离 3（中立）才是实质立场 |")
    lines.append("")
    if term:
        lines.append(f"**收敛判定**：`{term}`")
        lines.append("")

    recent = rounds[-8:]
    lines.append("**最近轮次轨迹**：")
    lines.append("")
    lines.append("| 轮次 | CV | W | 平均表态分 |")
    lines.append("|------|----|----|-----------|")
    for j in recent:
        r = j.get("round")
        c = j.get("cv_overall")
        wj = j.get("kendall_w")
        mj = j.get("mean_stance")
        c_s = f"{c:.4f}" if c is not None else "N/A"
        w_s = f"{wj:.3f}" if wj is not None else "N/A（缺失）"
        m_s = f"{mj:.3f}" if mj is not None else "N/A"
        lines.append(f"| R{r} | {c_s} | {w_s} | {m_s} |")
    lines.append("")
    lines.append("> 说明：W=N/A 表示该轮 LLM 表态缺失（网络波动/解析失败），该轮退化为只看 CV。")
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

    # ── 轨道2b 复合僵局：用合成数据回放 ──

    # 用例 C（高位震荡僵局）：连续平台轨道全程抓不到，2b 应在 R3 即触发
    c_cv = [0.4698, 0.4606, 0.3900, 0.4177]
    c_per_arg = [
        {"P1": 0.637, "P2": 0.510, "P3": 0.510, "P4": 0.354, "P5": 0.808, "P6": 0.000},
        {"P1": 0.637, "P2": 0.354, "P3": 0.510, "P4": 0.354, "P5": 0.808, "P6": 0.101},
        {"P1": 0.471, "P2": 0.354, "P3": 0.354, "P4": 0.354, "P5": 0.808, "P6": 0.000},
        {"P1": 0.637, "P2": 0.354, "P3": 0.354, "P4": 0.354, "P5": 0.808, "P6": 0.000},
    ]
    # 旧规则（无 per_arg）：全程不触发
    stop_c_old, _ = check_termination(list(c_cv))
    assert stop_c_old is False, "旧轨道2a 对高位震荡型僵局应抓不到"
    # 逐轮回放：R3 起应触发 composite_deadlock
    fired_at = None
    for i in range(len(c_cv)):
        s, r = check_termination(c_cv[:i + 1], per_arg_history=c_per_arg[:i + 1])
        if s:
            fired_at, fired_reason = i, r
            break
    print(f"termination (用例C 高位僵局): fired_at_index={fired_at}, reason={fired_reason}")
    assert fired_at == 1, f"用例C应在第2个CV点(R3)触发，实际 {fired_at}"
    assert "composite_deadlock" in fired_reason

    # 用例 A：R3 CV=0.1312 > ε1=0.07 → 不再判收敛
    a_cv = [0.2475, 0.1312]
    a_per_arg = [
        {"P1": 0.340, "P2": 0.374, "P3": 0.354, "P4": 0.109, "P5": 0.354, "P6": 0.101, "P7": 0.101},
        {"P1": 0.204, "P2": 0.129, "P3": 0.283, "P4": 0.101, "P5": 0.202, "P6": 0.000, "P7": 0.000},
    ]
    s_a1, _ = check_termination(a_cv[:1], per_arg_history=a_per_arg[:1])
    assert s_a1 is False, "用例AR1 不应触发（仍在移动）"
    s_a2, r_a2 = check_termination(a_cv, per_arg_history=a_per_arg)
    print(f"termination (用例A): stop={s_a2}, reason={r_a2}")
    assert s_a2 is False, "ε1=0.07 下用例A CV=0.1312 > ε1，不再假收敛"

    # 用例 B：R2 CV=0.1353 > ε1=0.07 → 轨道1 不再判收敛
    b_cv = [0.1627, 0.1353]
    b_per_arg = [
        {"P1": 0.129, "P2": 0.141, "P3": 0.202, "P4": 0.283, "P5": 0.101, "P6": 0.283, "P7": 0.000},
        {"P1": 0.129, "P2": 0.177, "P3": 0.000, "P4": 0.141, "P5": 0.109, "P6": 0.283, "P7": 0.109},
    ]
    s_b, r_b = check_termination(b_cv, per_arg_history=b_per_arg)
    print(f"termination (用例B): stop={s_b}, reason={r_b}")
    assert s_b is False, "ε1=0.07 下用例B CV=0.1353 > ε1，不再假收敛"

    # 合成用例：高位健康移动不应触发 2b（多数论点 down）
    h_cv = [0.4500, 0.3300]
    h_per_arg = [
        {"P1": 0.500, "P2": 0.500, "P3": 0.500, "P4": 0.400},
        {"P1": 0.300, "P2": 0.300, "P3": 0.300, "P4": 0.350},
    ]
    s_h, r_h = check_termination(h_cv, per_arg_history=h_per_arg)
    print(f"termination (高位移动中): stop={s_h}, reason={r_h}")
    assert s_h is False, "高位但多数论点在收敛中，不应判僵局"

    print("\n✓ 全部自测通过")
