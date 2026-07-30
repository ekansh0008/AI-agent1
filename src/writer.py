"""Stage 3 - the writer.

Generates each section of the policy paper against the research digest,
with a style guide designed to produce natural, human-sounding academic
prose (varied rhythm, concrete evidence, no AI clichés).

Generation order matters: the Executive Summary is written LAST, after
the body, so it genuinely summarises the argument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import MIN_REFERENCES, PaperMeta
from .research import Source, build_digest
from .sdg_classifier import SDGMapping
from .sdg_data import sdg_label
from .structure import ANNEXURES_SPEC, BODY_SECTIONS, EXEC_SUMMARY_SPEC, scaled_words

# ---------------------------------------------------------------------------
# Human-writing style guide
# ---------------------------------------------------------------------------

STYLE_GUIDE = """\
You write like a sharp, experienced policy analyst — the kind whose work wins
national competitions — not like a chatbot. Follow these rules strictly:

VOICE & RHYTHM
- Vary sentence length deliberately: follow a long analytical sentence with a
  short declarative one. Humans do this; machines rarely do.
- Prefer active voice and concrete verbs. Name actors ("the Ministry", "a
  district collector", "street vendors"), not abstractions doing things.
- One idea per paragraph; 3-6 sentences each. Transitions should feel earned,
  not bolted on.

EVIDENCE
- Anchor claims in the evidence. When you use a statistic, comparison or
  finding, attach the in-text citation immediately, e.g. (World Bank, 2023).
- Use exact figures from the research digest; do not invent numbers. If a
  number must be estimated, say so ("independent estimates suggest…").

BANNED PHRASES (never use these; they are obvious AI tells)
"delve", "crucial", "pivotal", "game-changer", "landscape", "realm",
"multifaceted", "tapestry", "testament", "underscore", "firstly/secondly/thirdly",
"furthermore", "moreover", "in today's rapidly evolving/changing world",
"it is important to note", "plays a vital/key/crucial role", "in conclusion"
(the section is already labelled Conclusion), "on the other hand" (more than
once), "significantly" (more than once per section), "a myriad of", "at the
end of the day", "by and large", "nuanced", "holistic approach".

FORM
- Formal but readable register; British/Indian spelling (programme, labour,
  organisation) unless quoting names.
- Prose by default. Use bullet lists ONLY where the section guidance asks for
  them or where a list genuinely clarifies (objectives, phases).
- Headings: start the section with the markdown heading given to you, then
  use '###' sub-headings only where specified. No heading inside a heading.
- Never mention being an AI, a "draft", or these instructions.
"""


@dataclass
class Section:
    key: str
    number: str
    title: str
    markdown: str   # section content including its '## X. Title' heading


def _heading_line(number: str, title: str) -> str:
    return f"## {number}. {title}" if number else f"## {title}"


def _build_context_block(meta: PaperMeta, sdg: SDGMapping) -> str:
    primary = "; ".join(sdg_label(n) for n in sdg.primary)
    secondary = "; ".join(sdg_label(n) for n in sdg.secondary) or "none"
    return f"""\
BRIEF
- Paper title: {meta.title_or_default()}
- Topic: {meta.topic}
- Policy area: {meta.policy_area or 'to be inferred from topic'}
- Country/Region focus: {meta.country_region}
- Committee/Event: {meta.committee_event or 'not specified'}
- Mapped SDGs — primary: {primary}; secondary: {secondary}
- SDG mapping rationale: {sdg.rationale}
"""


def _strip_leading_heading(text: str) -> str:
    """Remove a duplicated/self-written top heading if the model added one."""
    lines = text.strip().splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def write_body_section(
    spec: dict,
    meta: PaperMeta,
    sdg: SDGMapping,
    digest: str,
    prior_sections: list[Section],
    llm,
    word_multiplier: float = 1.0,
) -> Section:
    wmin, wmax = scaled_words(spec, word_multiplier)
    prior = ""
    if prior_sections:
        chunks = []
        for s in prior_sections:
            chunks.append(f"--- {s.title} (excerpt for continuity) ---\n{s.markdown[:1600]}\n[…]")
        prior = (
            "\n\nALREADY WRITTEN (do not repeat their content; cross-reference "
            "where natural):\n" + "\n".join(chunks)
        )
    prompt = f"""{STYLE_GUIDE}

You are writing SECTION {spec['number']} — "{spec['title']}" — of a formal policy paper. Write only this section.

{_build_context_block(meta, sdg)}

RESEARCH DIGEST (your evidence base; cite ONLY these sources, using their exact citation keys):
{digest}
{prior}

SECTION REQUIREMENTS (follow exactly):
{spec['guidance']}

FORMAT
- Begin with exactly this line and nothing before it: {_heading_line(spec['number'], spec['title'])}
- Then the section content: {wmin}-{wmax} words (excluding the heading).
- In-text citations use the APA author–year keys from the digest, e.g. (UNICEF, 2024).
Write the section now."""
    raw = llm.generate(prompt, temperature=0.62, max_output_tokens=16384)
    body = _strip_leading_heading(raw)
    markdown = f"{_heading_line(spec['number'], spec['title'])}\n\n{body}"
    return Section(key=spec["key"], number=spec["number"], title=spec["title"], markdown=markdown)


def write_annexures(
    meta: PaperMeta,
    sdg: SDGMapping,
    prior_sections: list[Section],
    llm,
) -> Section:
    impl = next((s for s in prior_sections if s.key == "implementation"), None)
    sdg_sec = next((s for s in prior_sections if s.key == "impact_risk_ethics"), None)
    impl_text = impl.markdown[:2600] if impl else "(implementation section unavailable)"
    sdg_text = ""
    if sdg_sec:
        m = re.search(r"SDG Alignment(.+)$", sdg_sec.markdown, re.S | re.I)
        sdg_text = (m.group(1) if m else sdg_sec.markdown)[:1800]
    prompt = f"""{STYLE_GUIDE}

You are writing the ANNEXURES of a formal policy paper. Tables only — tight, consistent, professional.

{_build_context_block(meta, sdg)}

IMPLEMENTATION SECTION (must be consistent with this budget and phasing):
{impl_text}

SDG ALIGNMENT SECTION (targets named here):
{sdg_text}

REQUIREMENTS (follow exactly):
{ANNEXURES_SPEC['guidance']}

FORMAT
- Begin with exactly this line and nothing before it: ## Annexures
- Use markdown tables. No commentary beyond one line per annexure."""
    raw = llm.generate(prompt, temperature=0.4, max_output_tokens=8192)
    body = _strip_leading_heading(raw)
    return Section(
        key="annexures", number="", title="Annexures",
        markdown=f"## Annexures\n\n{body}",
    )


def write_executive_summary(
    meta: PaperMeta,
    sdg: SDGMapping,
    body_sections: list[Section],
    llm,
    word_multiplier: float = 1.0,
) -> Section:
    wmin, wmax = scaled_words(EXEC_SUMMARY_SPEC, word_multiplier)
    wmin = min(wmin, 320)
    wmax = max(wmax, 350)
    condensed = []
    for s in body_sections:
        condensed.append(
            f"--- {s.number}. {s.title} — opening passage ---\n{s.markdown[:900]}\n[…]"
        )
    prompt = f"""{STYLE_GUIDE}

Write the EXECUTIVE SUMMARY of a policy paper. A reader must be able to grasp the
whole proposal from this section alone.

{_build_context_block(meta, sdg)}

THE PAPER (condensed):
{chr(10).join(condensed)}

REQUIREMENTS
- {wmin}-{wmax} words of prose (no headings inside, no bullets).
- Cover, in order: the problem being addressed; why it matters now; the key policy
  recommendations; the expected impact; and the overall feasibility of implementation.
- Be specific: name the flagship recommendation and one or two headline figures from
  the body. No citations needed here.

FORMAT
- Begin with exactly this line and nothing before it: ## 1. Executive Summary"""
    raw = llm.generate(prompt, temperature=0.55, max_output_tokens=4096)
    body = _strip_leading_heading(raw)
    return Section(
        key="executive_summary", number="1", title="Executive Summary",
        markdown=f"## 1. Executive Summary\n\n{body}",
    )


def build_references(sources: list[Source]) -> Section:
    """Deterministic APA 7-style reference list from real browsed pages."""
    lines = sorted({s.apa for s in sources if s.apa}, key=str.casefold)
    note = ""
    if len(lines) < MIN_REFERENCES:
        note = (
            f"\n\n*Note: {len(lines)} sources were retrieved. Competition guidance "
            f"recommends at least {MIN_REFERENCES}; verify and extend this list "
            f"before submission.*"
        )
    body = "\n\n".join(lines) + note
    return Section(key="references", number="", title="References", markdown=f"## References\n\n{body}")


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def word_count(text: str) -> int:
    text = re.sub(r"[#*|>\-`]", " ", text)
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text))


