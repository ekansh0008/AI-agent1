"""Diplomatic Negotiation Agent — Streamlit UI.

Run:  streamlit run app.py   (or double-click run.bat)

Two tabs:
  ⚡ Negotiation points from a round brief (2 lines or 2 pages — both fine)
  🎲 Practice generator (2-3 short topics -> pick one -> 1-2 page document)

Model, language and length are all auto/optimized — the user just pastes a brief.
"""

from __future__ import annotations

import os

import streamlit as st

from src.config import DEFAULT_MODEL
from src.llm import available_models_for_key
from src.negotiation import (
    CATEGORIES,
    DIFFICULTY_PROFILES,
    NegoMeta,
    _stringify,
    suggest_practice_topics,
)
from src.neg_pipeline import run_compact_playbook, run_compact_practice

REGION_DEFAULT = "South Asia"

st.set_page_config(
    page_title="Diplomatic Negotiation Agent",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
for key, default in (
    ("neg_result", None),
    ("practice_result", None),
    ("practice_ideas", None),
):
    st.session_state.setdefault(key, default)


# --------------------------------------------------------------------------
# Secrets / shared key / PIN gate (for public deployments)
# --------------------------------------------------------------------------

def _secret(name: str) -> str:
    try:
        val = st.secrets.get(name, "")
    except Exception:  # noqa: BLE001 - no secrets.toml locally
        val = ""
    if not val:
        val = os.getenv(name, "")
    return (val or "").strip()


def _shared_key() -> str:
    return _secret("GEMINI_API_KEY")


def _gate() -> None:
    """Optional PIN lock (APP_PIN in secrets/env) — keeps strangers out of a
    public deployment so they can't burn the shared API quota."""
    required = _secret("APP_PIN")
    if not required or st.session_state.get("pin_ok"):
        return
    st.title("🤝 Diplomatic Negotiation Agent")
    st.caption("This app is shared privately. Enter the access PIN to continue.")
    pin = st.text_input("Access PIN", type="password")
    if not pin:
        st.stop()
    if pin != required:
        st.error("Galat PIN. Ask the owner for the correct one.")
        st.stop()
    st.session_state.pin_ok = True
    st.rerun()


_gate()

# --------------------------------------------------------------------------
# Hide Streamlit Cloud chrome: GitHub / star / edit-pencil (top-right),
# "Manage app" (bottom-right) and the viewer badge.
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
      [data-testid="stToolbar"] {display: none !important;}
      [data-testid="stDecoration"] {display: none !important;}
      [data-testid="manage-app-button"] {display: none !important;}
      .viewerBadge_container__r5tak, .viewerBadge_link__qRIco {display: none !important;}
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Auto model selection — always pick the best model this key can use
# --------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def _auto_model(api_key: str) -> str:
    """Best available Gemini model for this key (refreshed hourly)."""
    try:
        models = available_models_for_key(api_key)
        if models:
            return models[0]
    except Exception:  # noqa: BLE001 - offline etc.
        pass
    return DEFAULT_MODEL


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🤝 Negotiation Agent")
    st.caption("Paste a brief → get your 1-2 page game plan. Simple English, 4-5 negotiation points.")
    st.divider()

    api_key = _shared_key()
    if api_key:
        # Shared server-side key (public deployment): never rendered into the page.
        st.success("Shared key active — koi key daalne ki zaroorat nahi. ✅", icon="🔓")
        with st.expander("Apni key use karni hai? (optional)"):
            custom = st.text_input("API key override", type="password", placeholder="AIza...")
            if custom.strip():
                api_key = custom.strip()
    else:
        st.markdown("Free key: [Google AI Studio](https://aistudio.google.com/apikey)")
        api_key = st.text_input("API key", type="password", placeholder="AIza...")

    if api_key:
        model = _auto_model(api_key)
        st.caption(f"🤖 Model: `{model}`  \n(auto — best available for this key)")
        with st.expander("🔍 Model details"):
            st.caption("The app asks Google's ListModels API which models your key "
                       "supports and picks the strongest free one automatically.")
            if st.button("Show all supported models", use_container_width=True):
                with st.spinner("Checking…"):
                    try:
                        st.code("\n".join(available_models_for_key(api_key)[:12]), language="text")
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc)[:300])
    else:
        model = DEFAULT_MODEL
        st.caption("🤖 Model auto-selects after the key is added.")
    st.divider()
    st.subheader("🧭 How it works")
    st.markdown(
        "1. **Playbook tab** — round ki brief paste karo (2 line ho ya 2 page)\n"
        "2. **1-2 page card ready** — 4-5 negotiation points, red lines, final deal points\n"
        "3. **Practice tab** — topics lo, pick karo, teammate ke saath rehearsal"
    )
    st.caption("⚠️ AI output verify karke hi table pe use karna.")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _render_error(exc: Exception) -> None:
    msg = str(exc)
    if "NOT_FOUND" in msg or "no longer available" in msg.lower() or "404" in msg:
        st.error(
            "Google isi waqt model switch kar raha hai — auto-detector ne waise bhi "
            "retry kiya hoga. Ek minute ruk kar dobara try karo.\n\n" + msg
        )
    elif "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        st.error(
            "Free quota thodi der ke liye khatam hui. 1 minute ruko ya sidebar se "
            "apni key daal ke try karo.\n\n" + msg
        )
    else:
        st.error(msg)


