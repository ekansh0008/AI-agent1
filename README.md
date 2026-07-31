# 🌍 SDG Policy Paper Agent

Give it a **topic** — it finds the right **UN Sustainable Development Goals**, runs
**deep web research** (statistics, laws, UN/World Bank/OECD reports, case studies,
academic evidence), and drafts a complete, **human-sounding policy paper** in the
recommended competition structure, exported as **Word (.docx)** and **Markdown (.md)**.

Powered by **Gemini** (free tier) + **DuckDuckGo** (no search API key needed).

---

## ✨ What it does

```
Your topic
   │
   ▼
1. SDG MAPPING ──► primary + secondary SDGs, policy area, title, research keywords
   │
   ▼
2. DEEP RESEARCH ──► 8–16 targeted searches ▸ fetches & reads the best pages
   │                  (un.org, worldbank.org, oecd.org, .gov, academic…)
   ▼
3. WRITING ──► every section of the required structure, with in-text APA citations
   │            from the researched sources (Executive Summary written last)
   ▼
4. EXPORT ──► formatted .docx (cover page, 1.5 spacing, real tables, page numbers)
               + .md copy
```

The draft follows this structure exactly:

Cover Page · 1. Executive Summary (250–350 words) · 2. Problem Analysis (Current
Situation / Stakeholder Analysis / Root Cause Analysis) · 3. Policy Context &
Evidence · 4. Policy Proposal (SMART Objectives / Proposed Solution / Innovation) ·
5. Implementation Strategy (phased plan + budget table) · 6. Impact, Risk & Ethics
(+ SDG Alignment) · 7. Monitoring & Evaluation Framework (indicator table) ·
8. Conclusion · References (APA 7th, built from the actually-searched sources) ·
Annexures (timeline, detailed budget, SDG-target map).

---

## 🚀 Quick start

### 1. Get a free Gemini API key
Visit **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** →
sign in with a Google account → *Create API key*. Free tier is enough.

### 2. Install
```bash
git clone <this repo> && cd AI-agent1
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your key
Either:
- copy `.env.example` to `.env` and paste your key, **or**
- just paste it into the app sidebar each session.

### 4. Run
```bash
streamlit run app.py
```
Open http://localhost:8501, enter your topic, click **Map this topic to SDGs**,
review the mapping, then **Research & Draft Policy Paper**. Download your `.docx`.

A standard-depth run takes roughly 3–6 minutes depending on network speed and
model load.

---

## 🧱 Project layout

```
app.py                  Streamlit web UI
src/
  config.py             settings, depth presets, cover metadata
  sdg_data.py           all 17 SDGs + keyword library
  sdg_classifier.py     topic → SDG mapping (LLM + offline keyword fallback)
  research.py           query generation, DuckDuckGo search, page extraction,
                        source ranking, APA cite-keys & reference lines
  structure.py          the required paper structure + per-section guidance
  writer.py             human-style section writer + assembly + word count
  docx_export.py        markdown → formatted Word (cover, tables, hanging
                        indents, page numbers)
  pipeline.py           streaming orchestrator (progress events → UI)
tests/test_smoke.py     no-key smoke tests:  python tests/test_smoke.py
outputs/                generated papers land here (git-ignored)
```

---

## ⚙️ Tips

- **Deeper research** — pick *Deep research* in the sidebar for more queries,
  more sources and a longer paper.
- **Quota errors (429)** — the free Gemini tier rate-limits; wait a minute, or
  change the model name in the sidebar (e.g. `gemini-3.5-flash`).
- **404 / NOT_FOUND errors** — Google renames model IDs over time. Type a current
  model ID from [aistudio.google.com](https://aistudio.google.com) into the
  sidebar's *Model* box (defaults to `gemini-3-flash`).
- **Offline demo** — classification has a keyword fallback, but research/writing
  need the API key.
- **Verify before submitting** — this is an AI-assisted *draft*. Check every
  statistic and click through the references (the list is built from pages the
  agent actually fetched, which keeps hallucination low, not zero).

## ⚠️ Disclaimer

Generated drafts are meant as a strong starting point for your own work. Most
competitions require original submissions — rewrite, verify sources, and add your
own analysis before submitting.
