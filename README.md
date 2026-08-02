# ⚡ AI Feature Prioritisation Engine

> **Turn a messy product backlog into a ranked, reasoned, stakeholder-ready roadmap — in under 10 seconds.**

A full-stack AI product tool built with Streamlit, Groq Llama 3.3 70B, and a hand-crafted dual-theme design system. Designed to showcase the intersection of **product thinking**, **LLM engineering**, and **production-quality UI craft**.

[![Streamlit](https://img.shields.io/badge/Streamlit-1.60+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036)](https://groq.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)

---

## The Problem

Most product teams prioritise features with gut feel, spreadsheets, or pure politics. RICE scoring exists — but applying it consistently across a backlog, while accounting for strategic goals, Kano classification, and honest risk assessment, takes hours of PM time per sprint.

**This tool does it in 10 seconds.**

---

## What It Does

Input your backlog. Get back a fully-ranked, AI-reasoned prioritisation with:

| Output | Detail |
|---|---|
| **RICE Score** | `(Reach × Impact × Confidence) ÷ Effort` with strategic goal multipliers (Revenue/Retention 1.3×, Delight 0.8×) |
| **Kano Category** | Must-have / Performance / Delight / Indifferent — classified by a 15-year PM persona |
| **Ship Quarter** | AI-recommended Q1–Q4 delivery timing based on effort and strategic priority |
| **AI Rationale** | 2-sentence reasoning: *why this rank* and *what business outcome it ships* |
| **Risk Flag** | The single biggest risk if this feature ships next quarter |
| **Stakeholder Objection** | A skeptical senior PM argues back against the #1 pick — forces you to defend your decision |

---

## Engineering Highlights

This isn't a weekend tutorial project. Here's what makes it production-grade:

### 🧠 LLM Pipeline (`prioritiser.py`)
- Structured JSON output enforcement with **strict schema validation** — all 7 required keys checked on every response
- **3-attempt retry loop** with `time.sleep(2)` backoff — handles Groq rate limits gracefully
- Enum validation on `kano_category` and `ship_quarter` — LLM hallucinations are caught and retried, not displayed
- Input coercion: `priority_rank` is coerced to `int` safely even if the model returns a string
- Specific exception handling: `groq.RateLimitError` vs `groq.AuthenticationError` vs generic `Exception`

### 🎨 Design System (`app.py`)
- **CSS custom properties (`--var`) dual-theme architecture** — 14 semantic tokens per theme (not just `!important` overrides)
- Light mode is a first-class design system, not an inverted dark mode: separate `--bg-void`, `--text-primary`, `--shadow-card-hover` values
- **Spring-physics card entrance animations** using `cubic-bezier(0.16, 1, 0.3, 1)` with 90ms stagger per card, scale + blur-to-sharp effect
- Theme toggle is implemented with pure CSS `:has()` selector — no JS, no flicker
- All Streamlit chrome hidden; fully custom layout with sticky header, bento grid, and auto-scroll to results

### 📄 PDF Report Generator
- Modern `fpdf2` API (`XPos`/`YPos` enums, not deprecated `ln=` params)
- Multi-page layout with confidence bars, colour-coded Kano badges, rationale + risk per card
- Footer injected on every page via direct page-index manipulation

### 🔁 State Management
- Session state tracks expanded cards as a `set` — O(1) lookup, no re-rendering side effects
- Auto-scroll to results on analysis completion using `st.components.v1.html` with `scrollIntoView`
- Theme changes clear expanded card state to prevent stale UI

---

## Architecture

```
User Input (Streamlit form)
        │
        ▼
┌─────────────────────┐
│   app.py            │  ← UI layer: CSS design system, state, rendering
│   (Streamlit UI)    │
└────────┬────────────┘
         │ calls
         ▼
┌─────────────────────┐
│   prioritiser.py    │  ← API layer: retry logic, schema validation
│   (Groq client)     │
└────────┬────────────┘
         │ uses
         ▼
┌─────────────────────┐
│   prompts.py        │  ← Prompt layer: PM persona, RICE rules, output schema
│   (System prompt)   │
└─────────────────────┘
         │
         ▼
  Groq Llama 3.3 70B
  (structured JSON response)
         │
         ▼
┌─────────────────────┐
│  Validation layer   │  ← All 7 keys present? Valid enums? Rank coercible?
│  (prioritiser.py)   │
└─────────────────────┘
         │
         ▼
  Sorted + Rendered Results
  (animated cards + bubble chart + PDF)
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/sankalpdusane/rice-kano-priority-engine.git
cd rice-kano-priority-engine

# 2. Create venv
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Add your Groq API key (free at console.groq.com)
echo "GROQ_API_KEY=your_key_here" > .env

# 5. Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Project Structure

```
ai-prioritisation-engine/
├── app.py              # UI: dual-theme CSS system, animations, charts, PDF
├── prioritiser.py      # API: Groq client, retry logic, schema validation
├── prompts.py          # LLM: PM persona system prompt, RICE + Kano rules
├── requirements.txt    # Pinned dependencies
├── .env                # 🔒 Never committed — GROQ_API_KEY goes here
├── .gitignore
└── .streamlit/
    └── config.toml     # Base theme config
```

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Rapid iteration without sacrificing full CSS control |
| LLM | Groq Llama 3.3 70B | Sub-second inference, free tier, structured output |
| Charts | Plotly Express | Theme-aware, interactive, zero extra JS |
| PDF | fpdf2 | Pure Python, no headless browser, no dependencies |
| Styling | Vanilla CSS (custom properties) | Full control; no framework lock-in |

---

## Security

- API key loaded at runtime via `python-dotenv` — never hardcoded
- `.env` in `.gitignore` — won't be accidentally committed
- Input validated before hitting the API (required fields, max 20 features)
- LLM output validated before rendering (schema + enum checks)

---

## What I'd Build Next

- **Streamlit Cloud / Railway deployment** with secrets management
- **Persistent backlog** via SQLite or Supabase
- **Multi-model comparison** (GPT-4o vs Llama vs Gemini) side by side
- **Jira / Linear integration** — push ranked backlog directly to your PM tool
- **Team mode** — multiple PMs submit scores, AI synthesises the median view

---

*Built by **Sankalp Dusane** — [LinkedIn](https://linkedin.com/in/sankalpdusane) · [GitHub](https://github.com/sankalpdusane/rice-kano-priority-engine)*
