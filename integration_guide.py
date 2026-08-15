#!/usr/bin/env python3
"""
共识管线 v2 · 集成适配指南（代码形态）
=====================================
本文件以伪代码+注释的形式，描述 5 个适配点的具体打法。


配套：
  - stance_quant_v2.py   → v2 采集器核心代码
  - analyze_stance_log.py → 日志分析器
  - mock_experiment.py    → 独立测试（无需 debate_engine.py 即可验证全链路）
"""

# ================================================================
# 适配点 #0：LLM 调用 wrapper 复用
# ================================================================
# 在 debate_engine.py 中找到现有的 LLM 调用函数（返回文本的那个）。
# 封装一个签名兼容的 wrapper 给 stance_quant_v2 用：
#
#   def llm_call_for_stance(prompt: str) -> str:
#       """复用现有 LLM wrapper，返回纯文本。"""
#       response = your_existing_llm_call(prompt)  # ← 替换为实际调用
#       return response.text  # ← 或 response['content'] 等
#
# 如果 wrapper 还返回 token usage，一并记录：
#   def llm_call_with_usage(prompt: str) -> tuple[str, int, int]:
#       response = your_existing_llm_call(prompt)
#       return response.text, response.prompt_tokens, response.completion_tokens


# ================================================================
# 适配点 #1：R1 后插入论点抽取
# ================================================================
# 在 debate_engine.py 中，R1 全部辩手发言收齐之后、R2 开始之前，插入：
#
#   from stance_quant_v2 import StanceTracker
#
#   tracker = StanceTracker(
#       run_id=f"v2proto_{date_str}_{topic_tag}",
#       topic=topic_text,
#       log_dir=run_output_dir,
#   )
#
#   # 拼接 R1 全部发言
#   round1_transcript = "\n\n".join(
#       f"[{debater_id}]: {output}" for debater_id, output in round1_outputs.items()
#   )
#   arguments = tracker.extract_arguments(round1_transcript, llm_call_for_stance)
#
#   # 持久化论点清单（中断恢复用）
#   import json
#   with open(run_output_dir / "arguments.json", "w") as f:
#       json.dump(arguments, f, ensure_ascii=False, indent=2)
#
# 降级：如果 arguments 为空列表，跳过后续 stance 采集，辩论照常进行。


# ================================================================
# 适配点 #2：R2 起追加表态块到辩手 prompt
# ================================================================
# 在辩手 prompt 组装函数的末尾，R2 起追加：
#
#   if round_num >= 2 and tracker.arguments:
#       stance_block = tracker.get_stance_block()
#       prompt += "\n\n" + stance_block


# ================================================================
# 适配点 #3：每辩手输出处接 parse_stance + round_cv
# ================================================================
# 每个辩手每轮输出返回后：
#
#   tracker.record_debater_stance(
#       debater_id=debater_id,
#       raw_output=debater_output,
#       prompt_tokens=prompt_tokens,      # 取不到填 0
#       completion_tokens=completion_tokens,
#   )
#
# 一轮全部辩手收齐后：
#
#   cv_result = tracker.finish_round(round_num)
#   # cv_result 包含：
#   #   overall: 轮级 CV
#   #   per_argument: 论点级 CV
#   #   cv_history: 历史 CV 列表
#   #   termination: (should_stop, reason) — 影子模式


# ================================================================
# 适配点 #4：JSONL 日志（自动，无需额外操作）
# ================================================================
# stance_quant_v2.py 内部的 write_stance_log() 会自动写
# debate_stance_log.jsonl，与原 debate_log 并存，互不干扰。
# 确认 log_dir 路径正确即可。


# ================================================================
# 适配点 #5：轮次参数
# ================================================================
# 找到 debate_engine.py 中的 rounds 参数（默认 3）。
# 首轮实验保持 3 不变。
# 如果 token 预算允许，第二组实验调到 5（校准方案建议值）。
#
#   # 首轮：
#   rounds = 3
#   # 第二组（可选）：
#   rounds = 5


# ================================================================
# 实验结束后
# ================================================================
# 1. 运行分析器：
#    python analyze_stance_log.py debate_stance_log.jsonl
#
# 2. 或输出到文件：
#    python analyze_stance_log.py debate_stance_log.jsonl -o 观察报告.md
#
# 3. 填写 10.4 观察记录表，判断 go/no-go。
