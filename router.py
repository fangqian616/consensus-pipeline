"""
AI Router模块 — Consensus Pipeline v3.0
分析用户输入，自动生成工作组配置（PresetConfig格式）。
"""
import json
import requests
from typing import Optional

# ============ 可用部门池 ============
# Router从这些部门中选择，根据用户需求裁剪
AVAILABLE_DEPARTMENTS = {
    "screenwriter": {"zh_name": "编剧部", "en_name": "Screenwriter"},
    "spatial": {"zh_name": "空间板块", "en_name": "Spatial Planning"},
    "storyboard": {"zh_name": "分镜部", "en_name": "Storyboard"},
    "dp": {"zh_name": "摄影指导部", "en_name": "Cinematography"},
    "lighting": {"zh_name": "灯光部", "en_name": "Lighting"},
    "vfx": {"zh_name": "视效部", "en_name": "Visual Effects"},
    "sound": {"zh_name": "音效部", "en_name": "Sound Design"},
    "editing": {"zh_name": "剪辑部", "en_name": "Editing"},
    # 通用内容创作扩展部门
    "narrative": {"zh_name": "叙事部", "en_name": "Narrative Design"},
    "visual_style": {"zh_name": "视觉风格部", "en_name": "Visual Style"},
    "content_structure": {"zh_name": "内容结构部", "en_name": "Content Structure"},
    "audience": {"zh_name": "受众分析部", "en_name": "Audience Analysis"},
    "quality": {"zh_name": "质控部", "en_name": "Quality Control"},
}

# ============ 内容类型模板 ============
CONTENT_TYPE_TEMPLATES = {
    "animation": {
        "zh_name": "动画制作",
        "default_departments": ["screenwriter", "spatial", "storyboard", "dp", "lighting", "vfx", "sound", "editing"],
        "debate_rounds": 3,
    },
    "video_short": {
        "zh_name": "短视频",
        "default_departments": ["screenwriter", "storyboard", "dp", "editing"],
        "debate_rounds": 2,
    },
    "novel": {
        "zh_name": "小说/文本创作",
        "default_departments": ["narrative", "content_structure", "audience", "quality"],
        "debate_rounds": 2,
    },
    "game_design": {
        "zh_name": "游戏设计",
        "default_departments": ["screenwriter", "spatial", "visual_style", "narrative", "quality"],
        "debate_rounds": 3,
    },
    "film": {
        "zh_name": "实拍电影",
        "default_departments": ["screenwriter", "spatial", "storyboard", "dp", "lighting", "sound", "editing"],
        "debate_rounds": 3,
    },
}

# ============ Router系统提示词 ============

ROUTER_SYSTEM_PROMPT_ZH = """你是Consensus Pipeline的AI Router。你的任务是根据用户描述的创作需求，自动配置最适合的辩论工作组。

## 你的工作流程
1. 分析用户输入，判断内容类型（动画/短视频/小说/游戏设计/实拍电影/其他）
2. 根据内容类型选择参与的部门（不是所有场景都需要全部8个部门）
3. 为每个参与部门配置2-4位辩手，每位辩手有不同的风格视角
4. 如有视觉需求，生成视觉指令
5. 配置交叉辩论组合
6. 返回完整的JSON配置

## 可用部门列表
screenwriter(编剧部), spatial(空间板块), storyboard(分镜部), dp(摄影指导部), lighting(灯光部), vfx(视效部), sound(音效部), editing(剪辑部), narrative(叙事部), visual_style(视觉风格部), content_structure(内容结构部), audience(受众分析部), quality(质控部)

## 输出格式（严格JSON，不要任何其他文字）
{
  "name": "配置名称（简洁描述）",
  "description": "配置详细描述",
  "content_type": "内容类型标识",
  "departments": {
    "部门key": {
      "zh_name": "中文名",
      "en_name": "英文名",
      "debaters": {
        "A": {"zh_name": "辩手中文名", "en_name": "辩手英文名", "zh_style": "中文风格描述（重要！要详细描述该辩手的专业视角和职责边界）", "en_style": "English style description"},
        "B": {...},
        "C": {...}
      }
    }
  },
  "dept_order": ["部门执行顺序"],
  "visual_directive": {"zh": "视觉指令中文（如无视觉需求则留空）", "en": "Visual directive English"},
  "p2_cross_debates": [{"side_a": "部门A", "side_b": "部门B", "zh_topic": "辩论主题", "en_topic": "Debate topic"}],
  "p5_cross_debates": [{"side_a": "部门A", "side_b": "部门B", "zh_topic": "辩论主题", "en_topic": "Debate topic"}],
  "proofread_departments": ["参与校对的部门"],
  "debate_rounds": 3,
  "negative_prompts": "",
  "needs_clarification": false,
  "clarification_questions": []
}

## 关键规则
- 每个部门至少2位辩手，至多4位
- 辩手风格必须有明确的职责边界和视角差异，不是泛泛的"不同角度"
- 辩手zh_style要写明：该辩手专注什么、职责边界在哪里、与其他辩手的根本分歧点
- 如果用户描述太模糊无法判断需求，设置needs_clarification=true并列出需要补充的问题
- 如果内容涉及视觉效果，visual_directive不能为空
- p2_cross_debates和p5_cross_debates根据部门间实际冲突点配置，不必照搬动画模板
- dept_order决定了部门串行执行的顺序，上游部门的产出会传递给下游
"""

