#!/usr/bin/env python3
"""
领域配置生成器 — Consensus Pipeline v6.0

根据研究主题动态生成领域配置，保证管线通用性。
不再依赖硬编码的领域关键词（如碳纳米管排除词、能源关键词等），
而是根据用户输入的研究主题，动态生成exclusion_signals、query_rotation、tier_definitions等。
"""
import json
import os
from typing import Dict, Any, Callable


def generate_domain_config(topic: str, llm_call_fn: Callable, output_dir: str = "") -> Dict[str, Any]:
    """
    根据研究主题动态生成领域配置。

    调用LLM，输入主题，输出包含以下字段的JSON：
    - domain_definition: 领域边界描述
    - exclusion_signals: 排除信号词列表
    - query_rotation: 搜索词轮换列表
    - tier_definitions: core/method/background三层定义
    - llm_classify_prompt: LLM二分类prompt模板

    Args:
        topic: 研究主题（如"机器学习在能源经济学上的运用"）
        llm_call_fn: LLM调用函数 (system_prompt, user_message, temperature) -> str
        output_dir: 输出目录，用于保存domain_config.json

    Returns:
        领域配置字典
    """
    system_prompt = """你是一个学术领域分析专家。你的任务是根据给定的研究主题，生成一个精确的领域配置JSON。

这个配置将用于学术文献调研管线的自动过滤，必须足够精确以排除不相关论文，同时足够宽泛以不遗漏相关论文。

你必须输出一个合法的JSON对象，包含以下字段：

1. "domain_definition": 一段100字以内的领域边界描述，明确该领域的核心研究对象和方法论范围

2. "exclusion_signals": 一个字符串列表（15-25个），包含不属于该领域的排除信号词。
   这些词出现时，论文大概率不属于目标领域。例如：
   - 如果研究ML在能源经济学中的应用，排除信号应包含：nanotube, nanowire, plant growth, 
     bacterial, photosynthesis, drug discovery, clinical trial, genetic, 
     semiconductor device, quantum computing, astrophysics 等
   - 必须覆盖常见的跨领域噪声源：材料科学、生物学、医学、纯化学、纯物理等

3. "query_rotation": 一个字符串列表（6-10个），用于搜索词轮换。
   每个搜索词应覆盖不同的检索角度：
   - 核心方法+领域组合（如"machine learning energy price forecasting"）
   - 具体子领域（如"deep learning carbon market prediction"）
   - 近义词变体（如"artificial intelligence electricity demand"）
   - 方法论角度（如"neural network load forecasting"）

4. "tier_definitions": 一个对象，包含三个层级定义：
   - "core": 该领域最核心的论文（直接研究主题+方法论）
     - "keywords": 关键词列表（10-15个）
     - "description": 层级描述
   - "method": 方法论补充层（研究的方法在目标领域有应用，但论文本身可能是其他领域的）
     - "keywords": 关键词列表（8-12个）
     - "description": 层级描述
   - "background": 机制背景层（提供领域背景知识，但不直接涉及方法论创新）
     - "keywords": 关键词列表（8-12个）
     - "description": 层级描述

5. "llm_classify_prompt": 一个字符串，是LLM二分类的system prompt模板。
   其中用{domain_definition}作为占位符，运行时会被替换为实际的domain_definition。
   prompt要求LLM对每篇论文回答"是"或"否"——这篇论文是否属于目标领域。
   格式要求：对每篇论文输出"论文N：是/否"，并附简短理由。

重要：
- 只输出JSON，不要输出任何其他文字
- 确保JSON合法可解析
- 关键词用英文小写
- 排除信号要覆盖常见的噪声领域"""

    user_msg = f"研究主题：{topic}\n\n请生成该领域的精确配置JSON。"

    try:
        response = llm_call_fn(system_prompt, user_msg, temperature=0.2)
    except Exception as e:
        # LLM调用失败，返回默认配置
        return _default_domain_config(topic)

    if not response:
        return _default_domain_config(topic)

    # 从响应中提取JSON
    config = _extract_json(response)

    if not config:
        return _default_domain_config(topic)

    # 校验必要字段
    required_fields = ["domain_definition", "exclusion_signals", "query_rotation",
                       "tier_definitions", "llm_classify_prompt"]
    for field in required_fields:
        if field not in config:
            config[field] = _default_domain_config(topic).get(field, "")

    # 确保tier_definitions结构完整
    if "tier_definitions" in config:
        for tier in ["core", "method", "background"]:
            if tier not in config["tier_definitions"]:
                config["tier_definitions"][tier] = {
                    "keywords": [],
                    "description": f"{tier} layer"
                }
            elif "keywords" not in config["tier_definitions"][tier]:
                config["tier_definitions"][tier]["keywords"] = []

    # 保存到文件
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, "domain_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def _extract_json(text: str) -> Dict[str, Any]:
    """从文本中提取JSON对象"""
    import re

    # 尝试1: 整体解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试2: 提取```json ... ```代码块
    pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试3: 找第一个{到最后一个}
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def _default_domain_config(topic: str) -> Dict[str, Any]:
    """默认领域配置（LLM调用失败时的回退方案）"""
    return {
        "domain_definition": f"关于{topic}的学术研究",
        "exclusion_signals": [
            "nanotube", "nanowire", "photosynthesis", "bacterial",
            "drug discovery", "clinical trial", "genetic mutation",
            "semiconductor device", "quantum computing", "astrophysics",
            "plant growth", "soil microbiome", "volcanic", "geological",
            "marine biology",
        ],
        "query_rotation": [
            topic,
            f"{topic} review survey",
            f"{topic} methodology comparison",
            f"{topic} recent advances",
        ],
        "tier_definitions": {
            "core": {
                "keywords": [],
                "description": f"直接研究{topic}的论文"
            },
            "method": {
                "keywords": [],
                "description": "方法论相关但可能不在目标领域的论文"
            },
            "background": {
                "keywords": [],
                "description": "领域背景知识论文"
            }
        },
        "llm_classify_prompt": f"""你是一个学术领域分类专家。你的任务是判断论文是否属于以下研究领域：{topic}

对每篇论文，请判断它是否属于该领域，输出格式：
论文N：是/否 — 简短理由

判定标准：
- "是"：论文的研究主题或方法论直接与"{topic}"相关
- "否"：论文完全不涉及该领域（如属于材料科学、生物学、医学等不相关领域）

请严格按照格式输出。"""
    }
