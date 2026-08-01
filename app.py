"""SDG Policy Paper + Diplomatic Negotiation Agent — Streamlit UI.

Run:  streamlit run app.py   (or double-click run.bat)

Modes:
  🤝 Negotiation  — playbook from a pasted round brief + practice match generator
  📄 Policy Paper — SDG mapping → deep research → full policy paper draft
"""

from __future__ import annotations

import streamlit as st

from src.config import DEPTH_PRESETS, DEFAULT_MODEL, PaperMeta
from src.pipeline import run_classification, run_pipeline
from src.sdg_classifier import SDGMapping
from src.negotiation import (
    CATEGORIES,
    DIFFICULTY_PROFILES,
    NegoMeta,
    _stringify,
)
from src.neg_pipeline import (
    run_compact_playbook,
    run_compact_practice,
    run_playbook_pipeline,
    run_practice_pipeline,
)

st.set_page_config(
    page_title="SDG Policy Paper + Negotiation Agent",
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
    ("neg_result", None),
    ("practice_result", None),
    ("practice_ideas", None),
):
    st.session_state.setdefault(key, default)


def _default_key() -> str:
    from src.config import env_api_key as _env

    key = _env()
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:  # noqa: BLE001 - no secrets.toml present
        return ""


# --------------------------------------------------------------------------
# Sidebar (shared across modes)
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Policy + Negotiation Agent")
    st.caption("Deep research → SDG policy papers · negotiation playbooks · practice matches")
    st.divider()

    st.subheader("🔑 Gemini API")
    st.markdown("Free key: [Google AI Studio](https://aistudio.google.com/apikey)")
    api_key = st.text_input(
        "API key", value=_default_key(), type="password", placeholder="AIza..."
    )
    model = st.text_input(
        "Model",
        value=DEFAULT_MODEL,
        help="If you get a 404 NOT_FOUND error, use the detector below — the app "
        "also auto-switches to an available model when it can.",
    )
    with st.expander("🔍 Detect models my key supports"):
        st.caption("Asks your API key exactly which model IDs work (Google ListModels).")
        detect_clicked = st.button("List available models", use_container_width=True)
    if detect_clicked:
        if not api_key:
            st.warning("Paste your API key above first.")
        else:
            from src.llm import available_models_for_key

            with st.spinner("Asking Google which models your key can use…"):
                try:
                    models = available_models_for_key(api_key.strip())
                    if models:
                        st.success("Your key supports these — copy one into the Model box:")
                        st.code("\n".join(models[:12]), language="text")
                    else:
                        st.warning("No Gemini text models found for this key.")
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc)[:400])
    depth = st.radio("Research depth & length", list(DEPTH_PRESETS.keys()), index=1)
    st.divider()
    st.subheader("🧭 Modes")
    st.markdown(
        "🤝 **Negotiation** — paste the round's brief → strategy playbook; "
        "or generate practice matches for your 2-person team.\n\n"
        "📄 **Policy Paper** — topic → SDG mapping → evidence-backed paper."
    )
    st.caption("⚠️ Verify facts & quotes before using them in a real round.")


def _render_error(exc: Exception) -> None:
    msg = str(exc)
    if "NOT_FOUND" in msg or "no longer available" in msg.lower() or "404" in msg:
        st.error(
            "That Gemini model ID was rejected by Google. Use the sidebar's "
            "**Detect models** button (or the auto-fallback already tried) and "
            "copy a supported ID into **Model**, then retry.\n\n" + msg
        )
    elif "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        st.error(
            "Gemini free-tier quota was hit. Wait a minute and retry, lower the "
            "depth, or switch the model in the sidebar.\n\n" + msg
        )
    else:
        st.error(msg)