ROUTER_SYSTEM_PROMPT_EN = """You are the AI Router for Consensus Pipeline. Your task is to automatically configure the optimal debate workgroup based on the user's creative needs.

## Your Workflow
1. Analyze user input to determine content type (animation/short video/novel/game design/film/other)
2. Select participating departments based on content type (not all scenarios need all 8 departments)
3. Configure 2-4 debaters per participating department, each with a distinct stylistic perspective
4. Generate visual directive if visual needs exist
5. Configure cross-debate pairings
6. Return complete JSON configuration

## Available Departments
screenwriter, spatial, storyboard, dp, lighting, vfx, sound, editing, narrative, visual_style, content_structure, audience, quality

## Output Format (strict JSON, no other text)
{
  "name": "Config name",
  "description": "Detailed description",
  "content_type": "Content type identifier",
  "departments": {
    "dept_key": {
      "zh_name": "Chinese name",
      "en_name": "English name",
      "debaters": {
        "A": {"zh_name": "...", "en_name": "...", "zh_style": "Detailed Chinese style description", "en_style": "Detailed English style description"},
        "B": {...},
        "C": {...}
      }
    }
  },
  "dept_order": ["execution order"],
  "visual_directive": {"zh": "...", "en": "..."},
  "p2_cross_debates": [{"side_a": "...", "side_b": "...", "zh_topic": "...", "en_topic": "..."}],
  "p5_cross_debates": [{"side_a": "...", "side_b": "...", "zh_topic": "...", "en_topic": "..."}],
  "proofread_departments": [...],
  "debate_rounds": 3,
  "negative_prompts": "",
  "needs_clarification": false,
  "clarification_questions": []
}

## Key Rules
- Each department must have 2-4 debaters
- Debater styles must have clear responsibility boundaries and perspective differences
- If user input is too vague, set needs_clarification=true with questions
- If content involves visuals, visual_directive must not be empty
- p2_cross_debates and p5_cross_debates should be configured based on actual conflict points
- dept_order determines sequential execution order; upstream output passes to downstream
"""


def analyze_and_configure(
    user_input: str,
    api_url: str,
    api_key: str,
    model: str,
    lang: str = "zh",
) -> dict:
    """
    分析用户输入，自动生成工作组配置。
    
    Args:
        user_input: 用户对创作需求的描述
        api_url: LLM API地址
        api_key: LLM API密钥
        model: 模型名称
        lang: 语言 "zh" 或 "en"
    
    Returns:
        PresetConfig格式的dict，包含工作组完整配置
    """
    system_prompt = ROUTER_SYSTEM_PROMPT_ZH if lang == "zh" else ROUTER_SYSTEM_PROMPT_EN
    
    user_prompt = f"用户需求描述：\n{user_input}" if lang == "zh" else f"User requirement:\n{user_input}"
    
    # 调用LLM
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
    except Exception as e:
        return {
            "error": True,
            "message": f"Router调用LLM失败: {str(e)}",
            "name": "配置失败",
            "description": "AI配组未能完成，请手动配置或重试",
            "departments": {},
            "dept_order": [],
            "visual_directive": {"zh": "", "en": ""},
            "p2_cross_debates": [],
            "p5_cross_debates": [],
            "proofread_departments": [],
            "debate_rounds": 2,
            "negative_prompts": "",
            "needs_clarification": True,
            "clarification_questions": ["请更详细地描述你的创作需求"],
        }
    
    # 解析JSON（容错：提取```json```代码块）
    config = _parse_json_response(content)
    if config is None:
        return {
            "error": True,
            "message": "Router返回的JSON解析失败，原始内容已保存",
            "raw_content": content,
            "name": "配置解析失败",
            "description": "AI返回格式异常，请重试或手动配置",
            "departments": {},
            "dept_order": [],
            "visual_directive": {"zh": "", "en": ""},
            "p2_cross_debates": [],
            "p5_cross_debates": [],
            "proofread_departments": [],
            "debate_rounds": 2,
            "negative_prompts": "",
            "needs_clarification": True,
            "clarification_questions": ["AI返回格式异常，请重试"],
        }
    
    # 确保必要字段存在
    config = _ensure_config_fields(config)
    config["error"] = False
    
    return config


def _parse_json_response(content: str) -> Optional[dict]:
    """从LLM响应中提取JSON，支持```json```代码块"""
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取```json```代码块
    import re
    json_blocks = re.findall(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    for block in json_blocks:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue
    
    # 尝试找最外层的大括号
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(content[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def _ensure_config_fields(config: dict) -> dict:
    """确保配置有必要字段，缺失的用默认值填充"""
    defaults = {
        "name": "未命名配置",
        "description": "",
        "content_type": "unknown",
        "departments": {},
        "dept_order": [],
        "visual_directive": {"zh": "", "en": ""},
        "p2_cross_debates": [],
        "p5_cross_debates": [],
        "proofread_departments": [],
        "debate_rounds": 2,
        "negative_prompts": "",
        "needs_clarification": False,
        "clarification_questions": [],
    }
    
    for key, default_val in defaults.items():
        if key not in config:
            config[key] = default_val
    
    # 确保dept_order与departments一致
    if not config["dept_order"]:
        config["dept_order"] = list(config["departments"].keys())
    
    return config
