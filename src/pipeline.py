"""Orchestrates the full agent run:

    topic → SDG mapping → deep research → section-by-section writing
          → references → markdown + DOCX export

`run_pipeline` is a generator yielding event dicts so the Streamlit UI can
show live progress:

    {"stage": ..., "text": human readable line, "data": optional payload}
    final event: {"stage": "done", "data": PipelineResult}
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import DEPTH_PRESETS, PaperMeta
from .docx_export import markdown_to_docx
from .llm import LLMClient
from .research import Source, build_digest, deep_research
from .sdg_classifier import SDGMapping, classify_sdg
from .sdg_data import sdg_label
from .structure import BODY_SECTIONS
from .writer import (
    Section,
    assemble_markdown,
    build_references,
    write_annexures,
    write_body_section,
    write_executive_summary,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


@dataclass
class PipelineResult:
    meta: PaperMeta
    sdg: SDGMapping
    sources: list[Source]
    queries: list[str]
    markdown: str
    word_count: int
    docx_path: str
    md_path: str
    sections: list[Section] = field(default_factory=list)


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(s) > max_len:
        s = s[:max_len]
        if "-" in s:  # cut at the last full word, not mid-word
            s = s[: s.rfind("-")]
    return s.rstrip("-") or "policy-paper"


def ev(stage: str, text: str, data=None) -> dict:
    return {"stage": stage, "text": text, "data": data}


def run_pipeline(
    meta: PaperMeta,
    sdg: SDGMapping,
    api_key: str,
    model: str = "gemini-3-flash",
    depth: str = "Standard (~4,500 words)",
):
    """Full run assuming the SDG mapping has already been done/confirmed."""
    preset = DEPTH_PRESETS.get(depth, DEPTH_PRESETS["Standard (~4,500 words)"])
    llm = LLMClient(api_key=api_key, model=model)

    # ------------------------------------------------------------------ 2. research
    yield ev("research", "Starting deep research…")
    messages: list[str] = []

    def progress(msg: str):
        messages.append(msg)

    n_queries = preset["n_queries"]
    results_per_query = preset["results_per_query"]
    max_sources = preset["max_sources"]
    word_multiplier = preset["word_multiplier"]

    sdg_labels = [sdg_label(n) for n in sdg.primary + sdg.secondary]
    research_events = []

    def streamed(msg: str):
        research_events.append(msg)

    # deep_research logs into `streamed`; we then relay them as events.
    import threading

    done_flag = threading.Event()
    sources: list[Source] = []
    queries: list[str] = []
    error: list[Exception] = []

    def _work():
        try:
            s, q = deep_research(
                topic=meta.topic,
                country=meta.country_region,
                sdg_labels=sdg_labels,
                keywords=meta.keywords or sdg.keywords,
                llm=llm,
                n_queries=n_queries,
                results_per_query=results_per_query,
                max_sources=max_sources,
                progress=streamed,
            )
            sources.extend(s)
            queries.extend(q)
        except Exception as e:  # noqa: BLE001
            error.append(e)
        finally:
            done_flag.set()

    t = threading.Thread(target=_work, daemon=True)
    t.start()
    seen = 0
    while not done_flag.is_set():
        while seen < len(research_events):
            yield ev("research", research_events[seen])
            seen += 1
        time.sleep(0.25)
    while seen < len(research_events):
        yield ev("research", research_events[seen])
        seen += 1
    if error:
        yield ev("error", f"Research failed: {error[0]}")
        return
    if len(sources) < 3:
        yield ev(
            "error",
            "Deep research could not gather enough sources (got "
            f"{len(sources)}; need at least 3 to build a credible paper). "
            "This usually means the network blocked the search engines or they "
            "are rate-limiting. Check your internet connection, wait a few "
            "minutes, and try again. No paper was written.",
        )
        return
    yield ev("research", f"Evidence base ready: {len(sources)} sources.", data=sources)

    digest = build_digest(sources, per_source_chars=1100)

    # ------------------------------------------------------------------ 3. writing
    yield ev("write", f"Drafting {len(BODY_SECTIONS) + 2} sections with {model}…")
    body_sections: list[Section] = []
    for spec in BODY_SECTIONS:
        yield ev("write", f"✍️ Writing section {spec['number']}: {spec['title']}…")
        section = write_body_section(
            spec, meta, sdg, digest, body_sections, llm,
            word_multiplier=word_multiplier,
        )
        body_sections.append(section)
        yield ev("write", f"✅ Section {spec['number']} done ({len(section.markdown.split())} words).")

    yield ev("write", "✍️ Writing Annexures…")
    annexures = write_annexures(meta, sdg, body_sections, llm)

    yield ev("write", "✍️ Writing Executive Summary (last, so it truly summarises)…")
    exec_summary = write_executive_summary(
        meta, sdg, body_sections, llm, word_multiplier=word_multiplier
    )

    # ------------------------------------------------------------------ 4. references
    references = build_references(sources)
    n_refs = len({s.apa for s in sources if s.apa})
    yield ev("write", f"📚 Reference list built: {n_refs} APA entries from researched sources.")

    # ------------------------------------------------------------------ 5. assemble & export
    markdown, body_words = assemble_markdown(
        meta, exec_summary, body_sections, annexures, references
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(meta.title_or_default())
    md_path = OUTPUT_DIR / f"{slug}.md"
    docx_path = OUTPUT_DIR / f"{slug}.docx"
    md_path.write_text(markdown, encoding="utf-8")
    yield ev("export", "📝 Building Word document…")
    markdown_to_docx(meta, markdown, str(docx_path))

    result = PipelineResult(
        meta=meta,
        sdg=sdg,
        sources=sources,
        queries=queries,
        markdown=markdown,
        word_count=body_words,
        docx_path=str(docx_path),
        md_path=str(md_path),
        sections=[exec_summary, *body_sections, references, annexures],
    )
    yield ev("done", f"Done — {body_words:,} words, {len(sources)} sources.", data=result)


def run_classification(topic: str, country: str, api_key: str, model: str) -> SDGMapping:
    """Step 1 used by the UI (kept separate so the user can review the mapping)."""
    llm = LLMClient(api_key=api_key, model=model)
    return classify_sdg(topic, llm, country)
