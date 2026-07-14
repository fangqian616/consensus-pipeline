# 🎬 Consensus Pipeline

> **Stop AI from talking to itself. Start a real creative team that debates, collides, and reaches consensus.**
>
> A multi-agent debate-driven content creation framework — not "one AI writes for you," but "an AI team argues out the best solution."

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Tests-25/25_passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs">
</p>

> 📖 [中文文档](README_CN.md)

---

## 🤔 Why This Exists

**The single-LLM problem:** Whether you ask GPT or Claude, it's always one "person" answering. Self-reflection seems helpful, but researchers have found it leads to "Degeneration of Thoughts" — biases can't self-correct, rigid thinking can't self-breakthrough, and blind spots without external feedback are forever invisible.

**The existing multi-agent debate problem:** Most frameworks focus on "reasoning enhancement" — having AIs debate math problems, translations, and common-sense QA. Almost no one applies multi-agent debate to **creative content production** — having an AI team, like Pixar's Braintrust, where every specialized department debates internally and cross-pollinates externally, ultimately producing a complete, usable creative plan.

**Consensus Pipeline is that missing piece.**

```
Traditional:   You → One AI → One answer (maybe good, but you have no choice)
Debate-driven: You → An AI team → 8 departments debate internally → cross-department collisions → The best plan
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Consensus Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input                                                     │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────┐    AI Router auto-analyzes requirements           │
│  │ Tab0     │    Matches content type → selects departments     │
│  │ Smart    │    → configures debaters → generates presets       │
│  │ Config   │    All prompts editable, Skill injection supported │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐                                                   │
│  │ Tab1     │   Script / Characters / Prompts / Visual direction │
│  │ Input    │                                                   │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Tab2 Department Debates (8 departments, serial)       │       │
│  │                                                      │       │
│  │  Screenwriting → Spatial Design → Storyboard         │       │
│  │        ↓            ↓               ↓                │       │
│  │  Cinematography → Lighting → VFX → Sound → Editing   │       │
│  │                                                      │       │
│  │  Per department: 3-4 debaters × N rounds → Director  │       │
│  │  synthesis → Department consensus                     │       │
│  └──────────────────────────────────────────────────────┘       │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Tab3 Cross-Department Debate                          │       │
│  │                                                      │       │
│  │  Screenwriting ↔ Storyboard (narrative beats vs cuts) │       │
│  │  Cinematography ↔ Lighting (composition vs mood)      │       │
│  │  VFX ↔ Sound (visual impact vs audio rhythm)          │       │
│  │  Spatial ↔ Editing (scene blocking vs pacing)         │       │
│  └──────────────────────────────────────────────────────┘       │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Tab4 Review → Tab5 Final Output                       │       │
│  │                                                      │       │
│  │  Four-department review → 9-grid storyboard +        │       │
│  │  shot-by-shot video prompts                           │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/fangqian616/consensus-pipeline.git
cd consensus-pipeline
pip install -r requirements.txt
streamlit run app.py
```

Open your browser, configure your API key in the sidebar (supports DeepSeek / OpenAI / any compatible API), then:

1. **Tab0** → Describe your needs, AI auto-configures (or load a built-in preset)
2. **Tab1** → Fill in script, character references, visual direction
3. **Tab2** → 8 departments debate in sequence, watch each department's debaters clash in real-time
4. **Tab3** → Cross-department debate, resolve contradictions
5. **Tab4-5** → Review → Final output

---

## ✨ Core Features

### 🧠 AI Router — Smart Configuration

Not rigid template matching. The AI analyzes your needs and automatically decides:
- Which departments are needed (all 8? or just 3?)
- How many debaters per department (2-4)
- What style for each debater (role boundaries, points of dissent with others)

```python
# You say "just Screenwriting, Storyboard, and Lighting — 3 departments"
→ Router returns exactly 3 departments, 6 debaters, nothing extra

# You say "warm tones throughout, minimalist line art style"
→ Router auto-creates a Visual Style department, each debater with a distinct role
```

### ✏️ Fully Editable

Not happy with the AI-generated prompts? Every department's debater styles and parameters can be manually edited. Edit and run — **your edits take priority.**

### 💾 Local Persistence

Your configurations auto-save to `user_profiles/`. Next launch, your last-used config loads automatically. Built-in presets + user profiles, two systems that don't interfere.

### 📦 Skill Injection

Upload your proprietary knowledge (Markdown format), auto-injected at the end of every debater prompt in the target department. For example:
- Character design docs → inject into Screenwriting
- Visual style guide → inject into Lighting / VFX
- Brand guidelines → inject into all departments

### 🎯 Built-in Preset: Animation Debate

