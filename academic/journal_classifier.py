"""
Journal Quality Classifier — Consensus Pipeline v4.3

Supports two modes:
1. Local hardcoded registry (default, zero-config)
2. easyScholar API (free, covers 30+ ranking systems, requires registration key)

Register at: https://www.easyscholar.cc → User Center → Open API
"""
import os
import json
import requests
from typing import Dict, Any, Optional, List
from functools import lru_cache

from .journal_registry import JOURNAL_QUALITY_REGISTRY


# ============================================================
# easyScholar API Configuration
# ============================================================
EASYSCHOLAR_API_URL = "https://www.easyscholar.cc/open/getPublicationRank"
EASYSCHOLAR_SECRET_KEY = os.environ.get("EASYSCHOLAR_SECRET_KEY", "")


def _level_from_easyscholar(rank_data: Dict) -> str:
    """
    Infer S/A/B/C/D tier from easyScholar response data.

    Rules:
    - SCI/SSCI Q1 + IF>=5 → S
    - SCI/SSCI Q1 or CAS Tier 1 → A
    - CSSCI/CSCD or CAS Tier 2 → B
    - Other ranking data present → C
    - No data → D
    """
    if not rank_data:
        return "D"

    official = rank_data.get("officialRank", {}).get("all", {})
    if not official:
        # customRank may be dict or list; handle both formats
        custom = rank_data.get("customRank", {})
        if isinstance(custom, dict):
            official = custom.get("all", {})
        elif isinstance(custom, list) and custom:
            official = custom[0].get("all", {}) if isinstance(custom[0], dict) else {}
        if not official:
            return "D"

    sci_jcr = official.get("sci", "") or official.get("ssci", "") or ""
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

    if cas_warning and cas_warning != "无":  # "无" = "none" in easyScholar API response; must keep Chinese
        return "D"

    if "Q1" in str(sci_jcr) and sci_if >= 5.0:
        return "S"
    if "1区" in str(cas_upgrade):  # "1区" = CAS Tier 1 in easyScholar API response; must keep Chinese
        return "S"
    if "Q1" in str(sci_jcr) or "2区" in str(cas_upgrade):  # "2区" = CAS Tier 2 in easyScholar API response
        return "A"
    if cssci or cscd or "Q2" in str(sci_jcr):
        return "B"
    if sci_jcr or cas_upgrade or sci_if > 0:
        return "C"

    return "D"


@lru_cache(maxsize=500)
def query_easyscholar(journal_name: str) -> Optional[Dict[str, Any]]:
    """Query journal ranking via the easyScholar API."""
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
    Enhanced journal classification: local registry → easyScholar API → default rules.

    v4.3: Fixed fuzzy matching — exact match first; substring match only triggers when
    the shorter string length is >= 80% of the longer one.

    Args:
        journal_name: Journal name
        use_easyscholar: Whether to try the easyScholar API

    Returns:
        {"level": "S/A/B/C/D", "if_2026": float|None, "jcr": str, "note": str, "source": "local/api/fallback"}
    """
    normalized = journal_name.lower().strip().replace(".", "").replace(",", "")

    # 1. Local registry — exact match first
    for key, val in JOURNAL_QUALITY_REGISTRY.items():
        key_norm = key.lower().strip().replace(".", "").replace(",", "")
        if normalized == key_norm:
            return {**val, "source": "local"}

    # Substring match — only triggers when shorter string length >= 80% of longer string
    # Avoid "Energy" matching all journals containing "Energy"
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
            official = api_data.get("officialRank", {}).get("all") or {}

            sci_if = None
            try:
                if_str = official.get("sciif", "") or ""
                sci_if = float(if_str) if if_str else None
            except (ValueError, TypeError):
                pass

            jcr_parts = []
            if official.get("sci"):
                jcr_parts.append(f"JCR {official['sci']}")
            if official.get("ssci"):
                jcr_parts.append(f"SSCI {official['ssci']}")
            if official.get("sciUp"):
                jcr_parts.append(f"CAS {official['sciUp']}")
            if official.get("cssci"):
                jcr_parts.append("CSSCI")
            if official.get("cscd"):
                jcr_parts.append("CSCD")

            return {
                "level": level,
                "if_2026": sci_if,
                "jcr": " / ".join(jcr_parts) if jcr_parts else "API query",
                "note": f"easyScholar query",
                "source": "api",
            }

    # 3. Default rules
    return {"level": "C", "if_2026": None, "jcr": "Unknown", "note": "Not in registry and API not queried", "source": "fallback"}


def batch_classify_journals(
    journal_names: List[str],
    use_easyscholar: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Batch-query journal rankings."""
    results = {}
    for name in journal_names:
        results[name] = classify_journal_enhanced(name, use_easyscholar=use_easyscholar)
    return results
