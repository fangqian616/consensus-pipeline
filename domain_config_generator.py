#!/usr/bin/env python3
"""
Domain Configuration Generator — Consensus Pipeline v0.7.0

Dynamically generates domain configuration based on research topic, ensuring pipeline generality.
No more hardcoded domain-specific keywords (e.g., exclusion signals, energy keywords).
Instead, the LLM dynamically generates exclusion_signals, query_rotation, tier_definitions, etc.
"""
import json
import os
from typing import Dict, Any, Callable


def generate_domain_config(topic: str, llm_call_fn: Callable, output_dir: str = "") -> Dict[str, Any]:
    """
    Dynamically generate domain configuration based on research topic.

    Uses TWO LLM calls to avoid max_tokens overflow:
    1. First call: generates domain_definition, exclusion_signals, query_rotation,
       tier_definitions, llm_classify_prompt (compact, ~8192 tokens safe)
    2. Second call: generates categorization_schema separately (tightly constrained,
       ≤3 categories per dimension, 3-5 keywords each, ≤8000 chars)

    Args:
        topic: Research topic (e.g., "Machine Learning in Energy Economics")
        llm_call_fn: LLM call function (system_prompt, user_message, temperature) -> str
        output_dir: Output directory for saving domain_config.json

    Returns:
        Domain configuration dict
    """
    # ========== First Call: Core Config (domain_definition, exclusion_signals, etc.) ==========
    core_config = _generate_core_config(topic, llm_call_fn)
    if not core_config:
        return _default_domain_config(topic)

    # ========== Second Call: categorization_schema (tightly constrained) ==========
    categorization_schema = _generate_categorization_schema(topic, llm_call_fn)
    if not categorization_schema:
        categorization_schema = _default_categorization_schema(topic)

    # Merge
    config = {**core_config, "categorization_schema": categorization_schema}

    # Validate required fields
    required_fields = ["domain_definition", "exclusion_signals", "query_rotation",
                       "tier_definitions", "llm_classify_prompt", "categorization_schema"]
    for field in required_fields:
        if field not in config:
            config[field] = _default_domain_config(topic).get(field, "")

    # Ensure tier_definitions structure is complete
    if "tier_definitions" in config:
        if not isinstance(config["tier_definitions"], dict):
            config["tier_definitions"] = _default_domain_config(topic).get("tier_definitions", {})
        for tier in ["core", "method", "background"]:
            if tier not in config["tier_definitions"]:
                config["tier_definitions"][tier] = {
                    "keywords": [],
                    "description": f"{tier} layer"
                }
            elif not isinstance(config["tier_definitions"][tier], dict):
                config["tier_definitions"][tier] = {
                    "keywords": [],
                    "description": f"{tier} layer"
                }
            elif "keywords" not in config["tier_definitions"][tier]:
                config["tier_definitions"][tier]["keywords"] = []

    # Validate categorization_schema structure
    required_dims = ["research_area", "methodology", "data_type", "geographic_scope"]
    if not isinstance(config.get("categorization_schema"), dict):
        config["categorization_schema"] = _default_categorization_schema(topic)
    else:
        for dim in required_dims:
            if dim not in config["categorization_schema"]:
                config["categorization_schema"][dim] = {"Other": []}
            elif not isinstance(config["categorization_schema"][dim], dict):
                config["categorization_schema"][dim] = {"Other": []}

    # Save to file
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, "domain_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    return config



def _generate_core_config(topic: str, llm_call_fn: Callable) -> Dict[str, Any]:
    """First LLM call: generate core config (domain_definition, exclusion_signals, etc.)

    These fields stay compact — no risk of max_tokens overflow.
    """
    system_prompt = """You are an academic domain analysis expert. Generate a precise domain configuration JSON for a literature research pipeline.

Output a valid JSON object with these fields ONLY:

1. "domain_definition": ≤100 words. Clarify the core research objects and methodological scope.

2. "exclusion_signals": 15-25 strings. Words that signal a paper is OUTSIDE the target domain.
   Must cover common noise: materials science, biology, medicine, pure chemistry, pure physics, etc.
   Must also cover non-hard-science noise: education/teaching (curriculum, pedagogy, course design, textbook, 教学, 课程, 教育), nutrition/dietary (obesity, dietary, calorie, nutrition), book reviews.

3. "query_rotation": 6-10 strings. CRITICAL: Each query MUST be a DISTINCT keyword phrase of 4-8 words.
   FORBIDDEN: copying the full topic and appending "review survey" / "methodology comparison" / "recent advances".
   Each query must target a DIFFERENT angle: core phenomenon, specific methodology, policy instrument,
   estimation strategy, theoretical framework, heterogeneity analysis, data/measurement, synonym variant.

4. "tier_definitions": Object with three tiers:
   - "core": 10-15 keywords, key papers directly on topic+methodology
   - "method": 8-12 keywords, methodology papers applicable to domain
   - "background": 8-12 keywords, domain background knowledge

5. "llm_classify_prompt": System prompt template for binary paper classification.
   Use {domain_definition} placeholder. Must ask LLM to output "Paper N: Yes/No — reason".

Rules:
- Output ONLY JSON, no other text
- All keywords in English lowercase
- Keep the entire JSON under 4000 characters"""

    user_msg = f"Research topic: {topic}\n\nGenerate the core domain configuration JSON (domain_definition, exclusion_signals, query_rotation, tier_definitions, llm_classify_prompt). Do NOT include categorization_schema."

    try:
        response = llm_call_fn(system_prompt, user_msg, temperature=0.2)
    except Exception:
        return {}

    if not response:
        return {}

    return _extract_json(response)


