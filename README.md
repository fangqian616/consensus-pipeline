# 🧠 Consensus Pipeline

<p align="center">
  <img src="banner.png" alt="Consensus Pipeline" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Latest-v0.7.0-brightgreen" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

> **Multi-agent debate framework for structured content generation.**
> Instead of one AI writing for you — an AI team debates, collides, and reaches consensus.

📖 [中文文档](README_CN.md) · 📦 [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases)

---

## 🎯 What Does It Do?

Consensus Pipeline replaces single-AI generation with **structured multi-agent debate**. Different AI "departments" argue from their professional perspectives, challenge each other's assumptions, and converge on a high-quality consensus output.

**Two pipelines, one framework:**

| | 🔬 Academic Pipeline | 🎬 Creative Pipeline |
|---|---|---|
| **Input** | A research topic | A script / story |
| **Process** | Search → QC → Debate → Review | 8-dept debate → Storyboard → Video prompts |
| **Output** | Literature review + paper metadata | 9-grid storyboard + per-shot video prompts |
| **Maturity** | ✅ v0.7.0 — production-ready | 🔄 v3.0 — actively iterating |
| **Best for** | Researchers, students, analysts | Animators, content creators |

---

## 🆕 What's New in v0.7.0

| Feature | Description |
|---------|-------------|
| **🔬 QC Department** | 3-layer filter: hard filter → LLM classify → layer tagging. Reduced 219 retrieved papers to 77 relevant ones (64% exclusion rate) |
| **⚙️ Dynamic Domain Config** | LLM generates domain-specific exclusion signals, query rotation, and tier definitions — zero hardcoding, change topic without code changes |
| **🔗 Citation Validation** | Auto-verify all `[N]` references against CSV; remove dangling citations |
| **📊 Confidence Annotation** | Every conclusion tagged with `(N/M papers, confidence level)` — no more unsupported claims |
| **🔧 OpenAlex Priority** | Abstract backfill uses OpenAlex first (no 429 rate limits), falls back to Semantic Scholar |

### v0.7.0 vs v5.1.8

| Metric | v5.1.8 | v0.7.0 |
|--------|:------:|:----:|
| Off-topic papers in output | 49/56 (88%) | 0/77 (0%) |
| "See [N]" placeholder citations | Multiple | 0 |
| Dangling references | Present | 0 |
| Confidence annotations | 0 | 15 |
| Domain switchability | Hardcoded | Dynamic |
| Self-evaluation | 4.8/10 | 7.4/10 |

Full changelog: [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases)

---

## 🏗️ Architecture

### Academic Pipeline (v0.7.0)

```
Research Topic
     │
     ▼
┌─────────────────────────┐
│ Phase 0.5: Domain Config │  ← LLM generates exclusion signals, query terms, tier rules
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 1: Multi-source   │  ← OpenAlex (primary) + Semantic Scholar + arXiv
│ Paper Retrieval         │     Deduplication, abstract backfill
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 3.5: QC Department│  ← 3-layer sieve:
│ Quality Control         │     hard_filter → LLM_classify → tag_layer
│ (NEW in v0.7.0)           │     219 papers → 77 relevant (core/method/background)
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 4: Department     │  ← 11 research departments debate
│ Debate (serial)         │     Each dept: 3-4 debaters → consensus
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 5: Cross-Dept     │  ← Resolve contradictions between departments
│ Debate                  │
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 7: Report         │  ← Literature review with confidence annotations
│ Generation              │     Citation validation, PDF/DOCX export
└─────────────────────────┘
```

### Creative Pipeline (v3.0)

```
Script / Story
     │
     ▼
┌──────────────────────────────────────────┐
│ 8 Creative Departments (serial debate)    │
│ Screenwriter → Spatial → Storyboard → DP │
│ → Lighting → VFX → Sound → Editing       │
│ Each dept: 3 debaters → consensus        │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│ Cross-Department Debate                   │
│ 8 groups resolve spatial/story conflicts  │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│ Output                                    │
│ 📐 9-grid storyboard (for image AI)      │
│ 🎬 Per-shot video prompts (for video AI) │
└──────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/fangqian616/consensus-pipeline.git
cd consensus-pipeline
pip install -r requirements.txt
streamlit run app.py
```

### Academic Pipeline (CLI)

```bash
# Set your DeepSeek API key
export DEEPSEEK_API_KEY=your_key_here

# Run the full pipeline
python run_pipeline.py --topic "Machine Learning in Energy Economics"
```

### Academic Pipeline (Streamlit)

1. Configure API key in sidebar
2. Enter your research topic
3. AI generates domain config → confirm
4. Watch papers retrieved, filtered, debated
5. Get your literature review with confidence annotations

