# 🧠 Consensus Pipeline

<p align="center">
  <img src="banner.png" alt="Consensus Pipeline" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Latest-v0.7.5-brightgreen" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

> **Multi-agent debate framework for structured content generation.**
> Instead of one AI writing for you — an AI team debates, collides, and reaches consensus.

📖 [中文文档](README_CN.md) · 📦 [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases)

---

## ❓ Why Not Just Ask ChatGPT?

A single LLM produces confident-sounding answers with no cross-validation — hallucinations slip through, conflicting perspectives get flattened, and you can't tell which conclusions are solid vs. speculative. This framework replaces one-shot generation with **structured multi-agent debate as a quality gate**: every claim is challenged by independent "departments," contradictions are surfaced explicitly, and final conclusions carry **confidence annotations** (e.g., "42/77 papers, high confidence"). Think of it as built-in peer review — not a single author, but an adversarial committee.

---

## 🎯 What Does It Do?

Consensus Pipeline replaces single-AI generation with **structured multi-agent debate**. Different AI "departments" argue from their professional perspectives, challenge each other's assumptions, and converge on a high-quality consensus output.

**Core design philosophy:** structured multi-agent debate as a quality gate — every claim is contested, every assumption is challenged, and the output carries explicit confidence levels rather than false certainty.

**Two pipelines, one framework:**

| | 🔬 Academic Pipeline | 🎬 Creative Pipeline |
|---|---|---|
| **Input** | A research topic | A script / story |
| **Process** | Search → QC → Debate → Review | 8-dept debate → Storyboard → Video prompts |
| **Output** | Literature review + paper metadata | 9-grid storyboard + per-shot video prompts |
| **Maturity** | 🧪 v0.7.3 — early stage, seeking feedback | 🔄 v3.0 — actively iterating |
| **Best for** | Researchers, students, analysts | Animators, content creators |

---

## 🆕 What's New in v0.7.3

| Feature | Description |
|---------|-------------|
| **🔬 QC Department** | 3-layer filter: hard filter → LLM classify → layer tagging. Reduced 219 retrieved papers to 77 relevant ones (64% exclusion rate) |
| **⚙️ Dynamic Domain Config** | LLM generates domain-specific exclusion signals, query rotation, and tier definitions — zero hardcoding, change topic without code changes |
| **🔗 Citation Validation** | Auto-verify all `[N]` references against CSV; remove dangling citations |
| **📊 Confidence Annotation** | Every conclusion tagged with `(N/M papers, confidence level)` — no more unsupported claims |
| **🔧 OpenAlex Priority** | Abstract backfill uses OpenAlex first (no 429 rate limits), falls back to Semantic Scholar |
| **🌐 English Report (`--lang en`)** | v0.7.2: Full English report output via `--lang en` flag |
| **🔄 Rounds Fix** | v0.7.3: Fixed debate rounds parameter handling for consistent multi-round behavior |

## 📸 Demo / Screenshots

> Screenshots coming soon. Below is a description of each Streamlit tab:

| Tab | What It Does |
|-----|-------------|
| 🧠 Smart Config | Describe your goal → AI auto-configures departments & debaters |
| 📝 Input | Enter script/topic, positive/negative prompts, character refs |
| 🗣️ Dept. Debate | Watch departments debate in real-time, review each debater's arguments |
| ⚔️ Cross Debate | Resolve contradictions between departments |
| 🔍 Proofread | Multi-department review & auto-correction of final output |
| 🎬 Output | Export 9-grid storyboard + per-shot video prompts |
| 📊 Compare | Side-by-side runs with different models/architectures |
| 🏪 Market | Candidate campaigns → voting election → patch correction |
| 📚 Academic | Full academic pipeline: search → QC → debate → literature review |

---

## 🏗️ Architecture

### Academic Pipeline (v0.7.3)