Ready-to-use 8-department × 24-debater complete animation production pipeline:
- Anime visual gene injection
- Spatial positioning system (object reference + screen position + vertical state)
- Complete review workflow
- From a script to a 9-grid storyboard + shot-by-shot video prompts

### 🏪 Market Simulation Mode

Instead of debaters persuading each other, creative ideas compete like products in a market:

```
Candidate campaigns → Quality interrogation → Voting → Patch refinement
```

3 AI-generated candidate proposals compete on the same stage, evaluated through sharp quality-assessment questions, with the winner receiving patches for optimization. Perfect for "I'm not sure what style I want" exploration scenarios.

### 🔄 Four Architecture Modes

| Mode | Mechanism | Quality | Speed | Token | Best For |
|------|-----------|:-------:|:-----:|:-----:|---------|
| **Consensus Pipeline** | 8 dept serial debate | ★★★★★ | ★★ | ★★★★ | Maximum quality |
| **Market Simulation** | Candidate competition + voting | ★★★★ | ★★ | ★★★★★ | Exploring directions |
| **Expert Pool** | Curated 2/dept | ★★★ | ★★★ | ★★ | Fast iteration |
| **Single Agent** | No debate, direct generation | ★★ | ★★★★★ | ★ | Baseline comparison |

One input, four modes — quantify the quality boost from "debate" and "competition."

---

## 🆚 Comparison

| Feature | Consensus Pipeline | MAD (Liang et al.) | MADJURY | ARGUS | AgentScope |
|---------|:---:|:---:|:---:|:---:|:---:|
| Multi-Agent Debate | ✅ | ✅ | ✅ | ✅ | ✅ |
| Creative Content Production | ✅ | ❌ | ❌ | ❌ | ❌ |
| AI Smart Configuration | ✅ | ❌ | ❌ | ❌ | ❌ |
| Department × Debater Structure | ✅ | ❌ | ❌ | ❌ | ❌ |
| User-Editable Prompts | ✅ | ❌ | ❌ | ✅ | ❌ |
| Local Persistence | ✅ | ❌ | ❌ | ❌ | ❌ |
| Market Simulation Model | ✅ | ❌ | ❌ | ❌ | ❌ |
| Four Architecture Modes | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cross-Domain General | ✅ | ❌ | ❌ | ❌ | ✅ |
| Streamlit UI | ✅ | ❌ | ❌ | ✅ | ✅ |
| Info Bottleneck (anti-bias) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Real-Time Visualization | ❌ | ❌ | ❌ | ✅ | ❌ |

**Consensus Pipeline's unique position:** Not chasing reasoning-benchmark scores, not chasing generic agent-framework breadth — focused on **using debate mechanisms to elevate creative content quality** — making an AI team collaborate like a real professional team.

---

## 📖 Examples

### Animated Short Film

```
Input: 3D animated short, desert chase scene, two characters, magic elements
AI Router → auto-config: 8 departments, 24 debaters
Run → 15 minutes later: 9-grid storyboard + 11 groups, 30 shots of video prompts
```

### Product Design

```
Input: AI note-taking app for Gen Z, need user research, feature architecture, interaction design
AI Router → auto-config: Audience Analysis / Content Structure / Visual Style / Narrative, 4 depts, 8 debaters
Run → output: user needs doc + feature architecture + interaction plan + visual guide
```

### Academic Paper

```
Input: Literature review on LLM multi-agent collaboration
AI Router → auto-config: Narrative / Content Structure / Audience / QA, 4 depts, 9 debaters
Run → output: literature review + methodology comparison + citation standards + rigor review
```

---

## 🔧 Configuration

Supports any OpenAI-compatible API:

| Provider | API URL | Recommended Model |
|----------|--------|-------------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Custom | Any compatible endpoint | Any model |

Fill in API Key, API URL, and model name in the sidebar.

---

## 🗺️ Roadmap

- [x] v3.0: AI Router smart config + user-editable prompts + local persistence + Skill injection
- [x] Built-in preset: Animation Debate (8 depts × 24 debaters)
- [x] Four architecture modes
- [x] Market Simulation model
- [ ] v3.1: Skill file upload (currently text paste)
- [ ] v3.2: More built-in presets (product design, novel writing, game design, academic papers)
- [ ] v3.3: Historical debate replay & comparison
- [ ] v3.4: Batch mode (one input, all four modes, compare outputs)
- [ ] v4.0: Debate process visualization (real-time DAG, debater opinion flow)

---

## 🤝 Contributing

PRs welcome! Especially:

- 🎨 **New preset templates** — product design, novel writing, game levels, business proposals…
- 🎭 **New debater styles** — contribute diverse debater perspectives for existing departments
- 🛠️ **New departments** — what's missing? Music department? Color department?
- 🐛 **Bug fixes**
- 📝 **Documentation improvements**

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License