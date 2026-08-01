"""Streaming orchestration for negotiation mode (playbook + practice)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .config import DEPTH_PRESETS
from .docx_export import markdown_to_docx
from .llm import LLMClient
from .negotiation import (
    NegoMeta,
    analyze_scenario,
    assemble_playbook_markdown,
    assemble_practice_markdown,
    design_practice_scenario,
    negotiation_queries,
    PLAYBOOK_SECTIONS,
    write_judge_note,
    write_playbook_section,
    write_shared_brief,
    write_team_brief,
)
from .pipeline import OUTPUT_DIR, ev, slugify
from .research import Source, build_digest


@dataclass
class NegoResult:
    kind: str                      # 'playbook' | 'practice'
    title: str
    markdown: str
    word_count: int
    docx_path: str
    md_path: str
    sources: list[Source] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)


def research_with_queries(queries: list[str], n_results: int, max_sources: int, progress) -> list[Source]:
    """Run a fixed query list through the shared research machinery."""
    from .research import ddg_search, fetch_page_text, Source, publisher_for, _base_domain, _score
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .research import _assign_cite_keys, format_apa, REQUEST_TIMEOUT

    found: dict[str, dict] = {}
    for i, q in enumerate(queries, 1):
        progress(f"🔎 [{i}/{len(queries)}] {q}")
        hits, err = ddg_search(q, max_results=n_results)
        if err:
            progress(f"   ⚠️ search issue: {err[:140]}")
        for hit in hits:
            found.setdefault(hit["url"], hit)
        time.sleep(0.7)

    if not found:
        progress("⛔ Web search returned nothing (network blocked or engines rate-limited).")
        return []

    candidates = []
    for hit in found.values():
        domain = _base_domain(hit["url"])
        candidates.append((hit, domain, _score(domain, hit["url"])))
    candidates.sort(key=lambda t: t[2], reverse=True)
    pool = candidates[: max_sources * 2]

    progress(f"📚 Reading {min(len(pool), max_sources * 2)} pages…")
    results: list[Source] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(fetch_page_text, hit["url"]): (hit, domain, score)
            for (hit, domain, score) in pool
        }
        for fut in as_completed(futures):
            hit, domain, score = futures[fut]
            try:
                text, published = fut.result(timeout=REQUEST_TIMEOUT + 8)
            except Exception:  # noqa: BLE001
                text, published = "", ""
            results.append(Source(
                title=hit["title"], url=hit["url"], domain=domain,
                publisher=publisher_for(domain), published=published,
                snippet=hit.get("snippet", ""), text=text,
                rank_score=score + (1.0 if len(text) > 1200 else 0.0),
            ))
    results.sort(key=lambda s: s.rank_score, reverse=True)
    sources = results[:max_sources]
    _assign_cite_keys(sources)
    for s in sources:
        s.apa = format_apa(s)
    return sources


def _stream_thread(fn, progress_list: list[str]):
    """Run fn() in a thread while the caller threads progress events out."""
    holder: dict = {}
    error: list[Exception] = []
    done = threading.Event()

    def _work():
        try:
            holder["value"] = fn()
        except Exception as e:  # noqa: BLE001
            error.append(e)
        finally:
            done.set()

    return holder, error, done, threading.Thread(target=_work, daemon=True)


# ---------------------------------------------------------------------------
# PLAYBOOK MODE
# ---------------------------------------------------------------------------

def run_playbook_pipeline(meta: NegoMeta, api_key: str, model: str, depth: str):
    preset = DEPTH_PRESETS.get(depth, DEPTH_PRESETS["Standard (~4,500 words)"])
    rapid = "Rapid" in depth or "Quick" in depth
    n_queries = 6 if rapid else preset["n_queries"]
    per_query = 3 if rapid else preset["results_per_query"]
    max_sources = 10 if rapid else preset["max_sources"]
    word_multiplier = min(preset["word_multiplier"], 1.0) if rapid else preset["word_multiplier"]

    llm = LLMClient(api_key=api_key, model=model)

    # ------------------------------------------------ analyze
    yield ev("analyze", "🧠 Reading the scenario brief…")
    analysis = analyze_scenario(
        meta.brief_text, meta.your_stakeholder, meta.other_parties, meta.region, llm
    )
    meta.scenario_title = meta.scenario_title or str(analysis.get("title", "")).strip()
    yield ev(
        "analyze",
        f"🗺️ Scenario decoded: **{meta.title_or_default()}** — "
        f"{len(analysis.get('issue_areas', []) or [])} issue areas, "
        f"{len(analysis.get('parties', []) or [])} parties.",
        data=analysis,
    )

    # ------------------------------------------------ research
    queries = negotiation_queries(
        analysis, meta.your_stakeholder, meta.other_parties, meta.region, n_queries, llm
    )
    progress: list[str] = []
    holder, error, done, t = _stream_thread(
        lambda: research_with_queries(queries, per_query, max_sources, progress.append),
        progress,
    )
    t.start()
    seen = 0
    while not done.is_set():
        while seen < len(progress):
            yield ev("research", progress[seen]); seen += 1
        time.sleep(0.25)
    while seen < len(progress):
        yield ev("research", progress[seen]); seen += 1
    if error:
        yield ev("error", f"Research failed: {error[0]}")
        return
    sources: list[Source] = holder.get("value", [])
    if len(sources) < 3:
        yield ev(
            "error",
            "Research gathered too few sources (network may be blocking the "
            "search engines). Check your connection and retry — the playbook "
            "needs real-world facts to be worth anything at the table.",
        )
        return
    yield ev("research", f"✅ Evidence base ready: {len(sources)} sources.", data=sources)
    digest = build_digest(sources, per_source_chars=1100)

    # ------------------------------------------------ write sections
    sections: list[str] = []
    for spec in PLAYBOOK_SECTIONS:
        yield ev("write", f"✍️ Section {spec['number']}: {spec['title']}…")
        sec = write_playbook_section(
            spec, meta, analysis, digest, sections, llm,
            word_multiplier=word_multiplier,
        )
        sections.append(sec)
        yield ev("write", f"✅ Section {spec['number']} done.")

    # ------------------------------------------------ assemble & export
    markdown, wc = assemble_playbook_markdown(meta, sections, sources)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(f"{meta.title_or_default()}-playbook")
    md_path = OUTPUT_DIR / f"{slug}.md"
    docx_path = OUTPUT_DIR / f"{slug}.docx"
    md_path.write_text(markdown, encoding="utf-8")
    yield ev("export", "📝 Building Word document…")
    cover_fields = [
        ("Scenario", meta.title_or_default()),
        ("Your Stakeholder", meta.your_stakeholder or "—"),
        ("Other Parties", meta.other_parties or "—"),
        ("Round", meta.round_name or "—"),
        ("Team", meta.team_members or "—"),
        ("Institution", meta.institution or "—"),
        ("Time Limit", meta.time_limit or "—"),
        ("Words", f"approximately {wc:,}"),
    ]
    markdown_to_docx(meta, markdown, str(docx_path),
                     cover_fields=cover_fields, subtitle="Negotiation Playbook")
    yield ev("done", f"Playbook ready — {wc:,} words, {len(sources)} sources.",
             data=NegoResult(
                 kind="playbook", title=meta.title_or_default(), markdown=markdown,
                 word_count=wc, docx_path=str(docx_path), md_path=str(md_path),
                 sources=sources, queries=queries, analysis=analysis,
             ))


# ---------------------------------------------------------------------------
# PRACTICE GENERATOR MODE
# ---------------------------------------------------------------------------

def run_practice_pipeline(category: str, difficulty: str, region: str,
                          with_research: bool, api_key: str, model: str):
    llm = LLMClient(api_key=api_key, model=model)

    yield ev("design", "🎲 Designing the match scenario…")
    try:
        design = design_practice_scenario(category, difficulty, region, llm)
    except Exception as exc:  # noqa: BLE001
        yield ev("error", f"Scenario design failed: {exc}")
        return
    title = str(design.get("title", "Practice Scenario"))
    yield ev("design", f"🗺️ Scenario: **{title}** — {design.get('setting', '')}", data=design)

    digest = ""
    sources: list[Source] = []
    if with_research:
        kw = [title, f"{_short_cat(category)} {region}"] + [
            str(x) for x in (design.get("issue_dimensions") or [])[:3]
        ]
        queries = []
        for x in kw[:5]:
            queries.append(x if len(x) > 25 else f"{x} facts data")
        progress: list[str] = []
        holder, error, done, t = _stream_thread(
            lambda: research_with_queries(queries, 3, 8, progress.append), progress
        )
        t.start()
        seen = 0
        while not done.is_set():
            while seen < len(progress):
                yield ev("research", progress[seen]); seen += 1
            time.sleep(0.25)
        while seen < len(progress):
            yield ev("research", progress[seen]); seen += 1
        sources = holder.get("value", []) if not error else []
        digest = build_digest(sources, per_source_chars=700) if sources else ""
        if sources:
            yield ev("research", f"✅ Grounded in {len(sources)} real-world sources.", data=sources)
        else:
            yield ev("research", "ℹ️ Research unavailable — briefs will use plausible fictional data.")

    yield ev("write", "✍️ Writing the shared match brief…")
    shared = write_shared_brief(design, difficulty, digest, llm)
    yield ev("write", "🔒 Writing Team A confidential brief…")
    brief_a = write_team_brief(design, "team_a", difficulty, digest, llm)
    yield ev("write", "🔒 Writing Team B confidential brief…")
    brief_b = write_team_brief(design, "team_b", difficulty, digest, llm)
    yield ev("write", "⚖️ Writing judge's solution note…")
    judge = write_judge_note(design, llm)

    markdown = assemble_practice_markdown(shared, brief_a, brief_b, judge)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(f"practice-{title}")
    md_path = OUTPUT_DIR / f"{slug}.md"
    docx_path = OUTPUT_DIR / f"{slug}.docx"
    md_path.write_text(markdown, encoding="utf-8")
    yield ev("export", "📝 Building Word document…")
    meta = NegoMeta(scenario_title=title, team_members="Practice match pack")
    from .writer import word_count as _wc

    wc = _wc(markdown)
    meta.word_count = wc
    cover_fields = [
        ("Scenario", title),
        ("Category", category.split("(")[0].strip()),
        ("Difficulty", difficulty.split("(")[0].strip()),
        ("Region", region),
        ("Contains", "Match brief + 2 confidential team briefs + judge's note"),
        ("Words", f"approximately {wc:,}"),
    ]
    markdown_to_docx(meta, markdown, str(docx_path),
                     cover_fields=cover_fields, subtitle="Practice Match Pack")
    yield ev("done", f"Practice match ready — {wc:,} words.",
             data=NegoResult(
                 kind="practice", title=title, markdown=markdown, word_count=wc,
                 docx_path=str(docx_path), md_path=str(md_path),
                 sources=sources, analysis=design,
             ))


# ---------------------------------------------------------------------------
# COMPACT PLAYBOOK — paste round brief -> 1-2 page negotiation-points doc
# ---------------------------------------------------------------------------

def run_compact_playbook(meta: NegoMeta, api_key: str, model: str):
    from .negotiation import write_compact_playbook
    from .writer import word_count as _wc

    llm = LLMClient(api_key=api_key, model=model)
    yield ev("write", "✍️ Building your 1-2 page negotiation-points document…")
    markdown = write_compact_playbook(meta, llm)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(f"negotiation-points-{meta.title_or_default()}")
    md_path = OUTPUT_DIR / f"{slug}.md"
    docx_path = OUTPUT_DIR / f"{slug}.docx"
    md_path.write_text(markdown, encoding="utf-8")
    yield ev("export", "📝 Building Word document…")
    wc = _wc(markdown)
    meta.word_count = wc
    cover_fields = [
        ("Scenario", meta.title_or_default()),
        ("Your side", meta.your_stakeholder or "—"),
        ("Other parties", meta.other_parties or "—"),
        ("Round", meta.round_name or "—"),
        ("Time limit", meta.time_limit or "—"),
        ("Words", f"approximately {wc:,}"),
    ]
    markdown_to_docx(meta, markdown, str(docx_path),
                     cover_fields=cover_fields, subtitle="Negotiation Points — 1-2 Pages")
    yield ev("done", f"Ready — {wc:,} words (1-2 pages).",
             data=NegoResult(
                 kind="playbook", title=meta.title_or_default(), markdown=markdown,
                 word_count=wc, docx_path=str(docx_path), md_path=str(md_path),
             ))


# ---------------------------------------------------------------------------
# COMPACT PRACTICE MODE — pick an idea -> 1-2 page negotiation document
# ---------------------------------------------------------------------------

def run_compact_practice(idea: dict, category: str, difficulty: str, region: str,
                         api_key: str, model: str):
    from .negotiation import write_compact_practice_doc
    from .writer import word_count as _wc

    llm = LLMClient(api_key=api_key, model=model)
    title = idea.get("title", "Practice Negotiation")
    yield ev("write", f"✍️ Writing your 1-2 page negotiation document for **{title}**…")
    markdown = write_compact_practice_doc(idea, category, difficulty, region, llm)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(f"negotiation-doc-{title}")
    md_path = OUTPUT_DIR / f"{slug}.md"
    docx_path = OUTPUT_DIR / f"{slug}.docx"
    md_path.write_text(markdown, encoding="utf-8")
    yield ev("export", "📝 Building Word document…")
    wc = _wc(markdown)
    meta = NegoMeta(scenario_title=title)
    meta.word_count = wc
    cover_fields = [
        ("Scenario", title),
        ("Sides", f"{idea.get('side_a', '—')}  vs  {idea.get('side_b', '—')}"),
        ("Category", category.split("(")[0].strip()),
        ("Difficulty", difficulty.split("(")[0].strip()),
        ("Words", f"approximately {wc:,}"),
    ]
    markdown_to_docx(meta, markdown, str(docx_path),
                     cover_fields=cover_fields, subtitle="Practice Negotiation Document")
    yield ev("done", f"Ready — {wc:,} words (1-2 pages).",
             data=NegoResult(
                 kind="practice", title=title, markdown=markdown, word_count=wc,
                 docx_path=str(docx_path), md_path=str(md_path),
             ))


def _short_cat(category: str) -> str:
    return category.split("(")[0].strip()
