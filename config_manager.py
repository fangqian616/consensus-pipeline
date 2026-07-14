"""
配置管理模块 — Consensus Pipeline v3.0
管理预设（presets/）和用户配置（user_profiles/），支持导入导出和持久化。
"""
import json
import os
from typing import Optional, Dict, List

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PRESETS_DIR = os.path.join(_BASE_DIR, "presets")
_PROFILES_DIR = os.path.join(_BASE_DIR, "user_profiles")
_LAST_USED_FILE = os.path.join(_PROFILES_DIR, ".last_used")


def _ensure_dirs():
    """确保目录存在"""
    os.makedirs(_PRESETS_DIR, exist_ok=True)
    os.makedirs(_PROFILES_DIR, exist_ok=True)


# ============ 预设管理 ============

def list_presets() -> List[str]:
    """列出内置预设名称（不含.json后缀）"""
    _ensure_dirs()
    names = []
    for f in sorted(os.listdir(_PRESETS_DIR)):
        if f.endswith(".json"):
            names.append(f[:-5])
    return names


def load_preset(name: str) -> dict:
    """从presets/加载内置预设，返回PresetConfig格式dict"""
    path = os.path.join(_PRESETS_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"预设不存在: {name}（查找路径: {path}）")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============ 用户配置管理 ============

def list_profiles() -> List[str]:
    """列出用户保存的配置名称（不含.json后缀）"""
    _ensure_dirs()
    names = []
    for f in sorted(os.listdir(_PROFILES_DIR)):
        if f.endswith(".json") and not f.startswith("."):
            names.append(f[:-5])
    return names


def save_profile(name: str, config: dict):
    """保存配置到user_profiles/"""
    _ensure_dirs()
    # 确保配置中有名称
    config["name"] = name
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_profile(name: str) -> dict:
    """从user_profiles/加载用户配置"""
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"用户配置不存在: {name}（查找路径: {path}）")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_profile(name: str):
    """删除用户配置"""
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
    # 如果删除的是上次使用的配置，也清除记录
    last = get_last_used()
    if last == name:
        set_last_used("")


# ============ 导入导出 ============

def export_config(config: dict) -> str:
    """导出配置为JSON字符串"""
    return json.dumps(config, ensure_ascii=False, indent=2)


def import_config(json_str: str) -> dict:
    """从JSON字符串导入配置，做基本校验"""
    config = json.loads(json_str)
    # 基本校验：至少要有name和departments
    if "name" not in config:
        raise ValueError("配置缺少 'name' 字段")
    if "departments" not in config:
        raise ValueError("配置缺少 'departments' 字段")
    return config


# ============ 上次使用记录 ============

def get_last_used() -> str:
    """获取上次使用的配置名称"""
    if os.path.exists(_LAST_USED_FILE):
        with open(_LAST_USED_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def set_last_used(name: str):
    """记录上次使用的配置名称"""
    _ensure_dirs()
    with open(_LAST_USED_FILE, "w", encoding="utf-8") as f:
        f.write(name)


# ============ 配置校验 ============

def validate_config(config: dict) -> List[str]:
    """
    校验PresetConfig格式，返回错误列表（空=合法）。
    不报错但可改进的项用warning形式返回。
    """
    errors = []
    
    if "name" not in config:
        errors.append("缺少 'name' 字段")
    if "departments" not in config:
        errors.append("缺少 'departments' 字段")
    elif not isinstance(config["departments"], dict):
        errors.append("'departments' 必须是字典")
    else:
        for dept_key, dept in config["departments"].items():
            if "debaters" not in dept:
                errors.append(f"部门 '{dept_key}' 缺少 'debaters' 字段")
            elif not isinstance(dept["debaters"], dict):
                errors.append(f"部门 '{dept_key}' 的 'debaters' 必须是字典")
            else:
                for debater_key, debater in dept["debaters"].items():
                    if "zh_style" not in debater and "en_style" not in debater:
                        errors.append(f"部门 '{dept_key}' 辩手 '{debater_key}' 缺少风格描述")
    
    return errors


# ============ 配置合并/补丁 ============

def merge_skill_injection(config: dict, skill_markdown: str, target_departments: List[str] = None) -> dict:
    """
    将Skill注入的markdown内容追加到指定部门的所有辩手提示词末尾。
    
    Args:
        config: 原始PresetConfig
        skill_markdown: 要注入的markdown内容
        target_departments: 目标部门列表，None=所有部门
    
    Returns:
        修改后的PresetConfig（深拷贝）
    """
    import copy
    result = copy.deepcopy(config)
    
    injection_zh = f"\n\n【Skill注入】\n{skill_markdown}"
    injection_en = f"\n\n[Skill Injection]\n{skill_markdown}"
    
    for dept_key, dept in result.get("departments", {}).items():
        if target_departments and dept_key not in target_departments:
            continue
        for debater_key, debater in dept.get("debaters", {}).items():
            if "zh_style" in debater:
                debater["zh_style"] += injection_zh
            if "en_style" in debater:
                debater["en_style"] += injection_en
    
    return result