def _generate_categorization_schema(topic: str, llm_call_fn: Callable) -> Dict[str, Any]:
    """Second LLM call: generate categorization_schema separately.

    Tightly constrained to avoid the max_tokens overflow that occurred when
    the LLM generated dozens of redundant keywords.

    Constraints:
    - 4 dimensions: research_area, methodology, data_type, geographic_scope
    - ≤3 meaningful categories + "Other" per dimension (max 4 total per dim)
    - 3-5 lowercase English keywords per category (NO more than 5!)
    - Entire JSON ≤2500 characters
    """
    system_prompt = """You are an academic taxonomy designer. Generate a categorization schema for classifying research papers.

Output ONLY this JSON structure (nothing else):
{
  "research_area": { "Category1": ["kw1","kw2","kw3"], "Category2": ["kw1","kw2","kw3"], "Other": [] },
  "methodology":   { "Category1": ["kw1","kw2","kw3"], "Category2": ["kw1","kw2","kw3"], "Other": [] },
  "data_type":     { "Category1": ["kw1","kw2","kw3"], "Category2": ["kw1","kw2","kw3"], "Other": [] },
  "geographic_scope": { "Category1": ["kw1","kw2","kw3"], "Category2": ["kw1","kw2","kw3"], "Other": [] }
}

CRITICAL RULES — violation will cause pipeline failure:
1. Each dimension: 2-3 meaningful categories + "Other" (max 4 entries per dim). NO MORE.
2. Each category: 3-5 lowercase English keywords. NO MORE THAN 5. NEVER use 6+.
3. Keywords must be TOPIC-SPECIFIC, not generic. "sustainability" is OK but do NOT spawn
   variants like "sustainability_value", "sustainability_ethics", "sustainability_justice",
   "sustainability_equity", "sustainability_fairness", "sustainability_inclusion"...
   Choose ONE keyword ("sustainability") and STOP.
4. "Other" must always have an empty list [].
5. Entire JSON must be ≤2500 characters. Be concise.
6. Output ONLY the JSON, no markdown, no explanation."""

    user_msg = (f"Research topic: {topic}\n\n"
                "Generate the categorization_schema JSON. "
                "Remember: ≤3 categories per dimension, 3-5 keywords each, "
                "≤2500 chars total. Do NOT generate keyword variants — pick ONE representative keyword per concept.")

    try:
        response = llm_call_fn(system_prompt, user_msg, temperature=0.2)
    except Exception:
        return {}

    if not response:
        return {}

    schema = _extract_json(response)

    # Post-validate: strip excessive keywords per category
    if isinstance(schema, dict):
        for dim in schema:
            if isinstance(schema[dim], dict):
                for cat in schema[dim]:
                    if isinstance(schema[dim][cat], list) and len(schema[dim][cat]) > 5:
                        schema[dim][cat] = schema[dim][cat][:5]

    return schema

def _default_categorization_schema(topic: str) -> Dict[str, Any]:
    """Default categorization schema (fallback when LLM generation fails)"""
    topic_lower = topic.lower()
    return {
        "research_area": {
            "Primary": [topic_lower.split()[0]] if topic_lower else ["research"],
            "Related": [w for w in topic_lower.split()[:3]] if len(topic_lower.split()) > 1 else [],
            "Other": [],
        },
        "methodology": {
            "Empirical": ["empirical", "quantitative", "statistical"],
            "Computational": ["simulation", "computational", "modeling"],
            "Review": ["review", "meta-analysis", "survey"],
            "Other": [],
        },
        "data_type": {
            "Quantitative": ["quantitative", "numerical", "statistical"],
            "Qualitative": ["qualitative", "interview", "case study"],
            "Mixed": ["mixed methods", "triangulation"],
            "Other": [],
        },
        "geographic_scope": {
            "Global": ["global", "worldwide", "international"],
            "Regional": ["regional", "cross-country", "multi-country"],
            "National": ["national", "country-specific"],
            "Other": [],
        },
    }


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON object from text"""
    import re

    # Attempt 1: parse as-is
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: extract ```json ... ``` code block
    pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Attempt 3: find first { to last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def _default_domain_config(topic: str) -> Dict[str, Any]:
    """Default domain configuration (fallback when LLM call fails)"""
    return {
        "domain_definition": f"Academic research on {topic}",
        "exclusion_signals": [
            "nanotube", "nanowire", "photosynthesis", "bacterial",
            "drug discovery", "clinical trial", "genetic mutation",
            "curriculum", "pedagogy", "course design", "textbook", "teaching",
            "obesity", "dietary", "calorie", "nutrition", "book review",
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
                "description": f"Papers directly researching {topic}"
            },
            "method": {
                "keywords": [],
                "description": "Methodology-related but possibly outside the target domain"
            },
            "background": {
                "keywords": [],
                "description": "Domain background knowledge papers"
            }
        },
        "llm_classify_prompt": f"""You are an academic domain classification expert. Your task is to determine whether papers belong to the following research domain: {topic}

For each paper, determine whether it belongs to this domain. Output format:
Paper N: Yes/No — Brief reason

Criteria:
- "Yes": The paper's research topic or methodology is directly related to "{topic}"
- "No": The paper does not involve this domain at all (e.g., belongs to unrelated fields like materials science, biology, medicine, etc.)

Please strictly follow the output format.""",
        "categorization_schema": _default_categorization_schema(topic),
    }