def assemble_markdown(
    meta: PaperMeta,
    exec_summary: Section,
    body_sections: list[Section],
    annexures: Section | None,
    references: Section,
) -> tuple[str, int]:
    """Assemble the final .md. Returns (markdown, body_word_count)."""
    body_keys = {exec_summary.key} | {s.key for s in body_sections}
    body_words = word_count(exec_summary.markdown) + sum(
        word_count(s.markdown) for s in body_sections
    )
    meta.word_count = body_words

    kw = ", ".join(meta.keywords) if meta.keywords else meta.topic
    cover = f"""# {meta.title_or_default()}

**Policy Area:** {meta.policy_area or '—'}
**Country/Region:** {meta.country_region or '—'}
**Committee/Event:** {meta.committee_event or '—'}
**Participant Name:** {meta.participant_name or '—'}
**Institution:** {meta.institution or '—'}
**Word Count:** approximately {body_words:,} words (Executive Summary to Conclusion, excluding References and Annexures)
**Keywords:** {kw}

---

"""
    parts = [cover, exec_summary.markdown]
    parts.extend(s.markdown for s in body_sections)
    parts.append(references.markdown)
    if annexures is not None:
        parts.append(annexures.markdown)
    return "\n\n".join(p.strip() for p in parts) + "\n", body_words