### Creative Pipeline

1. Select "Animation Mode" in sidebar
2. Enter your script
3. AI auto-configures 8 departments
4. Watch departments debate in real-time
5. Export 9-grid storyboard + video prompts

---

## 🔬 Academic Pipeline Details

### 11 Research Departments

| Department | Role |
|-----------|------|
| Literature Search | Multi-source retrieval (OpenAlex, Semantic Scholar, arXiv), deduplication |
| Metadata Inspector | DOI verification, metadata completeness check |
| Citation Network | Citation analysis, impact metrics |
| Methodology Review | 7-dimension evaluation (accuracy, efficiency, interpretability...) |
| Data Validation | Data source quality, reproducibility assessment |
| Counter-Evidence | Anti-mainstream findings, controversy mapping |
| Topic Clustering | Thematic grouping, trend identification |
| Visualization | Chart & distribution analysis |
| Report Integration | Cross-validation, consensus building |
| **Programming** | Analyze mainstream models/tools, output runnable code |
| **Tutorial** | Teach how to use research tools & methods |

### QC Department (v0.7.0 New)

The biggest quality leap in v0.7.0. Three-layer filtering ensures zero pollution:

```
Input: 219 papers (from multi-source retrieval)
  │
  ├── Layer 1: Hard Filter (exclusion signals)
  │   → Removes obviously off-topic papers (e.g., carbon nanotube, botany)
  │   → Excluded: 5 papers
  │
  ├── Layer 2: LLM Classify (domain membership)
  │   → LLM judges each paper: "belongs to domain?" Yes/No
  │   → Excluded: 137 papers
  │
  └── Layer 3: Layer Tagging (importance tier)
      → core (68) / method (6) / background (3)
      → Final output: 77 papers

Exclusion rate: 64.8%
Off-topic rate in final output: 0%
```

### Dynamic Domain Config (v0.7.0 New)

No more hardcoded keywords. LLM generates everything based on your topic:

```json
{
  "domain_definition": "Application of ML methods to energy economics...",
  "exclusion_signals": ["carbon nanotube", "botany", "materials science"],
  "query_rotation": ["machine learning energy forecasting", "deep learning electricity pricing", ...],
  "tier_definitions": {"core": "...", "method": "...", "background": "..."},
  "llm_classify_prompt": "Given a paper with title and abstract..."
}
```

Change topic from "ML in Energy Economics" to "LLM in Healthcare"? Zero code changes.

### Confidence Annotation

Every conclusion in the report carries a confidence tag:

> Deep learning methods dominate short-term energy load forecasting **(42/77 papers, high confidence)**

> Graph neural networks show emerging potential in energy network optimization **(3/77 papers, low confidence — trend not established)**

No more unsupported claims.

---

## 🎬 Creative Pipeline Details

### 8 Creative Departments

| Department | Debaters | Focus |
|-----------|----------|-------|
| Screenwriter | Micro-expression / Body Language / Emotional Pacing / Narrative Architect | Character details, story beats, on-screen roster |
| Spatial | Scene Surveyor / Blocking Director / Spatial Logic | Layout, positioning, movement paths |
| Storyboard | Long Take / Montage / Impact Frame | Shot composition, 9-grid keyframes |
| Cinematography | Lens Realist / Light & Shadow / Motion Designer | Focal length, depth, camera movement |
| Lighting | Natural Light / Dramatic / Practical | Light sources, mood, contrast |
| VFX | Particle / Physics / Composite | Effects, destruction, energy |
| Sound | Ambience / Foley / Score-placeholder | Environmental audio, action sounds |
| Editing | Narrative Pace / Visual Continuity / Shot Integrity | Cut timing, segment splitting |

### Output Format (v3.1 Verified)

Each shot follows a proven template tested with real AI video generation:

```
SHOT 01 | Scene Name | 0-2s
Reference: 9-grid cell position
Camera: ...
Lighting: ...
Guide: ...
Subject: Character [Character Reference Sheet] + action description
Background: ...

Positive Prompt: (English, complete camera + scene + lighting + render description)
Audio: (Sound effects only, no BGM)
```

Key rules learned from iteration:
- **One action per shot** — no action arcs within a single shot
- **Absolute direction** — "facing carriage rear (sandworm approach)", never "facing camera"
- **Reference sheet notation** — `Character [Character Reference Sheet]` instead of describing appearance
- **Interior/Exterior separation** — A-line (inside) and B-line (outside) are separate files

---

## ✨ Core Features

### 🧠 AI Router — Smart Configuration
AI analyzes your needs → selects departments → configures debaters → generates presets. All editable.