def _show_document(title: str, markdown: str, docx_path: str, md_path: str) -> None:
    st.subheader(title)
    words = len(markdown.split())
    st.caption(f"~{words:,} words · 1-2 pages")

    tab_preview, tab_download = st.tabs(["📖 Preview", "⬇️ Download"])
    with tab_preview:
        st.markdown(markdown)
    with tab_download:
        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        with open(md_path, "rb") as f:
            md_bytes = f.read()
        c1, c2 = st.columns(2)
        c1.download_button(
            "⬇️ Download Word (.docx)", docx_bytes,
            file_name=docx_path.split("/")[-1],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        c2.download_button(
            "⬇️ Download Markdown (.md)", md_bytes,
            file_name=md_path.split("/")[-1], mime="text/markdown",
            use_container_width=True,
        )
        st.caption("Word file: cover page ke saath — print karke seedha use karo.")


# --------------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------------
st.header("🤝 Diplomatic Negotiation Agent")
st.caption("On-the-spot brief aao — 1-2 page negotiation game plan paao. No setup, no jargon.")

tab_play, tab_prac = st.tabs(["⚡ Negotiation Points from a Brief", "🎲 Practice Generator"])

# ------------------------------- Tab 1: Playbook ---------------------------
with tab_play:
    st.write(
        "Round ki scenario brief jo mili use **yahan paste karo — 2-3 line ho ya 1-2 page, dono chalega.** "
        "Short ho toh agent samajhdari se expand karega; long ho toh sirf essential nikalega. "
        "Milega ek **1-2 page document** bilkul simple English mein: dono sides ke moti baat, "
        "tumhare red lines, **4-5 negotiation points** ki table, aur **4-5 final agreement points**. "
        "~1 minute mein ready."
    )
    with st.form("playbook_form"):
        brief = st.text_area(
            "Scenario brief (2 lines ho ya 2 pages — dono paste kar sakte ho) *",
            key="pb_brief", height=170,
            placeholder="Short: 'Do desh ek nadi ka paani baantne pe lad rahe hain, tum neeche wale desh ke ho.' …ya poori 1-2 page wali brief yahan paste karo",
        )
        c1, c2 = st.columns(2)
        with c1:
            stakeholder = st.text_input(
                "Your stakeholder/role", key="pb_side",
                placeholder="e.g. Ministry of Water, Republic of Aranya",
            )
            parties = st.text_input("Other parties (comma-separated)", key="pb_others")
        with c2:
            round_name = st.text_input(
                "Round", key="pb_round",
                placeholder="Preliminary / Quarterfinal / Semifinal / Grand Final",
            )
            time_limit = st.text_input("Time limit", key="pb_time", placeholder="e.g. 45 minutes")
        agreement_spec = st.text_input(
            "Agreement format announced at venue (optional)",
            key="pb_spec",
            placeholder="e.g. 2 pages, 800 words, clause-style — venue pe jo bole, yahan likho",
        )
        go = st.form_submit_button("⚡ Get my negotiation points (1-2 pages)", use_container_width=True)

    if go:
        if not brief.strip():
            st.warning("Pehle brief paste karo (2-3 line bhi chalegi).")
        elif not api_key:
            st.error("API key chahiye — sidebar mein daalo (free: https://aistudio.google.com/apikey).")
        else:
            meta = NegoMeta(
                brief_text=brief.strip(),
                your_stakeholder=stakeholder,
                other_parties=parties,
                round_name=round_name,
                time_limit=time_limit,
                agreement_spec=agreement_spec,
                topic=brief.strip()[:80],
            )
            status_box = st.status("Building your negotiation points…", expanded=True)
            result = None
            try:
                for event_ in run_compact_playbook(meta, api_key.strip(), model):
                    if event_["stage"] == "error":
                        status_box.update(label="Something went wrong", state="error")
                        st.error(event_["text"])
                        break
                    status_box.markdown(event_["text"])
                    if event_["stage"] == "done":
                        result = event_["data"]
                if result is not None:
                    status_box.update(label=f"✅ {result.title} — ready", state="complete")
                    st.session_state.neg_result = result
            except Exception as exc:  # noqa: BLE001
                status_box.update(label="Failed", state="error")
                _render_error(exc)

    if st.session_state.neg_result is not None:
        st.divider()
        _show_document(
            f"📋 {st.session_state.neg_result.title}",
            st.session_state.neg_result.markdown,
            st.session_state.neg_result.docx_path,
            st.session_state.neg_result.md_path,
        )

# ------------------------------- Tab 2: Practice ---------------------------
with tab_prac:
    st.write(
        "**Step 1:** **2-3 short practice topics** lo (2-3 lines each). "
        "**Step 2:** ek pick karo → **1-2 page negotiation document** — dono sides ka standpoint, "
        "**4-5 points ki negotiation** aur **4-5 final agreement points**. Print karke "
        "teammate ke saath practice karo."
    )
    with st.form("practice_ideas_form"):
        category = st.selectbox("Scenario category", CATEGORIES, key="pr_cat")
        difficulty = st.selectbox("Difficulty level", list(DIFFICULTY_PROFILES.keys()), key="pr_diff")
        ideas_clicked = st.form_submit_button("💡 Get 2-3 practice topics", use_container_width=True)

    if ideas_clicked:
        if not api_key:
            st.error("API key chahiye — sidebar mein daalo (free: https://aistudio.google.com/apikey).")
        else:
            from src.llm import LLMClient

            with st.spinner("Thinking up practice scenarios…"):
                try:
                    ideas = suggest_practice_topics(
                        category, difficulty, REGION_DEFAULT,
                        LLMClient(api_key=api_key.strip(), model=model),
                    )
                    st.session_state.practice_ideas = {
                        "ideas": ideas,
                        "category": category,
                        "difficulty": difficulty,
                    }
                    st.session_state.practice_result = None
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)

    pack = st.session_state.practice_ideas
    if pack:
        st.subheader("💡 Your practice topics")
        options = []
        for i, idea in enumerate(pack["ideas"], 1):
            options.append(f"{i}. {idea.get('title', '')}")
            st.markdown(
                f"**{i}. {idea.get('title', '')}** — {idea.get('blurb', '')}  \n"
                f"*🤝 {idea.get('side_a', '')} vs {idea.get('side_b', '')}*"
            )
        with st.form("practice_pick_form"):
            choice = st.radio(
                "Pick a topic for the document", options, key="pr_choice", horizontal=True
            )
            gen_clicked = st.form_submit_button(
                "📄 Make the 1-2 page negotiation document", use_container_width=True
            )
        if gen_clicked:
            idx = options.index(choice) if choice in options else 0
            idea = pack["ideas"][idx]
            status_box = st.status("Writing your negotiation document…", expanded=True)
            result = None
            try:
                for event_ in run_compact_practice(
                    idea, pack["category"], pack["difficulty"], REGION_DEFAULT,
                    api_key.strip(), model,
                ):
                    if event_["stage"] == "error":
                        status_box.update(label="Something went wrong", state="error")
                        st.error(event_["text"])
                        break
                    status_box.markdown(event_["text"])
                    if event_["stage"] == "done":
                        result = event_["data"]
                if result is not None:
                    status_box.update(label=f"✅ {result.title} — ready", state="complete")
                    st.session_state.practice_result = result
            except Exception as exc:  # noqa: BLE001
                status_box.update(label="Failed", state="error")
                _render_error(exc)

    if st.session_state.practice_result is not None:
        st.divider()
        st.info("📄 Compact 1-2 page document — print it, team briefs baant lo, timer chalao.")
        _show_document(
            f"🎲 {st.session_state.practice_result.title}",
            st.session_state.practice_result.markdown,
            st.session_state.practice_result.docx_path,
            st.session_state.practice_result.md_path,
        )
