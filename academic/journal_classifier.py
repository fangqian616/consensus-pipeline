"""
期刊质量查询器 — Consensus Pipeline v4.3

支持两种模式：
1. 本地硬编码注册表（默认，零配置）
2. easyScholar API（免费，覆盖30+分级体系，需注册获取密钥）

注册地址：https://www.easyscholar.cc → 用户中心 → 开放接口

v4.3: 修复循环导入（改从journal_registry导入）、修复模糊匹配过于激进
"""
import os
import json
import requests
from typing import Dict, Any, Optional, List
from functools import lru_cache

from .journal_registry import JOURNAL_QUALITY_REGISTRY


# ============================================================
# easyScholar API 配置
# ============================================================
EASYSCHOLAR_API_URL = "https://www.easyscholar.cc/open/getPublicationRank"
EASYSCHOLAR_SECRET_KEY = os.environ.get("EASYSCHOLAR_SECRET_KEY", "")


def _level_from_easyscholar(rank_data: Dict) -> str:
    """
    从easyScholar返回数据推断S/A/B/C/D等级。

    规则：
    - SCI/SSCI Q1 + IF>=5 → S
    - SCI/SSCI Q1 或 中科院1区 → A
    - CSSCI/CSCD 或 中科院2区 → B
    - 其他有等级数据 → C
    - 无数据 → D
    """
    if not rank_data:
        return "D"

    official = rank_data.get("officialRank", {}).get("all", {})
    if not official:
        custom = rank_data.get("customRank", [])
        if custom:
            official = custom[0].get("all", {}) if custom else {}
        if not official:
            return "D"

    sci_jcr = official.get("sci", "")
    cas_upgrade = official.get("sciUp", "")
    sci_if_str = official.get("sciif", "")
    sci_if = 0.0
    try:
        sci_if = float(sci_if_str) if sci_if_str else 0.0
    except (ValueError, TypeError):
        pass
    cssci = official.get("cssci", "")
    cscd = official.get("cscd", "")
    cas_warning = official.get("sciwarn", "")

    if cas_warning and cas_warning != "无":
        return "D"

    if "Q1" in str(sci_jcr) and sci_if >= 5.0:
        return "S"
    if "1区" in str(cas_upgrade):
        return "S"
    if "Q1" in str(sci_jcr) or "2区" in str(cas_upgrade):
        return "A"
    if cssci or cscd or "Q2" in str(sci_jcr):
        return "B"
    if sci_jcr or cas_upgrade or sci_if > 0:
        return "C"

    return "D"


@lru_cache(maxsize=500)
def query_easyscholar(journal_name: str) -> Optional[Dict[str, Any]]:
    """通过easyScholar API查询期刊等级。"""
    if not EASYSCHOLAR_SECRET_KEY:
        return None

    try:
        params = {
            "secretKey": EASYSCHOLAR_SECRET_KEY,
            "publicationName": journal_name,
        }
        resp = requests.get(EASYSCHOLAR_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") == 200:
            return data.get("data")
        else:
            return None
    except Exception:
        return None


def classify_journal_enhanced(
    journal_name: str,
    use_easyscholar: bool = True,
) -> Dict[str, Any]:
    """
    增强版期刊分级：本地注册表 → easyScholar API → 默认规则。

    v4.3: 修复模糊匹配 — 精确优先，子串匹配仅当长度比例>=80%时才触发

    Args:
        journal_name: 期刊名称
        use_easyscholar: 是否尝试easyScholar API

    Returns:
        {"level": "S/A/B/C/D", "if_2026": float|None, "jcr": str, "note": str, "source": "local/api/fallback"}
    """
    normalized = journal_name.lower().strip().replace(".", "").replace(",", "")

    # 1. 本地注册表 — 精确匹配优先
    for key, val in JOURNAL_QUALITY_REGISTRY.items():
        key_norm = key.lower().strip().replace(".", "").replace(",", "")
        if normalized == key_norm:
            return {**val, "source": "local"}

    # 子串匹配 — 仅当较短的字符串长度 >= 较长字符串的80%时才触发
    # 避免"Energy"匹配到所有含Energy的期刊
    for key, val in JOURNAL_QUALITY_REGISTRY.items():
        key_norm = key.lower().strip().replace(".", "").replace(",", "")
        shorter = min(len(normalized), len(key_norm))
        longer = max(len(normalized), len(key_norm))
        if longer == 0:
            continue
        if shorter / longer >= 0.8:
            if normalized in key_norm or key_norm in normalized:
                return {**val, "source": "local"}

    # 2. easyScholar API
    if use_easyscholar and EASYSCHOLAR_SECRET_KEY:
        api_data = query_easyscholar(journal_name)
        if api_data:
            level = _level_from_easyscholar(api_data)
            official = api_data.get("officialRank", {}).get("all", {})

            sci_if = None
            try:
                if_str = official.get("sciif", "")
                sci_if = float(if_str) if if_str else None
            except (ValueError, TypeError):
                pass

            jcr_parts = []
            if official.get("sci"):
                jcr_parts.append(f"JCR {official['sci']}")
            if official.get("sciUp"):
                jcr_parts.append(f"中科院{official['sciUp']}")
            if official.get("cssci"):
                jcr_parts.append("CSSCI")
            if official.get("cscd"):
                jcr_parts.append("CSCD")

            return {
                "level": level,
                "if_2026": sci_if,
                "jcr": " / ".join(jcr_parts) if jcr_parts else "API查询",
                "note": f"easyScholar查询",
                "source": "api",
            }

    # 3. 默认规则
    return {"level": "C", "if_2026": None, "jcr": "未知", "note": "未在注册表中且未查询API", "source": "fallback"}


def batch_classify_journals(
    journal_names: List[str],
    use_easyscholar: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """批量查询期刊等级。"""
    results = {}
    for name in journal_names:
        results[name] = classify_journal_enhanced(name, use_easyscholar=use_easyscholar)
    return results
