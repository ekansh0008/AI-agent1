"""SDG Policy Paper Agent — Streamlit UI.

Run:  streamlit run app.py

Flow:
  1. Enter your topic (and cover-page details)
  2. Click "Map to SDGs" — review/adjust the mapping
  3. Click "Research & Draft Policy Paper" — deep web research, then the
     full paper is written, and you download .docx / .md
"""

from __future__ import annotations

import streamlit as st

from src.config import DEPTH_PRESETS, DEFAULT_MODEL, PaperMeta, env_api_key
from src.pipeline import run_classification, run_pipeline
from src.sdg_classifier import SDGMapping
from src.sdg_data import SDGS, sdg_label

st.set_page_config(
    page_title="SDG Policy Paper Agent",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
for key, default in (
    ("sdg_mapping", None),
    ("result", None),
    ("classified_topic", ""),
):
    st.session_state.setdefault(key, default)


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 SDG Policy Paper Agent")
    st.caption("Topic → SDG mapping → deep research → human-written policy draft")
    st.divider()

    st.subheader("🔑 Gemini API")
    st.markdown(
        "Free key: [Google AI Studio](https://aistudio.google.com/apikey)"
    )

    def _default_key() -> str:
        from src.config import env_api_key as _env

        key = _env()
        if key:
            return key
        try:
            return st.secrets.get("GEMINI_API_KEY", "")
        except Exception:  # noqa: BLE001 - no secrets.toml present
            return ""

    api_key = st.text_input(
        "API key",
        value=_default_key(),
        type="password",
        placeholder="AIza...",
    )
    model = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-2.0-flash"],
        index=0,
    )
    depth = st.radio("Research depth", list(DEPTH_PRESETS.keys()), index=1)
    st.divider()
    st.subheader("🧭 How it works")
    st.markdown(
        "1. **Map** — your topic is placed in the SDG framework\n"
        "2. **Research** — DuckDuckGo finds statistics, laws, UN & World Bank reports\n"
        "3. **Write** — each section drafted with citations\n"
        "4. **Export** — Markdown + formatted Word (.docx)"
    )
    st.caption("⚠️ Always review facts and references before submission.")


# --------------------------------------------------------------------------
# Main — inputs
# --------------------------------------------------------------------------
st.header("Policy Paper Draft Agent")
st.write(
    "Give me a topic. I'll map it to the right **UN Sustainable Development Goals**, "
    "run **deep research** on the web, and draft a complete policy paper in the "
    "recommended structure — with APA references."
)

with st.form("topic_form"):
    topic = st.text_area(
        "Your topic *",
        placeholder="e.g. Universal healthcare access for rural communities in India",
        height=90,
    )
    c1, c2 = st.columns(2)
    with c1:
        country = st.text_input("Country/Region", value="India")
        event = st.text_input("Committee/Event", placeholder="e.g. Youth Policy Conclave 2026")
        name = st.text_input("Participant name", placeholder="Your name")
    with c2:
        institution = st.text_input("Institution", placeholder="Your college/university")
    map_clicked = st.form_submit_button("🗺️ Map this topic to SDGs", use_container_width=True)

if map_clicked:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    elif not api_key:
        st.error(
            "Add your Gemini API key in the sidebar. "
            "Get one free at https://aistudio.google.com/apikey"
        )
    else:
        with st.spinner("Classifying your topic against the 17 SDGs…"):
            mapping = run_classification(topic.strip(), country.strip(), api_key, model)
        st.session_state.sdg_mapping = mapping
        st.session_state.classified_topic = topic.strip()
        st.session_state.result = None

