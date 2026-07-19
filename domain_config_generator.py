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

    Calls the LLM with the topic, returning a JSON containing:
    - domain_definition: Domain boundary description
    - exclusion_signals: Exclusion signal word list
    - query_rotation: Search query rotation list
    - tier_definitions: core/method/background tier definitions
    - llm_classify_prompt: LLM binary classification prompt template
    - categorization_schema: Auto-generated classification dimensions, buckets, and keywords

    Args:
        topic: Research topic (e.g., "Machine Learning in Energy Economics")
        llm_call_fn: LLM call function (system_prompt, user_message, temperature) -> str
        output_dir: Output directory for saving domain_config.json

    Returns:
        Domain configuration dict
    """
    system_prompt = """You are an academic domain analysis expert. Your task is to generate a precise domain configuration JSON based on the given research topic.

This configuration will be used for automatic filtering in an academic literature research pipeline. It must be precise enough to exclude irrelevant papers, yet broad enough not to miss relevant ones.

You must output a valid JSON object containing the following fields:

1. "domain_definition": A domain boundary description within 100 words, clarifying the core research objects and methodological scope of this domain.

2. "exclusion_signals": A list of strings (15-25 items) containing exclusion signal words that do not belong to this domain.
   When these words appear, the paper is likely outside the target domain. For example:
   - If researching ML applications in energy economics, exclusion signals should include: nanotube, nanowire, plant growth, 
     bacterial, photosynthesis, drug discovery, clinical trial, genetic, 
     semiconductor device, quantum computing, astrophysics, etc.
   - Must cover common cross-domain noise sources: materials science, biology, medicine, pure chemistry, pure physics, etc.
   - Must also cover non-hard-science noise: education/teaching (curriculum, pedagogy, course design, textbook, teaching, education, 教学, 课程, 教育), nutrition/dietary (obesity, dietary, calorie, nutrition), book reviews

3. "query_rotation": A list of strings (6-10 items) for search query rotation.
   CRITICAL CONSTRAINTS:
   - Each query MUST be a DISTINCT keyword phrase of 4-8 words, NOT a copy of the original topic with appended suffixes.
   - FORBIDDEN: taking the full topic sentence and adding "review survey" / "methodology comparison" / "recent advances" at the end. This produces garbage results.
   - Each query must target a DIFFERENT retrieval angle. Examples of angles:
     (1) Core phenomenon: "environmental regulation carbon emission causal effect"
     (2) Specific methodology: "difference-in-differences carbon policy evaluation"
     (3) Policy instrument: "emission trading scheme causal inference"
     (4) Estimation strategy: "carbon tax instrumental variable estimation"
     (5) Theoretical framework: "Porter hypothesis environmental regulation productivity"
     (6) Heterogeneity analysis: "environmental regulation energy efficiency heterogeneity"
     (7) Data/measurement angle: "energy intensity convergence panel data"
     (8) Synonym variant: "pollution haven hypothesis empirical evidence"
   - GOOD: "difference-in-differences carbon policy evaluation" (distinct angle, keyword-based)
   - BAD: "Causal Effects of Environmental Regulations on Carbon Emissions: DID and IV Evidence review survey" (copy + suffix)

4. "tier_definitions": An object containing three tier definitions:
   - "core": The most central papers in this domain (directly researching the topic + methodology)
     - "keywords": Keyword list (10-15 items)
     - "description": Tier description
   - "method": Methodology supplement tier (the researched methods have applications in the target domain, but the paper itself may be from other domains)
     - "keywords": Keyword list (8-12 items)
     - "description": Tier description
   - "background": Mechanism background tier (provides domain background knowledge, but does not directly involve methodological innovation)
     - "keywords": Keyword list (8-12 items)
     - "description": Tier description

5. "llm_classify_prompt": A string that is the system prompt template for LLM binary classification.
   Use {domain_definition} as a placeholder, which will be replaced with the actual domain_definition at runtime.
   The prompt asks the LLM to answer "yes" or "no" for each paper — does this paper belong to the target domain?
   Format requirement: output "Paper N: Yes/No" for each paper, with a brief reason.

6. "categorization_schema": An object defining classification dimensions for topic clustering.
   This replaces hardcoded category maps, enabling domain-agnostic paper categorization.
   Structure:
   {
     "research_area": {
       "Category1": ["keyword1", "keyword2", ...],
       "Category2": ["keyword3", ...],
       "Other": []
     },
     "methodology": {
       "Category1": ["keyword1", ...],
       "Category2": ["keyword2", ...],
       "Other": []
     },
     "data_type": {
       "Category1": ["keyword1", ...],
       "Other": []
     },
     "geographic_scope": {
       "Category1": ["keyword1", ...],
       "Other": []
     }
   }
   Requirements:
   - Must include exactly these 4 dimensions: research_area, methodology, data_type, geographic_scope
   - Each dimension must have 3-5 meaningful categories (plus "Other" as fallback)
   - Each category must have 3-8 lowercase English keywords (and optionally Chinese equivalents for matching Chinese papers)
   - Categories and keywords must be SPECIFIC to the research topic — do NOT use generic placeholders
   - The "Other" bucket must always exist with an empty keyword list []

Important:
- Output only JSON, no other text
- Ensure the JSON is valid and parseable
- Use English lowercase for keywords
- Exclusion signals should cover common noise domains including education/teaching and nutrition/dietary noise
- categorization_schema must be topic-specific, not generic
- CONCISENESS REQUIREMENT: Keep the JSON concise. categorization_schema should have at most 3 categories per dimension (plus "Other") with 3-5 keywords each. llm_classify_prompt should be under 500 characters. Total output must not exceed 12000 characters."""

    user_msg = f"Research topic: {topic}\n\nPlease generate the precise domain configuration JSON."

    try:
        response = llm_call_fn(system_prompt, user_msg, temperature=0.2)
    except Exception as e:
        # LLM call failed, return default config
        return _default_domain_config(topic)

    if not response:
        return _default_domain_config(topic)

    # Extract JSON from response
    config = _extract_json(response)

    if not config:
        return _default_domain_config(topic)

    # Validate required fields
    required_fields = ["domain_definition", "exclusion_signals", "query_rotation",
                       "tier_definitions", "llm_classify_prompt", "categorization_schema"]
    for field in required_fields:
        if field not in config:
            config[field] = _default_domain_config(topic).get(field, "")

    # Ensure tier_definitions structure is complete
    if "tier_definitions" in config:
        for tier in ["core", "method", "background"]:
            if tier not in config["tier_definitions"]:
                config["tier_definitions"][tier] = {
                    "keywords": [],
                    "description": f"{tier} layer"
                }
            elif "keywords" not in config["tier_definitions"][tier]:
                config["tier_definitions"][tier]["keywords"] = []

    # Validate categorization_schema structure
    required_dims = ["research_area", "methodology", "data_type", "geographic_scope"]
    if "categorization_schema" not in config or not isinstance(config["categorization_schema"], dict):
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
