"""
Configuration Manager — Consensus Pipeline v3.0
Manages presets (presets/) and user profiles (user_profiles/), with import/export and persistence support.
"""
import json
import os
from typing import Optional, Dict, List

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PRESETS_DIR = os.path.join(_BASE_DIR, "presets")
_PROFILES_DIR = os.path.join(_BASE_DIR, "user_profiles")
_LAST_USED_FILE = os.path.join(_PROFILES_DIR, ".last_used")


def _ensure_dirs():
    """Ensure required directories exist"""
    os.makedirs(_PRESETS_DIR, exist_ok=True)
    os.makedirs(_PROFILES_DIR, exist_ok=True)


# ============ Preset Management ============

def list_presets() -> List[str]:
    """List built-in preset names (without .json suffix)"""
    _ensure_dirs()
    names = []
    for f in sorted(os.listdir(_PRESETS_DIR)):
        if f.endswith(".json"):
            names.append(f[:-5])
    return names


def load_preset(name: str) -> dict:
    """Load a built-in preset from presets/, returning a PresetConfig-format dict"""
    path = os.path.join(_PRESETS_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Preset not found: {name} (searched path: {path})")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============ User Profile Management ============

def list_profiles() -> List[str]:
    """List user-saved profile names (without .json suffix)"""
    _ensure_dirs()
    names = []
    for f in sorted(os.listdir(_PROFILES_DIR)):
        if f.endswith(".json") and not f.startswith("."):
            names.append(f[:-5])
    return names


def save_profile(name: str, config: dict):
    """Save configuration to user_profiles/"""
    _ensure_dirs()
    # Ensure the config has a name field
    config["name"] = name
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_profile(name: str) -> dict:
    """Load a user profile from user_profiles/"""
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"User profile not found: {name} (searched path: {path})")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_profile(name: str):
    """Delete a user profile"""
    path = os.path.join(_PROFILES_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
    # If deleting the last-used profile, clear the record too
    last = get_last_used()
    if last == name:
        set_last_used("")


# ============ Import / Export ============

def export_config(config: dict) -> str:
    """Export configuration as a JSON string"""
    return json.dumps(config, ensure_ascii=False, indent=2)


def import_config(json_str: str) -> dict:
    """Import configuration from a JSON string, with basic validation"""
    config = json.loads(json_str)
    # Basic validation: must have at least name and departments
    if "name" not in config:
        raise ValueError("Config missing 'name' field")
    if "departments" not in config:
        raise ValueError("Config missing 'departments' field")
    return config


# ============ Last-Used Record ============

def get_last_used() -> str:
    """Get the name of the last-used configuration"""
    if os.path.exists(_LAST_USED_FILE):
        with open(_LAST_USED_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def set_last_used(name: str):
    """Record the name of the last-used configuration"""
    _ensure_dirs()
    with open(_LAST_USED_FILE, "w", encoding="utf-8") as f:
        f.write(name)


# ============ Configuration Validation ============

def validate_config(config: dict) -> List[str]:
    """
    Validate PresetConfig format, returning a list of errors (empty = valid).
    Items that are not errors but could be improved are returned as warnings.
    """
    errors = []
    
    if "name" not in config:
        errors.append("Missing 'name' field")
    if "departments" not in config:
        errors.append("Missing 'departments' field")
    elif not isinstance(config["departments"], dict):
        errors.append("'departments' must be a dict")
    else:
        for dept_key, dept in config["departments"].items():
            if "debaters" not in dept:
                errors.append(f"Department '{dept_key}' missing 'debaters' field")
            elif not isinstance(dept["debaters"], dict):
                errors.append(f"Department '{dept_key}' 'debaters' must be a dict")
            else:
                for debater_key, debater in dept["debaters"].items():
                    if "zh_style" not in debater and "en_style" not in debater:
                        errors.append(f"Department '{dept_key}' debater '{debater_key}' missing style description")
    
    return errors


# ============ Config Merge / Patch ============

def merge_skill_injection(config: dict, skill_markdown: str, target_departments: List[str] = None) -> dict:
    """
    Append skill-injected markdown content to all debater prompts in specified departments.
    
    Args:
        config: Original PresetConfig
        skill_markdown: Markdown content to inject
        target_departments: Target department list; None = all departments
    
    Returns:
        Modified PresetConfig (deep copy)
    """
    import copy
    result = copy.deepcopy(config)
    
    injection_zh = f"\n\n[Skill Injection]\n{skill_markdown}"
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