```
Research Topic
     │
     ▼
┌─────────────────────────┐
│ Phase 0: Domain Config │  ← LLM generates exclusion signals, query terms, tier rules
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
│ Phase 2: QC Department  │  ← 3-layer sieve:
│ Quality Control         │     hard_filter → LLM_classify → tag_layer
│ (NEW in v0.7.1)         │     219 papers → 77 relevant (core/method/background)
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 3: Department     │  ← 11 research departments debate
│ Debate (serial)         │     Each dept: 3-4 debaters → consensus
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 4: Cross-Dept     │  ← Resolve contradictions between departments
│ Debate                  │
└────────────┬────────────┘
             │
     ▼
┌─────────────────────────┐
│ Phase 5: Report         │  ← Literature review with confidence annotations
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

## 📋 Prerequisites

| Requirement | Details |
|-------------|---------|
| Python 3.9+ | 3.11+ recommended |
| DeepSeek API Key | [Register](https://platform.deepseek.com/) — ~$0.01 per full run |
| Internet | Access to DeepSeek API (custom endpoints supported) |

> 💡 No GPU needed. No database needed. No other service registration required. Paper retrieval uses free open APIs (arXiv / Semantic Scholar / OpenAlex).

---

## 🚀 Quick Start

```bash
git clone https://github.com/fangqian616/consensus-pipeline.git
cd consensus-pipeline
pip install -r requirements.txt
streamlit run app.py
```

### 🔬 Academic Pipeline (CLI)

```bash
# 1️⃣ Set your DeepSeek API key
export DEEPSEEK_API_KEY=your_key_here

# 2️⃣ Run the full pipeline (Chinese report, default)
python run_pipeline.py --topic "Machine Learning in Energy Economics"

# 3️⃣ Run with English report output
python run_pipeline.py --topic "Machine Learning in Energy Economics" --lang en
```

**CLI parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--topic` | ✅ Yes | — | Research topic (e.g., "LLM in Healthcare") |
| `--lang` | No | `zh` | Output language: `zh` (Chinese) or `en` (English) |

### 🔬 Academic Pipeline (Streamlit)

1️⃣ **Configure API** — Enter your DeepSeek/OpenAI key in the sidebar
2️⃣ **Enter topic** — Type your research topic in the 📚 Academic tab
3️⃣ **Confirm config** — AI generates domain config (exclusion signals, query terms); review & confirm
4️⃣ **Watch pipeline run** — Papers are retrieved → QC-filtered → debated across 11 departments
5️⃣ **Get results** — Download literature review with confidence annotations, PDF/DOCX exports

### 🎬 Creative Pipeline (Streamlit)

1️⃣ **Smart Config** — Go to 🧠 Smart Config tab, describe your content goal (or pick a preset)
2️⃣ **Enter script** — Switch to 📝 Input tab, fill in script + positive/negative prompts
3️⃣ **Run debate** — Click "一键全辩" (auto-run all) or use step-by-step mode
4️⃣ **Review output** — Check 🗣️ Dept. Debate and ⚔️ Cross Debate tabs for intermediate results
5️⃣ **Export** — Go to 🎬 Output tab for 9-grid storyboard + per-shot video prompts

---

## 📖 Usage

### CLI Reference

The `run_pipeline.py` script provides headless execution of the academic pipeline:

```bash
python run_pipeline.py --topic "Your Research Topic" --lang en
```

| Flag | Type | Default | Choices | Description |
|------|------|---------|---------|-------------|
| `--topic` | str | *(required)* | — | Research topic for literature review |
| `--lang` | str | `zh` | `zh`, `en` | Output language for the final report |

You can also set the topic via environment variable:

```bash
export DEEPSEEK_TOPIC="Machine Learning in Energy Economics"
python run_pipeline.py
```

### Streamlit Tab Guide

The Streamlit UI (`streamlit run app.py`) organizes the workflow across tabs:

| # | Tab | Pipeline | Purpose |
|---|-----|----------|---------|
| 1 | 🧠 Smart Config | Both | AI auto-configures departments & debaters; load/save presets |
| 2 | 📝 Input | Creative | Enter script, prompts, character references |
| 3 | 🗣️ Dept. Debate | Creative | Run & monitor department-level debates |
| 4 | ⚔️ Cross Debate | Creative | Resolve inter-department contradictions |
| 5 | 🔍 Proofread | Creative | Multi-dept review and auto-correction |
| 6 | 🎬 Output | Creative | View & export storyboard + video prompts |
| 7 | 📊 Compare | Creative | Side-by-side comparison of different runs |
| 8 | 🏪 Market | Creative | Candidate generation → voting → patch correction |
| 9 | 📚 Academic | Academic | Full pipeline: search → QC → debate → report |

### Environment Configuration

**API Keys (required):**

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | ✅ Yes | DeepSeek API key for LLM calls |
| `EASYSCHOLAR_SECRET_KEY` | No | easyScholar key for enhanced journal ranking |