def _show_document(title: str, markdown: str, docx_path: str, md_path: str,
                   sources, queries, analysis, kind: str) -> None:
    st.subheader(title)
    m1, m2, m3 = st.columns(3)
    m1.metric("Words", f"{len(markdown.split()):,}")
    m2.metric("Sources", len(sources or []))
    m3.metric("Type", "Playbook" if kind == "playbook" else ("Practice match" if kind == "practice" else "Policy paper"))

    tab_preview, tab_download, tab_research = st.tabs(["📖 Preview", "⬇️ Download", "🔎 Evidence & details"])
    with tab_preview:
        st.markdown(markdown)
    with tab_download:
        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        with open(md_path, "rb") as f:
            md_bytes = f.read()
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download Word (.docx)", docx_bytes,
                           file_name=docx_path.split("/")[-1],
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
        c2.download_button("⬇️ Download Markdown (.md)", md_bytes,
                           file_name=md_path.split("/")[-1], mime="text/markdown",
                           use_container_width=True)
        st.caption("The .docx has a formatted cover page, real tables and page numbers.")
    with tab_research:
        if analysis:
            with st.expander("🗺️ Scenario analysis", expanded=kind == "playbook"):
                if analysis.get("summary"):
                    st.write(analysis["summary"])
                if analysis.get("issue_areas"):
                    st.markdown("**Issue areas:** " + ", ".join(map(str, analysis["issue_areas"])))
                if analysis.get("parties"):
                    st.markdown("**Parties:** " + ", ".join(map(str, analysis["parties"])))
                if analysis.get("real_world_analogs"):
                    st.markdown("**Real-world analogs:** " + ", ".join(map(str, analysis["real_world_analogs"])))
                if analysis.get("agreement_space"):
                    st.markdown("**Agreement space (judges' eyes):** " + _stringify(analysis["agreement_space"]))
        if queries:
            st.markdown("**Search queries used**")
            for q in queries:
                st.markdown(f"- {q}")
        if sources:
            st.markdown("**Sources read & cited**")
            for i, s in enumerate(sources, 1):
                st.markdown(f"{i}. {s.cite_key} — [{s.title}]({s.url})")


# --------------------------------------------------------------------------
# Mode switcher
# --------------------------------------------------------------------------
mode = st.radio(
    "Mode",
    ["🤝 Diplomatic Negotiation", "📄 SDG Policy Paper"],
    index=0,
    horizontal=True,
)
st.divider()


