# 🔬 Consensus Pipeline

> **A multi-agent debate-driven research & creation framework.**  
> Not one AI writes for you — an AI team debates, collides, and reaches consensus.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Latest-v5.1.1-brightgreen" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

> 📖 [中文文档](README_CN.md)

---

## 🆕 What's New in v5.x

| Version | Highlight |
|---------|-----------|
| **v5.1.1** | 📝 Report compression — final report ≤3000 chars, LLM fluff skipping, hard truncate |
| **v5.1** | 📊 Dual-template report (deliverable + internal doc), 4th relevance filter, 209-journal registry |
| **v5.0** | 🔍 easyScholar API integration — S-level papers 3→47, C-level 80→9 |
| **v4.5** | 🔗 Full pipeline: requirement research → debate → report |
| **v4.0** | 🧪 Requirement research Tab, academic mode, programming & tutorial departments |

Full changelog: [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Consensus Pipeline v5                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 0-4: Requirement Research (NEW)                           │
│     AI interview → scope definition → user confirmation           │
│     ──────────────────────────────────────────                    │
│                                                                  │
│  Two Modes:                                                      │
│  ┌─────────────────────┐    ┌──────────────────────────┐         │
│  │ 🎬 Animation Mode   │    │ 🔬 Academic Mode         │         │
│  │                     │    │                          │         │
│  │ 8 creative depts    │    │ 11 research depts        │         │
│  │ + video prompts     │    │ + programming + tutorial │         │
│  │ + 9-grid storyboard │    │ + paper quality filter   │         │
│  └─────────────────────┘    └──────────────────────────┘         │
│     │                              │                              │
│     ▼                              ▼                              │
│  ┌────────────────────────────────────────────────────┐          │
│  │ Department Debate (serial, 3-4 debaters each)       │          │
│  │  → Director synthesis → Department consensus        │          │
│  └────────────────────────────────────────────────────┘          │
│     │                                                            │
│     ▼                                                            │
│  ┌────────────────────────────────────────────────────┐          │
│  │ Cross-Department Debate                              │          │
│  │  Resolve contradictions, strengthen evidence         │          │
│  └────────────────────────────────────────────────────┘          │
│     │                                                            │
│     ▼                                                            │
│  ┌────────────────────────────────────────────────────┐          │
│  │ Final Output                                         │          │
│  │  Deliverable report (≤3000 chars) + Internal doc    │          │
│  │  + PDF export + CSV metadata + Fact-checking        │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/fangqian616/consensus-pipeline.git
cd consensus-pipeline
pip install -r requirements.txt
streamlit run app.py
```

Open your browser, configure API key in sidebar, then:

1. **Tab 0** → Describe your needs (AI interviews you or you fill in directly)
2. **Tab 1** → AI auto-configures departments & debaters
3. **Tab 2** → Fill in research topic / script
4. **Tab 3** → Watch departments debate in real-time
5. **Tab 4** → Cross-department debate
6. **Tab 5** → Final deliverable report + PDF export

---

## 🔬 Academic Mode

The headline feature of v4.0+. A complete academic research pipeline:

### 11 Research Departments

| Department | Role |
|-----------|------|
| Literature Search | Multi-source retrieval, deduplication |
| Metadata Inspector | DOI verification, metadata completeness |
| Citation Network | Citation analysis, impact metrics |
| Methodology Review | 7-dimension evaluation (accuracy, efficiency, interpretability...) |
| Data Validation | Data source quality, reproducibility |
| Counter-Evidence | Anti-mainstream findings, controversy mapping |
| Topic Clustering | Thematic grouping, trend identification |
| Visualization | Chart & distribution analysis |
| Report Integration | Cross-validation, consensus building |
| **Programming** | Analyze mainstream models/tools, output runnable code |
| **Tutorial** | Teach how to use research tools & methods |

### Paper Quality Filtering (4-Layer Sieve)

```
Layer 1: easyScholar API → journal rank (S/A/B/C)
Layer 2: Citation count + h-index filter
Layer 3: Local 209-journal registry (9 disciplines + 6 AI conferences + 3 CN CSSCI)
Layer 4: Relevance scoring (_compute_relevance) — domain must-have + ML must-have
```

**Results (ML in Energy Economics experiment):**

| Metric | v4.5 (no easyScholar) | v5.0 (easyScholar) | v5.1 (full pipeline) |
|--------|:---:|:---:|:---:|
| S-level papers | 3 | 47 | 41 |
| C-level papers | 80 | 9 | 9 |
| Total papers | 84 | 71 | 76 |
| Self-evaluation | 4/10 | 4/10 | 5.5/10 |

### Dual-Template Report

- **Deliverable report** (≤3000 chars): Core findings with confidence levels, methodology distribution, top papers, research gaps
- **Internal document** (full detail): Complete debate transcripts, all papers with metadata, programming & tutorial output

Both exportable as PDF with Chinese font support (LXGW WenKai).

---

## ✨ Core Features

### 🧠 AI Router — Smart Configuration
AI analyzes your needs → selects departments → configures debaters → generates presets. All editable.

### 💬 Requirement Research (v4.0+)
AI-conducted interview (Phase 0-4) before entering the main pipeline. Define scope, constraints, and priorities through dialogue.

### 🏪 Market Simulation Mode
Creative ideas compete like products: Candidates → Quality interrogation → Voting → Patch refinement

### 🔄 Four Architecture Modes

| Mode | Mechanism | Quality | Speed | Best For |
|------|-----------|:-------:|:-----:|----------|
| **Consensus Pipeline** | Serial dept debate | ★★★★★ | ★★ | Maximum quality |
| **Market Simulation** | Competition + voting | ★★★★ | ★★ | Exploring directions |
| **Expert Pool** | 2/dept curated | ★★★ | ★★★ | Fast iteration |
| **Single Agent** | No debate | ★★ | ★★★★★ | Baseline |

### 📦 Skill Injection
Upload proprietary knowledge (Markdown) → auto-injected into target department prompts.

### 🔍 Fact-Checking (Phase 7.5)
Automated factual verification of report claims with source tracing.

---

## 🔧 Configuration

| Provider | API URL | Recommended Model |
|----------|--------|-------------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Custom | Any compatible endpoint | Any model |

### Optional: easyScholar API

For enhanced journal ranking, get a key at [easyScholar](https://www.easyscholar.cc/):

```bash
# Set in Streamlit sidebar or environment variable
export EASYSCHOLAR_SECRET_KEY=your_key_here
```

Without easyScholar, the pipeline uses a local 209-journal registry as fallback.

---

## 📁 Project Structure

```
consensus-pipeline/
├── app.py                    # Streamlit main app (9 tabs)
├── router.py                 # AI Router — smart department config
├── debate_engine.py          # Core debate engine
├── config_manager.py         # Config persistence & presets
├── pdf_exporter.py           # PDF export with Chinese fonts
├── requirement/              # Requirement research module (v4.0+)
│   ├── interviewer.py        # AI interview agent
│   ├── structurer.py         # Scope & constraint extraction
│   ├── generator.py          # Requirement document generation
│   ├── validator.py          # Completeness check
│   └── __init__.py
├── academic/                 # Academic research module (v4.0+)
│   ├── search_engine.py      # Multi-source search (OpenAlex, Semantic Scholar, arXiv)
│   ├── journal_classifier.py # 4-layer journal quality sieve + easyScholar
│   ├── journal_registry.py   # 209-journal local registry
│   ├── report_generator.py   # Dual-template report generation
│   ├── fact_checker.py       # Automated fact verification
│   └── __init__.py
├── templates/                # Debate prompt templates
├── presets/                  # Built-in presets (animation, academic)
├── fonts/                    # Chinese fonts (LXGW WenKai)
└── run_pipeline.py           # CLI runner for headless execution
```

---

## 🗺️ Version History

| Version | Date | Changes |
|---------|------|---------|
| v5.1.1 | 2026-07-15 | Report compression, LLM fluff skipping, 3000-char hard limit |
| v5.1 | 2026-07-15 | Dual-template report, 4th relevance filter, 209-journal registry, methodology 7-dim framework |
| v5.0 | 2026-07-15 | easyScholar API integration, journal rank bug fixes |
| v4.5 | 2026-07-15 | Full requirement→debate pipeline, academic mode UI fix |
| v4.4 | 2026-07-15 | 20+ paper guarantee, preprint appendix, URL encoding fix |
| v4.3 | 2026-07-15 | 11 review issues fixed, Chinese tokenization, fuzzy match constraint |
| v4.2 | 2026-07-15 | easyScholar integration, FactChecker, journal quality enhancement |
| v4.1 | 2026-07-15 | PDF export with Chinese font support |
| v4.0 | 2026-07-15 | Requirement research, academic mode, programming & tutorial depts |
| v3.0 | 2026-07-14 | AI Router, user-editable prompts, local persistence, Skill injection |

All versions available as [GitHub Releases](https://github.com/fangqian616/consensus-pipeline/releases).

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
