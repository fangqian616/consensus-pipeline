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