# ==========================================================================
#  NEGOTIATION MODE
# ==========================================================================
if mode.startswith("🤝"):
    tab_play, tab_prac = st.tabs(["⚡ Playbook from a brief", "🎲 Practice scenario generator"])

    # ------------------------------- Playbook ------------------------------
    with tab_play:
        st.subheader("⚡ Negotiation Points from a Brief")
        st.write(
            "The moment you receive the round's scenario brief, paste it below. "
            "You'll get a **1-2 page negotiation document**: both sides' fundamentals, "
            "your red lines, the **4-5 points of negotiation** in a point-by-point table, "
            "and the **4-5 final agreement points** to steer toward. Ready in ~1 minute."
        )
        with st.form("playbook_form"):
            brief = st.text_area(
                "Scenario brief (paste full text) — or a one-line scenario *",
                key="pb_brief", height=170,
                placeholder="e.g. Two riparian states must renegotiate the Parambhik river treaty after a drought year…",
            )
            c1, c2 = st.columns(2)
            with c1:
                stakeholder = st.text_input("Your stakeholder/role", key="pb_side",
                                            placeholder="e.g. Ministry of Water, Republic of Aranya")
                parties = st.text_input("Other parties (comma-separated)", key="pb_others")
            with c2:
                round_name = st.text_input("Round", key="pb_round",
                                           placeholder="Preliminary / Quarterfinal / Semifinal / Grand Final")
                time_limit = st.text_input("Time limit", key="pb_time", placeholder="e.g. 45 minutes")
            go = st.form_submit_button("⚡ Get my negotiation points (1-2 pages)", use_container_width=True)

        if go:
            if not brief.strip():
                st.warning("Paste a scenario brief or write at least one line about the scenario.")
            elif not api_key:
                st.error("Add your Gemini API key in the sidebar (free: https://aistudio.google.com/apikey).")
            else:
                meta = NegoMeta(
                    brief_text=brief.strip(),
                    your_stakeholder=stakeholder,
                    other_parties=parties,
                    round_name=round_name,
                    time_limit=time_limit,
                    topic=brief.strip()[:80],
                )
                status_box = st.status("Building your negotiation points…", expanded=True)
                result = None
                try:
                    for event_ in run_compact_playbook(meta, api_key.strip(), model.strip()):
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

        neg_result = st.session_state.neg_result
        if neg_result is not None:
            st.divider()
            _show_document(
                f"📋 {neg_result.title}", neg_result.markdown,
                neg_result.docx_path, neg_result.md_path, neg_result.sources,
                neg_result.queries, None, "playbook",
            )

    # ------------------------------- Practice ------------------------------
    with tab_prac:
        st.header("🎲 Practice Generator")
        st.write(
            "**Step 1:** get **2-3 short practice topics** (2-3 lines each). "
            "**Step 2:** pick one → the agent writes a compact **1-2 page negotiation "
            "document**: both sides' stands, a **point-by-point negotiation of 4-5 "
            "issues**, and the **4-5 final points** the deal lands on."
        )
        with st.form("practice_ideas_form"):
            category = st.selectbox("Scenario category", CATEGORIES, key="pr_cat")
            difficulty = st.selectbox("Difficulty level", list(DIFFICULTY_PROFILES.keys()), key="pr_diff")
            c1, c2 = st.columns(2)
            with c1:
                pr_region = st.text_input("Region flavour", value="South Asia", key="pr_region")
            ideas_clicked = st.form_submit_button("💡 Get 2-3 practice topics", use_container_width=True)

        if ideas_clicked:
            if not api_key:
                st.error("Add your Gemini API key in the sidebar (free: https://aistudio.google.com/apikey).")
            else:
                from src.llm import LLMClient
                from src.negotiation import suggest_practice_topics

                with st.spinner("Thinking up practice scenarios…"):
                    try:
                        ideas = suggest_practice_topics(
                            category, difficulty, pr_region,
                            LLMClient(api_key=api_key.strip(), model=model.strip()),
                        )
                        st.session_state.practice_ideas = {
                            "ideas": ideas,
                            "category": category,
                            "difficulty": difficulty,
                            "region": pr_region,
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
                choice = st.radio("Pick a topic for the document", options, key="pr_choice",
                                  horizontal=True)
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
                        idea, pack["category"], pack["difficulty"], pack["region"],
                        api_key.strip(), model.strip(),
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

        practice_result = st.session_state.practice_result
        if practice_result is not None:
            st.divider()
            st.info("📄 Compact 1-2 page document — print it, split the team briefs between you and your teammate, and start the clock.")
            _show_document(
                f"🎲 {practice_result.title}",
                practice_result.markdown, practice_result.docx_path,
                practice_result.md_path, practice_result.sources, None,
                None, "practice",
            )


# ==========================================================================
#  POLICY PAPER MODE (original flow)
# ==========================================================================
else:
    st.header("📄 Policy Paper Draft Agent")
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
                mapping = run_classification(topic.strip(), country.strip(), api_key.strip(), model.strip())
            st.session_state.sdg_mapping = mapping
            st.session_state.classified_topic = topic.strip()
            st.session_state.result = None

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
            st.metric("Primary SDG(s)", ", ".join(f"Goal {n}" for n in mapping.primary))
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
                for event_ in run_pipeline(meta, mapping, api_key.strip(), model.strip(), depth):
                    if event_["stage"] == "error":
                        status_box.update(label="Something went wrong", state="error")
                        st.error(event_["text"])
                        break
                    status_box.markdown(event_["text"])
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
                _render_error(exc)

    result = st.session_state.result
    if result is not None:
        st.divider()
        st.subheader("📄 Your policy paper draft")
        m1, m2, m3 = st.columns(3)
        m1.metric("Words (body)", f"{result.word_count:,}")
        m2.metric("Sources researched", len(result.sources))
        m3.metric("Primary SDG", "; ".join(f"Goal {n}" for n in result.sdg.primary))

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
                "⬇️ Download Word (.docx)", docx_bytes,
                file_name=result.docx_path.split("/")[-1],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
            st.download_button(
                "⬇️ Download Markdown (.md)", md_bytes,
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