### 🔄 Four Architecture Modes

| Mode | Mechanism | Quality | Speed | Best For |
|------|-----------|:-------:|:-----:|----------|
| **Consensus Pipeline** | Serial dept debate | ★★★★★ | ★★ | Maximum quality |
| **Market Simulation** | Competition + voting | ★★★★ | ★★ | Exploring directions |
| **Expert Pool** | 2/dept curated | ★★★ | ★★★ | Fast iteration |
| **Single Agent** | No debate | ★★ | ★★★★★ | Baseline comparison |

### 📦 Skill Injection
Upload proprietary knowledge (Markdown) → auto-injected into target department prompts.

### 🔍 Fact-Checking
Automated factual verification of report claims with source tracing.

---

## 🔧 Configuration

| Provider | API URL | Recommended Model |
|----------|--------|-------------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` or `deepseek-v4-pro` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Custom | Any OpenAI-compatible endpoint | Any model |

### Optional: easyScholar API

For enhanced journal ranking, get a key at [easyScholar](https://www.easyscholar.cc/):

```bash
# Set in Streamlit sidebar or environment variable
export EASYSCHOLAR_SECRET_KEY=your_key_here
```

Without easyScholar, the pipeline uses a local 209-journal registry as fallback.

### Environment Variables

```bash
DEEPSEEK_API_KEY=your_key          # Required for LLM calls
EASYSCHOLAR_SECRET_KEY=your_key    # Optional, for journal ranking
```

---

## 📁 Project Structure

```
consensus-pipeline/
├── app.py                       # Streamlit main app
├── router.py                    # AI Router — smart department config
├── debate_engine.py             # Core debate engine (v3.0)
├── config_manager.py            # Config persistence & presets
├── run_pipeline.py              # CLI runner for headless execution
├── quality_controller.py        # QC department (v0.7.0)
├── domain_config_generator.py   # Dynamic domain config (v0.7.0)
├── report_generator.py          # Report generation with confidence
├── docx_exporter.py             # Word export with table formatting
├── pdf_exporter.py              # PDF export with Chinese fonts
├── academic/                    # Academic research module
│   ├── search_engine.py         # Multi-source search (OpenAlex, SS, arXiv)
│   ├── journal_classifier.py   # 4-layer journal quality sieve + easyScholar
│   ├── journal_registry.py     # 209-journal local registry
│   ├── fact_checker.py         # Automated fact verification
│   └── __init__.py
├── requirement/                 # Requirement research module
│   ├── interviewer.py           # AI interview agent
│   ├── structurer.py            # Scope & constraint extraction
│   ├── generator.py             # Requirement document generation
│   ├── validator.py             # Completeness check
│   └── __init__.py
├── templates/                   # Debate prompt templates
├── presets/                     # Built-in presets
└── fonts/                       # Chinese fonts (LXGW WenKai)
```

---

## 🗺️ Version History

| Version | Date | Changes |
|---------|------|---------|
| **v0.7.0** | 2026-07-17 | QC department, dynamic domain config, citation validation, confidence annotation, OpenAlex priority |
| v5.1.8-fix2 | 2026-07-16 | Reference section regex fix, carbon keyword filter |
| v5.1.8 | 2026-07-15 | "See [N]" prefix ban, out-of-scope citation removal |
| v5.1.7 | 2026-07-15 | Abstract backfill, OpenAlex integration |
| v5.1 | 2026-07-15 | Dual-template report, 4th relevance filter, 209-journal registry |
| v5.0 | 2026-07-15 | easyScholar API integration |
| v4.0 | 2026-07-15 | Requirement research, academic mode, programming & tutorial depts |
| v3.0 | 2026-07-14 | AI Router, user-editable prompts, local persistence, Skill injection |

All versions available as [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases).

---

## 🗺️ Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| P0 | Report segment generation (plan-then-generate) | Planned |
| P0 | QC false-positive reverse validation | Planned |
| P1 | Semantic citation verification (embedding-based) | Planned |
| P1 | Sub-topic query splitting | Planned |
| P1 | Publication bias detection (funnel plot) | Planned |
| P2 | Cross-language retrieval (CNKI + bilingual alignment) | Planned |
| P2 | Incremental update capability | Planned |

---

## 🤝 Contributing

PRs welcome! Especially:
- 🎨 **New preset templates** — product design, novel writing, game levels…
- 🎭 **New debater styles** — diverse perspectives for existing departments
- 🛠️ **New departments** — what's missing?
- 🐛 **Bug fixes**
- 📝 **Documentation improvements**

---

## 📄 License

MIT License
