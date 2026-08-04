# 🤝 Diplomatic Negotiation Agent

A negotiation-prep agent for the **Diplomatic Negotiation Challenge**: paste the
on-the-spot scenario brief (2 lines or 2 pages — both fine) and get a compact
**1-2 page game plan** in simple English. Everything is automatic — the app picks
the best AI model for your key, writes in grade-5-simple language, and fits the
whole strategy on one printout.

## Two tabs

**⚡ Negotiation points from a brief** — paste the round's brief → get:

- the situation in 3 lines · both sides' fundamentals · **your red lines**
- **the 4-5 points of negotiation** in a point-by-point table (you open here /
  they open there / landing zone)
- **the 4-5 final agreement points** — concrete, signable clauses
- opening & closing lines to say at the table

Short briefs are expanded with clearly stated assumptions; long briefs are
distilled to the essentials. Ready in about a minute.

**🎲 Practice generator** — pick a category + difficulty → get **2-3 short
practice topics** (2-3 lines each) → choose one → the same kind of **1-2 page
negotiation document** to rehearse with your 2-person team.

*(An SDG policy-paper mode used to be part of this app; its engine remains in
`src/` but is no longer exposed in the UI.)*

## 📄 Mode 2: SDG Policy Paper

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

## 🌐 Publish it (share a public link)

Deploy free on **Streamlit Community Cloud** so anyone can use the app in their
browser — no install needed:

1. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub.
2. **Create app** → repo `ekansh0008/AI-agent1`, branch `arena/019fb242-ai-agent1`,
   main file `app.py` → **Deploy** (2-3 min).
3. Open the app's **Settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your-key-here"     # visitors won't need any key
   APP_PIN = "choose-a-simple-pin"      # optional: only people with this PIN can use it
   ```
4. Share the generated link (and PIN, if set) — done. ✅

Notes: secrets live only on the deployment server (never committed to git). A
shared key shares your free Gemini daily quota — the PIN gate keeps strangers out.
If you'd rather not share your key, skip the secrets: each visitor then pastes
their own free key in the sidebar.

## ⚙️ Tips

- **Deeper research** — pick *Deep research* in the sidebar for more queries,
  more sources and a longer paper.
- **Quota errors (429)** — the free Gemini tier rate-limits; wait a minute, or
  change the model name in the sidebar (e.g. `gemini-3.5-flash`).
- **404 / NOT_FOUND errors** — Google renames model IDs over time. The agent
  auto-detects an available model and retries; you can also click
  *Detect models my key supports* in the sidebar to see exactly which model IDs
  your API key can use, and copy one into the *Model* box.
- **Offline demo** — classification has a keyword fallback, but research/writing
  need the API key.
- **Verify before submitting** — this is an AI-assisted *draft*. Check every
  statistic and click through the references (the list is built from pages the
  agent actually fetched, which keeps hallucination low, not zero).

## ⚠️ Disclaimer

Generated drafts are meant as a strong starting point for your own work. Most
competitions require original submissions — rewrite, verify sources, and add your
own analysis before submitting.