**Model Selection:**

| Provider | API URL | Recommended Model |
|----------|--------|-------------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` or `deepseek-v4-pro` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Custom | Any OpenAI-compatible endpoint | Any model |

Set API key and model in the Streamlit sidebar, or via environment variables.

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

### QC Department (v0.7.1+)

The biggest quality leap in v0.7.1. Three-layer filtering ensures zero pollution:

- **Layer 1 — Hard Filter**: Remove obviously off-topic papers via exclusion signals (e.g., carbon nanotube, botany)
- **Layer 2 — LLM Classify**: LLM judges each paper's domain membership; excluded 137/219 papers
- **Layer 3 — Layer Tagging**: Classify remaining papers into importance tiers: core (68) / method (6) / background (3)

Result: 219 → 77 papers, 64.8% exclusion rate, 0% off-topic in final output.

### Dynamic Domain Config (v0.7.1+)

No more hardcoded keywords. LLM generates everything based on your topic:

```json
{
  "domain_definition": "Application of ML methods to energy economics...",
  "exclusion_signals": ["carbon nanotube", "botany", "materials science"],
  "query_rotation": ["machine learning energy forecasting", "deep learning electricity pricing", ...],
  "tier_definitions": {"core": "...", "method": "...", "background": "..."}
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
├── quality_controller.py        # QC department (v0.7.1)
├── domain_config_generator.py   # Dynamic domain config (v0.7.1)
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
| **v0.7.5** | 2026-07-17 | UI 9→4 Tab restructure, easyScholar demoted, README rewrite, language welcome screen |
| **v0.7.3** | 2026-07-17 | Fixed debate rounds parameter (multi-round debate loop) |
| **v0.7.2** | 2026-07-17 | English report output (`--lang en`), legacy tag cleanup |
| **v0.7.1** | 2026-07-17 | First public release: QC department, dynamic domain config, citation validation, confidence annotation, OpenAlex priority |

> Pre-v0.7.1 versions were internal development builds and are not publicly released.

---

## 🗺️ Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| P0 | Report segment generation (plan-then-generate) | Planned |
| P0 | QC false-positive reverse validation | Planned |
| P1 | Semantic citation verification (embedding-based) | Planned |
| P1 | Sub-topic query splitting | Planned |
| P1 | Publication bias detection (funnel plot) | Planned |
| P1 | Multi-round debate | ✅ Done (v0.7.3) |
| P2 | Cross-language retrieval (CNKI + bilingual alignment) | Planned |
| P2 | Incremental update capability | Planned |

---

## ❓ FAQ / Troubleshooting

**Q: How long does a full pipeline run take?**
A: Academic pipeline: 10-30 minutes depending on topic and paper count. Creative pipeline: 5-15 minutes for 8-department debate. Use Expert Pool mode to cut time ~50%.

**Q: Token consumption seems high — how much does it cost?**
A: Full 8-department creative debate costs ~10k-30k tokens (varies by debate rounds). Expert Pool mode reduces this by ~50%. With DeepSeek pricing, a full run costs under $0.10.

**Q: Which APIs are supported?**
A: Any OpenAI-compatible API. DeepSeek (recommended, best value), OpenAI, or locally deployed models via custom endpoints.

**Q: What languages does the output support?**
A: Academic pipeline: Chinese (`--lang zh`, default) and English (`--lang en`). Creative pipeline: output prompts are always in English; the Streamlit UI supports both Chinese and English.

**Q: Debate quality is inconsistent — what can I do?**
A: (1) Increase debate rounds, (2) use a stronger model, (3) add specific constraints in debater prompts, (4) use director rejection to force re-debate.

**Q: Can I run only some departments?**
A: Yes. In Smart Config, disable departments you don't need. For CLI, the full pipeline runs all departments.

**Q: How do I switch to a different research domain?**
A: Just change the `--topic` argument. Dynamic Domain Config (v0.7.1+) auto-generates new exclusion signals, query rotation, and tier definitions — no code changes needed.

---

### Optional: easyScholar API

For enhanced journal ranking, get a key at [easyScholar](https://www.easyscholar.cc/):

```bash
# Set in Streamlit sidebar or environment variable
export EASYSCHOLAR_SECRET_KEY=your_key_here
```

Without easyScholar, the pipeline uses a local 209-journal registry as fallback.

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