# --------------------------------------------------------------------------
# Step 1 result: SDG mapping (+ editable derived fields)
# --------------------------------------------------------------------------
mapping: SDGMapping | None = st.session_state.sdg_mapping
if mapping and st.session_state.classified_topic:
    if mapping.method == "keyword-fallback":
        st.warning(
            "LLM classification was unavailable, so a keyword-based fallback was used. "
            "Review the mapping carefully."
        )
    st.subheader("📍 SDG Mapping")
    cols = st.columns([2, 1])
    with cols[0]:
        for line in mapping.display_lines():
            st.markdown("- " + line)
        st.info(f"**Why these goals:** {mapping.rationale}")
    with cols[1]:
        primary_badges = " ".join(
            f"`Goal {n}`" for n in mapping.primary
        )
        st.metric("Primary SDG(s)", primary_badges.replace("`", ""))
        st.metric("Secondary SDG(s)", ", ".join(f"Goal {n}" for n in mapping.secondary) or "—")

    with st.form("details_form"):
        st.markdown("**Adjust derived fields (optional)**")
        title = st.text_input("Paper title", value=mapping.suggested_title or "")
        policy_area = st.text_input("Policy area", value=mapping.policy_area)
        keywords_raw = st.text_input(
            "Research keywords (comma-separated)", value=", ".join(mapping.keywords)
        )
        generate_clicked = st.form_submit_button(
            "🔬 Research & Draft Policy Paper", use_container_width=True
        )

    if generate_clicked:
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        meta = PaperMeta(
            topic=st.session_state.classified_topic,
            title=title,
            policy_area=policy_area,
            country_region=country,
            committee_event=event,
            participant_name=name,
            institution=institution,
            keywords=keywords,
        )
        status_box = st.status("Working… this takes a few minutes.", expanded=True)
        result = None
        try:
            for event_ in run_pipeline(meta, mapping, api_key, model, depth):
                if event_["stage"] == "error":
                    status_box.update(label="Something went wrong", state="error")
                    st.error(event_["text"])
                    break
                status_box.write(event_["text"])
                if event_["stage"] == "done":
                    result = event_["data"]
            if result is not None:
                status_box.update(
                    label=f"✅ Policy paper ready — {result.word_count:,} words, "
                    f"{len(result.sources)} sources",
                    state="complete",
                )
                st.session_state.result = result
        except Exception as exc:  # noqa: BLE001
            status_box.update(label="Failed", state="error")
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg.lower() or "quota" in msg.lower():
                st.error(
                    "Gemini free-tier quota was hit. Wait a minute and try again, "
                    "or switch to 'gemini-2.5-flash-lite' in the sidebar.\n\n" + msg
                )
            else:
                st.error(msg)

# --------------------------------------------------------------------------
# Step 2 result: the paper
# --------------------------------------------------------------------------
result = st.session_state.result
if result is not None:
    st.divider()
    st.subheader("📄 Your policy paper draft")
    m1, m2, m3 = st.columns(3)
    m1.metric("Words (body)", f"{result.word_count:,}")
    m2.metric("Sources researched", len(result.sources))
    m3.metric(
        "Primary SDG",
        "; ".join(f"Goal {n}" for n in result.sdg.primary),
    )

    tab_preview, tab_download, tab_research = st.tabs(
        ["📖 Preview", "⬇️ Download", "🔎 Evidence base"]
    )

    with tab_preview:
        st.markdown(result.markdown)

    with tab_download:
        with open(result.docx_path, "rb") as f:
            docx_bytes = f.read()
        with open(result.md_path, "rb") as f:
            md_bytes = f.read()
        st.download_button(
            "⬇️ Download Word (.docx)",
            docx_bytes,
            file_name=result.docx_path.split("/")[-1],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Download Markdown (.md)",
            md_bytes,
            file_name=result.md_path.split("/")[-1],
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption(
            "The .docx has a formatted cover page, 1.5 spacing, Times New Roman, "
            "real tables, hanging-indent references and page numbers."
        )

    with tab_research:
        st.markdown("**Search queries used**")
        for q in result.queries:
            st.markdown(f"- {q}")
        st.markdown("**Sources read & cited**")
        for i, s in enumerate(result.sources, 1):
            st.markdown(f"{i}. {s.cite_key} — [{s.title}]({s.url})")

    st.caption(
        "💡 Tip: regenerate at a deeper setting for a longer paper, or edit the "
        "title/policy area above and rerun. Verify facts & references before submitting."
    )
