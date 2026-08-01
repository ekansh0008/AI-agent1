"""Stage 1 - map a free-form topic to the UN Sustainable Development Goals."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .sdg_data import SDGS, sdg_catalogue_text


@dataclass
class SDGMapping:
    primary: list[int] = field(default_factory=list)       # 1-2 goal numbers
    secondary: list[int] = field(default_factory=list)     # up to 3 goal numbers
    rationale: str = ""
    policy_area: str = ""
    keywords: list[str] = field(default_factory=list)
    suggested_title: str = ""
    method: str = "llm"   # 'llm' or 'keyword-fallback'

    def display_lines(self) -> list[str]:
        lines = []
        for n in self.primary:
            lines.append(f"**Primary — Goal {n}: {SDGS[n]['name']}** — {SDGS[n]['description']}")
        for n in self.secondary:
            lines.append(f"Secondary — Goal {n}: {SDGS[n]['name']}")
        return lines


_CLASSIFY_PROMPT = """You are an expert on the United Nations Sustainable Development Goals (SDGs, the 2030 Agenda).

A participant is writing a policy paper and needs to know where their topic sits within the SDG framework.

Topic: "{topic}"
{country_line}

The 17 SDGs:
{catalogue}

Decide which SDG(s) this topic belongs to.

Rules:
- Choose exactly ONE primary SDG — the single best fit for the core of the topic. Add a second primary ONLY if the topic is genuinely inseparable across two goals.
- Choose up to 3 secondary SDGs that are clearly affected or relevant. Do not pad.
- Suggest a concise "Policy Area" label (3-6 words, e.g. "Urban Solid Waste Management").
- Suggest 6-8 specific research keywords/phrases (not single generic words) that would help a researcher find statistics, laws and reports on this exact topic.
- Suggest an academic policy-paper title (max 14 words) combining a thematic hook and the subject, e.g. "From Scarcity to Security: Groundwater Governance Reform in Punjab".
- Give a one-paragraph rationale (3-5 sentences) citing relevant SDG targets.

Respond with ONLY minified JSON, no markdown fences:
{{"primary":[4],"secondary":[8,17],"rationale":"...","policy_area":"...","keywords":["..."],"title":"..."}}"""


def _valid_number(x, allow_multiple=False) -> bool:
    try:
        n = int(x)
        return 1 <= n <= 17
    except (TypeError, ValueError):
        return False


def classify_sdg(topic: str, llm, country_region: str = "") -> SDGMapping:
    """Classify via the LLM; fall back to keyword scoring on any failure."""
    country_line = (
        f"Country/Region focus: {country_region}" if country_region else ""
    )
    prompt = _CLASSIFY_PROMPT.format(
        topic=topic, country_line=country_line, catalogue=sdg_catalogue_text()
    )
    try:
        data = llm.generate_json(prompt, max_output_tokens=2048)
        primary = [int(n) for n in data.get("primary", []) if _valid_number(n)]
        secondary = [
            int(n)
            for n in data.get("secondary", [])
            if _valid_number(n) and int(n) not in primary
        ][:3]
        if not primary:
            raise ValueError("LLM returned no valid primary SDG")
        return SDGMapping(
            primary=primary[:2],
            secondary=secondary,
            rationale=str(data.get("rationale", "")).strip(),
            policy_area=str(data.get("policy_area", "")).strip(),
            keywords=[str(k).strip() for k in data.get("keywords", [])][:8],
            suggested_title=str(data.get("title", "")).strip(),
            method="llm",
        )
    except Exception:
        return keyword_fallback(topic)


def keyword_fallback(topic: str) -> SDGMapping:
    """Deterministic keyword-overlap classifier (no LLM needed)."""
    tokens = re.findall(r"[a-z][a-z\-]+", topic.lower())
    text = " " + " ".join(tokens) + " "
    scores: dict[int, int] = {}
    for n, goal in SDGS.items():
        score = 0
        for kw in goal["keywords"]:
            if " " in kw:
                if kw.lower() in text:
                    score += 3  # multi-word match is strong evidence
            elif any(kw.lower() == t or t.startswith(kw.lower()[:6]) for t in tokens):
                score += 1
        scores[n] = score
    ranked = sorted(scores, key=lambda n: (-scores[n], n))
    primary = [n for n in ranked if scores[n] > 0][:2] or [ranked[0]]
    secondary = [n for n in ranked if scores[n] > 0 and n not in primary][:3]
    top_names = ", ".join(SDGS[n]["name"] for n in primary)
    return SDGMapping(
        primary=primary,
        secondary=secondary,
        rationale=(
            f"Mapped by keyword matching (offline fallback): the topic's vocabulary "
            f"most closely matches {top_names}. Review this mapping and adjust "
            f"if needed."
        ),
        policy_area=topic.strip().rstrip(".").title(),
        keywords=[topic.strip()],
        suggested_title="",
        method="keyword-fallback",
    )
