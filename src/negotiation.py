"""Negotiation mode — for the Diplomatic Negotiation Challenge.

Two capabilities:
1. PLAYBOOK: paste a scenario brief (or topic) -> deep research -> a full
   strategy playbook: stakeholder map, ranked objectives with BATNA/reservation
   points, concession ladder, coalition plan, evidence-backed argument bank,
   crisis contingencies, draft agreement skeleton, diplomatic phrases, and a
   one-page quick-reference card.
2. PRACTICE GENERATOR: creates realistic practice matches (shared brief + two
   confidential team briefs + judge's solution note) calibrated to the four
   tournament difficulty levels.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .llm import extract_json
from .research import Source, build_digest
from .writer import STYLE_GUIDE, build_references, word_count

NEG_VOICE = """\
CONTEXT OF THIS DOCUMENT
This is a negotiation strategy playbook for a diplomatic simulation judged on:
consensus-building, realism, implementability, adaptability and professional
diplomacy — NOT on stubbornly defending a position. Write for a negotiator who
has minutes to absorb this before walking to the table. Be concrete and
actionable: named moves, specific numbers, exact phrases. Every factual claim
about the real world must cite the evidence digest.
"""


# --------------------------------------------------------------------------
# Metadata
# --------------------------------------------------------------------------

@dataclass
class NegoMeta:
    scenario_title: str = ""
    brief_text: str = ""              # pasted round brief (may be short topic)
    your_stakeholder: str = ""
    other_parties: str = ""
    round_name: str = ""
    team_members: str = ""
    institution: str = ""
    time_limit: str = ""
    agreement_spec: str = ""        # optional venue-announced format: pages/word count/style
    region: str = "South Asia"
    keywords: list[str] = field(default_factory=list)
    word_count: int = 0
    topic: str = ""                   # fallback title source

    def title_or_default(self) -> str:
        return self.scenario_title.strip() or self.topic.strip().rstrip(".") or "Negotiation Playbook"


# --------------------------------------------------------------------------
# Stage A — understand the scenario
# --------------------------------------------------------------------------

_ANALYZE_PROMPT = """You are a veteran diplomat briefing a young negotiator.

The negotiator received this scenario material:
\"\"\"
{brief}
\"\"\"
{extra}

Respond with ONLY minified JSON:
{{
 "title": "short scenario title, max 10 words",
 "summary": "2-3 sentence neutral summary of the situation",
 "issue_areas": ["3-6 issue areas at stake"],
 "parties": ["stakeholders likely at the table, include the negotiator's own side if identifiable"],
 "stakes": "one sentence on why this matters / what failure costs",
 "real_world_analogs": ["1-3 real treaties/disputes this resembles"],
 "keywords": ["6-8 research phrases to find facts, treaties, data and past negotiation outcomes on this kind of dispute"],
 "your_side_hint": "the negotiator's stakeholder as best inferred, or empty"
}}"""


def analyze_scenario(brief: str, your_stakeholder: str, other_parties: str, region: str, llm) -> dict:
    extra_bits = []
    if your_stakeholder:
        extra_bits.append(f"The negotiator represents: {your_stakeholder}")
    if other_parties:
        extra_bits.append(f"Other parties at the table: {other_parties}")
    if region:
        extra_bits.append(f"Regional context: {region}")
    prompt = _ANALYZE_PROMPT.format(brief=brief[:6000], extra="\n".join(extra_bits))
    try:
        data = llm.generate_json(prompt, max_output_tokens=4096)
        if not isinstance(data, dict) or "title" not in data:
            raise ValueError("bad analysis payload")
        return data
    except Exception:  # noqa: BLE001
        return {
            "title": brief.strip().splitlines()[0][:80] if brief.strip() else "Negotiation Scenario",
            "summary": brief.strip()[:400],
            "issue_areas": [],
            "parties": [p.strip() for p in other_parties.split(",") if p.strip()],
            "stakes": "",
            "real_world_analogs": [],
            "keywords": [brief.strip()[:60]] if brief.strip() else [],
            "your_side_hint": your_stakeholder,
        }


# --------------------------------------------------------------------------
# Stage B — research queries tuned for negotiation prep
# --------------------------------------------------------------------------

_QUERY_PROMPT = """You are a research chief for a diplomatic negotiation team.

Scenario: {title}
Summary: {summary}
Your side: {side}
Other parties: {parties}
Region: {region}
Real-world analogs: {analogs}

Generate {n} high-value web search queries to arm negotiators with facts:
- hard data and statistics on the core issue (latest available)
- the real treaties/agreements named as analogs (their key provisions + how disputes were settled)
- the real geopolitical/economic interests of countries resembling the parties
- past negotiation outcomes and what made them succeed or fail
- enabling legal frameworks (international conventions, UN resolutions)

Phrase queries precisely. Respond with ONLY minified JSON: {{"queries":["..."]}}"""


def negotiation_queries(analysis: dict, side: str, parties: str, region: str, n: int, llm) -> list[str]:
    prompt = _QUERY_PROMPT.format(
        title=analysis.get("title", ""),
        summary=analysis.get("summary", ""),
        side=side or analysis.get("your_side_hint", ""),
        parties=parties or ", ".join(analysis.get("parties", [])),
        region=region,
        analogs=", ".join(analysis.get("real_world_analogs", [])) or "none known",
        n=n,
    )
    llm_qs: list[str] = []
    try:
        raw = llm.generate(prompt, temperature=0.4, max_output_tokens=4096)
        llm_qs = [q for q in extract_json(raw).get("queries", []) if str(q).strip()]
    except Exception:  # noqa: BLE001
        pass
    base = []
    for kw in (analysis.get("keywords") or [])[:4]:
        base.append(str(kw))
    title = analysis.get("title", "")
    if title:
        base += [f"{title} treaty agreement", f"{title} latest data 2025"]
    seen, out = set(), []
    for q in llm_qs + base:
        k = str(q).strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(str(q).strip())
    return out[: max(n, 5)]


# --------------------------------------------------------------------------
# Stage C — the playbook sections
# --------------------------------------------------------------------------

PLAYBOOK_SECTIONS: list[dict] = [
    {
        "key": "exec_landscape",
        "number": "1",
        "title": "The Situation — Read First",
        "word_min": 420, "word_max": 640,
        "guidance": """Two parts (no sub-headings):
First, an EXECUTIVE BRIEF (4-6 sentences): what this negotiation is about, who sits at the table, what your side needs, and the single most important objective. A reader must grasp the whole game from this.
Then THE LANDSCAPE: the hard facts the room will argue over — key statistics with citations, what is driving urgency now, relevant history (past agreements and why they failed or held), and 1-2 real-world analog outcomes with citations. Facts win arguments; make this section quotable.""",
    },
    {
        "key": "stakeholders",
        "number": "2",
        "title": "Stakeholder Map",
        "word_min": 250, "word_max": 420,
        "guidance": """Map every party at the table. Present a markdown table with EXACTLY these columns:
| Party | Core interests | Red lines | Leverage / pressure points | Probable opening stance |
Then add one short paragraph per party (or cluster) reading their deeper motivations — what they cannot say aloud but are actually optimizing for, and which of their interests secretly aligns with yours. End with 2-3 sentences on where the Zone of Possible Agreement (ZOPA) most plausibly lies.""",
    },
    {
        "key": "position",
        "number": "3",
        "title": "Your Position: Objectives, BATNA & Walk-aways",
        "word_min": 350, "word_max": 550,
        "guidance": """Written for the negotiator's OWN side. Use three sub-headings:
### Ranked Objectives
A numbered list of 5-7 objectives split into three tiers: MUST-WIN (walk away without these), DESIRABLE (push hard, trade late if needed), TRADABLE (currency for concessions). Phrase each concretely (numbers, dates, mechanisms).
### Your BATNA
Your best alternative to a negotiated agreement — what your side realistically does if this round fails, and how strong that fallback is. One short paragraph; then ONE sentence on the opponent's likely BATNA and its weakness.
### Red Lines & Reservation Points
Bullet list: the lines you never cross, and for each, the fallback formulation (a softer clause you could live with). Note which red lines you should keep private vs declare early.""",
    },
    {
        "key": "strategy",
        "number": "4",
        "title": "Negotiation Strategy & Concession Ladder",
        "word_min": 500, "word_max": 800,
        "guidance": """The operational core. Use four sub-headings:
### Opening Stance
What to open with (position + rationale + tone), and the first 2 minutes essentially scripted: your framing of the problem so the room adopts your vocabulary.
### The Concession Ladder
A numbered ladder of 5-8 moves, each step formatted as: 'Give X -> demand Y in return -> deploy when [early/mid/late]'. Rules baked into the list: descend slowly, never concede unilaterally, always pair a give with a get, save one 'surprise' concession for the endgame.
### Package Deals
2-3 bundled offers that trade across issue areas (log-rolling), each with the rationale for why every party can claim a win from the bundle.
### Time & Process Management
How to pace the negotiation within the time limit, when to call a caucus/side-meeting, how to force drafting (offer to write the communiqué — drafters control the deal), and how to close.""",
    },
    {
        "key": "coalitions_arguments",
        "number": "5",
        "title": "Coalitions, Arguments & Rebuttals",
        "word_min": 550, "word_max": 850,
        "guidance": """Two sub-headings:
### Coalition Plan
Who to ally with, who is persuadable, who to politely isolate — with the specific offer that buys each ally. A short markdown table (Party | Relationship goal | What you offer them | What you ask) plus one paragraph on sequencing the wooing.
### Argument Bank
8-12 arguments formatted as a markdown table with EXACTLY these columns:
| # | Argument (one line) | Evidence (cite digest) | Best deployed against | Likely counter | Your rebuttal |
Every evidence cell must carry a citation key from the digest. After the table, expand your THREE strongest arguments into short paragraphs (the knockout hits you lead with), including exact numbers and their sources.""",
    },
    {
        "key": "contingencies_closing",
        "number": "6",
        "title": "Contingencies, Draft Agreement & Closing Kit",
        "word_min": 550, "word_max": 850,
        "guidance": """Three sub-headings:
### Crisis Contingencies
A markdown table (Trigger | Your move | Why it works) covering 5-6 crises: opponent walkout, surprise demand, public grandstanding, an inject/new fact revealed mid-round, time running out with no deal, and an ally defecting.
### Draft Agreement Framework
A numbered skeleton of the communiqué/treaty text you will push into drafting (Preamble framing; 4-6 operative clauses naming parties + mechanisms + timelines; implementation & review body; dispute-resolution clause; entry-into-force). Written so it can be read aloud verbatim at the table. Ground mechanisms in real treaty practice (cite analogs from the digest).
### Diplomatic Phrasebook
10-14 ready-to-say lines grouped under bold labels: **Openers**, **Framing a concession**, **Defusing tension**, **Firm pushback without hostility**, **Buying time**, **Closing the deal**. Adapt each line to THIS scenario (mention the issue and parties), keep each line 1-2 sentences — things a delegate actually says.""",
    },
    {
        "key": "quick_reference",
        "number": "7",
        "title": "One-Page Quick Reference Card",
        "word_min": 220, "word_max": 320,
        "guidance": """Everything the negotiator glances at in the last 30 seconds. Tight bullets only, no prose paragraphs:
- **Your 5 priorities** (in order)
- **5 killer numbers to quote** — each with year and source from the digest
- **Your 3 red lines**
- **Opening line** (one sentence, verbatim)
- **Closing line** (one sentence, verbatim)
- **If you forget everything else**: the single rule for this room.""",
    },
]

SECTION_ORDER_NOTE = (
    "The judges value consensus-building, realistic and implementable agreements, "
    "creative problem-solving, adaptability and professional diplomatic conduct. "
    "Weight your advice accordingly."
)


def _brief_block(meta: NegoMeta, analysis: dict) -> str:
    parties = ", ".join(analysis.get("parties", []) or [])
    return f"""\
SCENARIO BRIEF (raw):
\"\"\"
{meta.brief_text[:5000]}
\"\"\"

DERIVED ANALYSIS:
- Title: {analysis.get('title')}
- Summary: {analysis.get('summary')}
- Issue areas: {', '.join(analysis.get('issue_areas', []) or [])}
- Parties: {meta.other_parties or parties}
- Your side: {meta.your_stakeholder or analysis.get('your_side_hint', 'the assigned stakeholder')}
- Stakes: {analysis.get('stakes')}
- Real-world analogs: {', '.join(analysis.get('real_world_analogs', []) or []) or 'none identified'}
- Region: {meta.region}
- Round: {meta.round_name or 'not specified'} | Time limit: {meta.time_limit or 'not specified'}
"""


def write_playbook_section(
    spec: dict,
    meta: NegoMeta,
    analysis: dict,
    digest: str,
    prior: list[str],
    llm,
    word_multiplier: float = 1.0,
) -> str:
    wmin = int(spec["word_min"] * word_multiplier)
    wmax = int(spec["word_max"] * word_multiplier)
    prior_txt = ""
    if prior:
        joined = "\n\n".join(p[:1200] for p in prior)
        prior_txt = f"\n\nEARLIER SECTIONS (excerpts — build on them, cross-reference, never repeat):\n{joined}"
    prompt = f"""{STYLE_GUIDE}

{NEG_VOICE}

{SECTION_ORDER_NOTE}

You are writing SECTION {spec['number']} — "{spec['title']}" — of the playbook. Write only this section.

{_brief_block(meta, analysis)}

EVIDENCE DIGEST (cite ONLY these, using their citation keys):
{digest}
{prior_txt}

SECTION REQUIREMENTS (follow exactly):
{spec['guidance']}

FORMAT
- Begin with exactly this line and nothing before it: ## {spec['number']}. {spec['title']}
- Then the content: {wmin}-{wmax} words.
Write the section now."""
    raw = llm.generate(prompt, temperature=0.6, max_output_tokens=16384)
    body = raw.strip()
    if body.lstrip().startswith("#"):
        body = "\n".join(body.splitlines()[1:]).strip()
    return f"## {spec['number']}. {spec['title']}\n\n{body}"


# --------------------------------------------------------------------------
# Practice scenario generator
# --------------------------------------------------------------------------

DIFFICULTY_PROFILES = {
    "Preliminary (bilateral, one issue)": "Bilateral or regional dispute, ONE core issue (e.g. water-sharing revision), 2 stakeholders, clear objectives, moderate data, no hidden crises.",
    "Quarterfinal (multi-dimensional)": "One dispute touching 2-3 dimensions (e.g. economics + environment + public health), 3-4 parties at the table, some asymmetric information.",
    "Semifinal (complex transnational)": "Multi-country transnational challenge, 3 interlocking issue areas, each side carries a hidden private constraint that pressures them (stated only in their confidential brief), one mid-round crisis inject the briefs hint at.",
    "Grand Final (integrated global crisis)": "Integrated crisis spanning political, economic, humanitarian, environmental AND security domains simultaneously, 4+ stakeholders, high uncertainty, secrets per side, and a structured crisis-development sequence.",
}

CATEGORIES = [
    "Cross-border resource management (water / fisheries / shared pollution / renewable energy / health cooperation)",
    "Transnational security & resource governance (critical minerals / AI governance / cybersecurity / infrastructure threats)",
    "Complex crisis management (humanitarian emergency / disaster response / maritime crisis / environmental incident)",
    "Multi-domain global summit (climate + inequality + migration + energy + finance + development)",
]

_DESIGN_PROMPT = """You design negotiation scenarios for a diplomatic competition.

Category: {category}
Difficulty profile: {difficulty}
Region flavour: {region}

Invent a realistic, self-contained scenario (fictional countries/actors are fine; keep it plausible and politically tasteful — no real ongoing wars).

Respond with ONLY minified JSON:
{{
 "title": "evocative scenario title, max 12 words",
 "setting": "where/when this takes place (1-2 sentences)",
 "background": "the situation in 3-4 sentences",
 "core_dispute": "the central conflict in 1-2 sentences",
 "team_a": {{"stakeholder": "who Team A represents", "public_position": "their public stance", "pressure": "their key vulnerability"}},
 "team_b": {{"stakeholder": "who Team B represents", "public_position": "their public stance", "pressure": "their key vulnerability"}},
 "extra_parties": ["0-3 other actors present or invoked"],
 "issue_dimensions": ["the 1-5 policy dimensions, matching the difficulty profile"],
 "crisis_inject": "a plausible mid-round twist revealed later (or empty if difficulty is Preliminary)",
 "agreement_space": "what a good deal plausibly looks like (2 sentences, judges' eyes only)"
}}"""


def design_practice_scenario(category: str, difficulty: str, region: str, llm) -> dict:
    prompt = _DESIGN_PROMPT.format(
        category=category, difficulty=DIFFICULTY_PROFILES[difficulty], region=region
    )
    data = llm.generate_json(prompt, max_output_tokens=8192)
    return data


def _stringify(value) -> str:
    if isinstance(value, (list, tuple)):
        return " | ".join(str(v) for v in value)
    return str(value)


def write_shared_brief(design: dict, difficulty: str, digest: str, llm) -> str:
    prompt = f"""{STYLE_GUIDE}

Write the SHARED MATCH BRIEF handed to BOTH teams at round start. This is the neutral, public document.

SCENARIO DESIGN:
{_stringify(design)[:2500]}
Difficulty: {difficulty}

GROUNDING (real-world facts you may weave in for authenticity, with citations in the form (Source, year)):
{digest[:6000] if digest else "(none — rely on fictional but plausible figures and mark them as scenario data)"}

STRUCTURE (use these markdown headings):
## Match Brief — [scenario title]
### 1. The Setting (where, when, who convenes the table)
### 2. Background (how we got here — 4-6 sentences, concrete numbers)
### 3. The Current Crisis/Dispute (what must be settled today)
### 4. The Parties at the Table
### 5. Format & Rules (time limit, that a joint communiqué is expected, that winners advance)

Keep it 450-650 words, immersive but factual in tone — like a real summit brief."""
    raw = llm.generate(prompt, temperature=0.65, max_output_tokens=8192)
    body = raw.strip()
    return body if body.startswith("##") else f"## Match Brief — {design.get('title', 'Practice Scenario')}\n\n{body}"


def write_team_brief(design: dict, team_key: str, difficulty: str, digest: str, llm) -> str:
    t = design.get(team_key, {}) or {}
    label = "Team A" if team_key == "team_a" else "Team B"
    title = f"Confidential Brief — {label}: {t.get('stakeholder', 'Stakeholder')}"
    prompt = f"""{STYLE_GUIDE}

Write a CONFIDENTIAL brief handed ONLY to {label}: {t.get('stakeholder')}.

SCENARIO: {design.get('title')} — {_stringify(design.get('background', ''))}
Core dispute: {_stringify(design.get('core_dispute', ''))}
This side's public position: {_stringify(t.get('public_position', ''))}
This side's private pressure/vulnerability: {_stringify(t.get('pressure', ''))}
Difficulty: {difficulty}
Crisis inject (if any): {_stringify(design.get('crisis_inject', 'none'))}
Real-world grounding (cite as (Source, year) where used):
{digest[:4000] if digest else '(none)'}

Produce a confidential brief, 350-550 words, with markdown headings:
### Your Mandate (2-3 sentences of flavour)
### Your Objectives (4-6, ranked — mix of public demands and private needs)
### Intelligence on the Other Side (what you suspect about them — 3-4 bullets)
### Your Pressure Points (why you must reach a deal; what failure costs you)
### Hidden Constraints (1-2 secrets you must not reveal early)
### Winning Looks Like (a one-line definition of a victory you can sell at home)

Write with tension and texture — this should feel like being handed the real file."""
    raw = llm.generate(prompt, temperature=0.65, max_output_tokens=8192)
    note = raw.strip()
    return ("" if note.startswith("##") else f"## {title}\n\n") + note


def write_judge_note(design: dict, llm) -> str:
    prompt = f"""{STYLE_GUIDE}

Write the JUDGE'S NOTE for this practice match (seen only after the match).

Scenario: {design.get('title')}
Core dispute: {_stringify(design.get('core_dispute', ''))}
Agreement space: {_stringify(design.get('agreement_space', ''))}

Produce markdown, 300-450 words:
### What a Strong Deal Looks Like (the plausible consensus zone, 3-5 clauses with rough content)
### Likely Traps (2-3 ways teams waste the round)
### Scoring Rubric (markdown table: Criterion | Weight | What excellent looks like — with criteria Consensus-building, Realism & implementability, Argumentation & evidence, Adaptability & crisis handling, Diplomatic conduct; weights summing to 100%)"""
    raw = llm.generate(prompt, temperature=0.5, max_output_tokens=8192)
    note = raw.strip()
    return ("" if note.startswith("##") else "## Judge's Solution Note\n\n") + note


JUDGING_NOTE = """\
WHAT JUDGES SCORE (in this order):
- CRITICAL THINKING is the main thing: clear logic, cause-and-effect, and
  solutions that could really work. Every claim should have a reason behind it.
- The GOAL is to REACH AN AGREEMENT.
- Real-world laws and rules are only SUPPORTING tools — mention one only when
  it genuinely strengthens a point; never pad the document with legal names.
- Scenarios are fiction-based crisis stories — think fast, stay practical,
  keep solutions workable in the real world."""


# --------------------------------------------------------------------------
# Compact playbook: paste a round brief -> 1-2 page negotiation-points card
# --------------------------------------------------------------------------

SIMPLE_LANGUAGE = """\
LANGUAGE RULES (most important — follow strictly):
- Write like you are explaining to a class 6 student (11-12 years old).
  Every line must be easy on the first read. No dictionary needed.
- Very short sentences: 5-10 words each. One idea per sentence.
- Use only small everyday words: water, money, border, deal, promise, trust,
  safe, angry, help, wait, share.
- Avoid long "big people" words like framework, leverage, concession,
  infrastructure, diplomatic, allocation, arbitration.
- If a hard word is truly needed, explain it right away in 3-5 simple words,
  e.g. "sanction (punishment by blocking trade)", "treaty (a written promise
  between countries)".
- Prefer simple numbers: "half the water", "10,000 people", "6 weeks" —
  not percentages alone or big technical figures.
- Table cells: 2-5 simple words only.
- The "why this works" lines must be dead simple cause-and-effect, e.g.
  "Both sides get water, so both stop fighting. So the deal holds."
- Test every sentence: if a class 6 kid would frown, rewrite it simpler.
Ignore any earlier instruction about a formal register for this document."""

_COMPACT_PLAYBOOK_PROMPT = """{style}

{simple}

{judging}

You are a veteran diplomat briefing a negotiator minutes before a simulation round. From the scenario brief below, write a tight 1-2 page negotiation document (450-700 words). The whole document is built around 4-5 concrete points of negotiation, and it ends with the 4-5 final agreement points to steer the room toward. The judges reward consensus-building and implementable deals, not stubbornness — weight your positions for a balanced agreement that your side can still call a win.

ADAPTIVE RULES (the input length varies — handle both):
- The scenario material may be TINY (2-3 lines) or LONG (1-2 pages).
- If the brief is SHORT: quietly expand it into a realistic full scenario before writing — invent plausible parties, numbers and pressures. Then on the first line of the document, note your key assumption in one bracketed line, e.g. *(Assumed: two neighbouring states, treaty expiring this year.)*
- If the brief is LONG: distill hard — skip the colour, keep only the dispute, the parties, the numbers and the deadline.
- If the brief does not name the parties, name plausible stakeholders yourself (fictional countries/actors are fine).
- If YOUR SIDE and OTHER PARTIES are given below, treat them as correct and build around them.

SCENARIO BRIEF:
\"\"\"
{brief}
\"\"\"

YOUR SIDE: {side}
OTHER PARTIES: {parties}
TIME LIMIT: {time_limit}
REGION: {region}
{spec_block}
Produce markdown with EXACTLY this structure (no extra sections):

## {title_line}
*1-2 page negotiation card · inferred from your round brief · suggested final {time_short} for drafting*

### The situation in 3 lines
Compress the brief to its essence: the dispute, why now, what happens if no deal.

### Both sides at a glance
- **You ({side}):** 1-2 lines — what you fundamentally need out of this room
- **Them ({parties}):** 1-2 lines — what they fundamentally need

### The negotiation, point by point
A markdown table with EXACTLY these columns and 4-5 rows (each row = one point of negotiation):
| # | Point to settle | You open at | They open at | Landing zone |

### Your red lines
3 bullets, one line each — what you never concede.

### The final agreement — the 4-5 points to push for
4-5 numbered points. Each point = a **bold lead-in** + 1-2 concrete sentences of what the deal text should say — who does what, by when, with what mechanism. Specific and signable. Balanced enough that the other side can sign it, favourable enough that you can defend it at home.
After each point's deal text, add one short line: "→ why this works:" followed by the simple logic (cause and effect). This line shows the critical thinking the judges score — it is the most important part.

### Say it at the table
- **Opening line:** one diplomatic sentence that frames the room
- **Closing line:** one sentence to lock the deal

### Concluding statement (learn by heart and say at the end — about 1 minute long)
A spoken statement of roughly 120-150 words (8-10 short lines) that takes about
1 minute to say out loud. Count the words and stay inside 120-150. In simple English:
1. thank the other side and the judges,
2. restate the 4-5 agreed points in 2-3 lines,
3. say — respectfully but clearly — that OUR side drove the result: we came with solutions, we protected our people's needs, and we still met the other side halfway,
4. end with one confident line about friendship, balance and lasting peace.

### Why our negotiation was the best
3 bullets, one line each of simple logic, to answer the judges if they ask "why should your side win?":
- what we protected: our red lines held in the final deal
- what we gave smartly: small cost to us, big trust gained
- why the deal works mostly because of points OUR side pushed first"""


def write_compact_playbook(meta: NegoMeta, llm) -> str:
    side = meta.your_stakeholder.strip() or "your assigned stakeholder"
    parties = meta.other_parties.strip() or "the other parties named in the brief"
    title_line = (meta.scenario_title.strip() or "Round Negotiation") + " — Negotiation Points"
    time_short = (meta.time_limit.strip() or "20-30 minutes")
    spec = (getattr(meta, "agreement_spec", "") or "").strip()
    spec_block = ""
    if spec:
        spec_block = (
            f'VENUE-ANNOUNCED AGREEMENT FORMAT: "{spec}"\n'
            "- Shape 'The final agreement' section to follow this EXACTLY "
            "(pages / word count / format style, e.g. numbered clauses, MOU, resolution).\n"
            "- If the announced format needs more room, keep every other section extra "
            "short so the agreement gets the space it needs.\n"
        )
    prompt = _COMPACT_PLAYBOOK_PROMPT.format(
        style=STYLE_GUIDE,
        simple=SIMPLE_LANGUAGE,
        judging=JUDGING_NOTE,
        brief=meta.brief_text[:10000],
        side=side,
        parties=parties,
        time_limit=time_short,
        region=meta.region or "not specified",
        title_line=title_line,
        time_short=time_short,
        spec_block=spec_block,
    )
    raw = llm.generate(prompt, temperature=0.55, max_output_tokens=2048)
    body = raw.strip()
    if not body.startswith("##"):
        body = f"## {title_line}\n\n{body}"
    return body


# --------------------------------------------------------------------------
# Compact practice flow: 2-3 short topic ideas -> pick one -> 1-2 page doc
# --------------------------------------------------------------------------

_IDEAS_PROMPT = """You design practice negotiation topics for a diplomatic competition (2-person teams, each side represents a stakeholder).

Category: {category}
Difficulty profile: {difficulty}
Region flavour: {region}

Suggest 3 distinct, plausible practice scenario ideas (fictional countries are welcome; avoid real ongoing wars). Keep every idea SHORT.

Respond with ONLY minified JSON:
{{"ideas":[
 {{"title":"max 10 words","blurb":"2-3 lines describing the situation and what must be negotiated","side_a":"who Team A represents","side_b":"who Team B represents"}},
 {{"title":"...","blurb":"...","side_a":"...","side_b":"..."}},
 {{"title":"...","blurb":"...","side_a":"...","side_b":"..."}}
]}}"""


def suggest_practice_topics(category: str, difficulty: str, region: str, llm) -> list[dict]:
    """Return 3 short scenario ideas [{title, blurb, side_a, side_b}]."""
    prompt = _IDEAS_PROMPT.format(
        category=category,
        difficulty=DIFFICULTY_PROFILES.get(difficulty, difficulty),
        region=region,
    )
    try:
        data = llm.generate_json(prompt, max_output_tokens=1536)
        ideas = [
            {k: str(v).strip() for k, v in idea.items()}
            for idea in data.get("ideas", [])
            if isinstance(idea, dict) and idea.get("title")
        ]
        if ideas:
            return ideas[:3]
        raise ValueError("no ideas parsed")
    except Exception:  # noqa: BLE001
        short_cat = category.split("(")[0].strip().lower()
        return [
            {"title": f"Practice scenario 1", "blurb": f"A {short_cat} negotiation between two neighbouring states.", "side_a": "State A", "side_b": "State B"},
            {"title": "Practice scenario 2", "blurb": f"A multilateral {short_cat} crisis requiring a joint communiqué.", "side_a": "Bloc A", "side_b": "Bloc B"},
            {"title": "Practice scenario 3", "blurb": f"A regional summit on {short_cat} with competing domestic pressures.", "side_a": "Delegation A", "side_b": "Delegation B"},
        ]


_COMPACT_DOC_PROMPT = """{style}

{simple}

{judging}

Write a COMPACT practice negotiation document — strictly 1-2 pages (450-750 words total). The whole document is built around 4-5 concrete negotiation points, and it ends by SHOWING the settled deal: 4-5 final agreed points.

SCENARIO IDEA:
- Title: {title}
- Situation: {blurb}
- Team A represents: {side_a}
- Team B represents: {side_b}
- Difficulty: {difficulty}
- Region flavour: {region}

Produce markdown with EXACTLY this structure (no extra sections):

## {title}
*Fictional practice negotiation · {category_short} · Suggested time: 20-30 minutes*

### The situation in brief
3-4 short lines: where, what tension, why it must be settled now. Use concrete (plausible, fictional) numbers.

### Team A — {side_a}
- **Wants:** 2-3 bullets tied to the negotiation points below
- **Red line:** one line
- **Hidden pressure:** one line (why they secretly need a deal)

### Team B — {side_b}
- **Wants:** 2-3 bullets, conflicting where natural
- **Red line:** one line
- **Hidden pressure:** one line

### The negotiation, point by point
A markdown table with EXACTLY these columns and 4-5 rows (each row = one negotiation point):
| # | Point to settle | Team A opens at | Team B opens at | Likely landing zone |

### The final agreement — the 4-5 points that get signed
4-5 numbered points. Each point = a **bold lead-in** + 1-2 concrete sentences stating what the two sides actually agree on — who does what, by when, with what mechanism, and the numbers involved. Specific and signable, not vague aspirations. Together they must balance wins for BOTH sides. End each point with: "→ why this works:" and one short simple line of logic (cause and effect) — this shows the critical thinking judges score first.

### Concluding statement (for both teams — about 1 minute long)
- A spoken statement of roughly 120-150 words (takes about 1 minute to say) that EITHER team can adapt and speak at the end: thank the other side and the judges; restate the deal in 2-3 lines; say why OUR side stayed the most constructive and pushed the best solutions; close with one confident line about the future.
- Then two short lines:
  - **Team A's strongest "we were better" argument:** one line of simple logic
  - **Team B's strongest "we were better" argument:** one line of simple logic

### Facilitator's note
1-2 lines: why this deal balances both sides, and one trap negotiators fall into on this topic."""


def write_compact_practice_doc(idea: dict, category: str, difficulty: str, region: str, llm) -> str:
    prompt = _COMPACT_DOC_PROMPT.format(
        style=STYLE_GUIDE,
        simple=SIMPLE_LANGUAGE,
        judging=JUDGING_NOTE,
        title=idea.get("title", "Practice Negotiation"),
        blurb=idea.get("blurb", ""),
        side_a=idea.get("side_a", "Team A"),
        side_b=idea.get("side_b", "Team B"),
        difficulty=difficulty.split("(")[0].strip(),
        region=region,
        category_short=category.split("(")[0].strip(),
    )
    raw = llm.generate(prompt, temperature=0.6, max_output_tokens=2048)
    body = raw.strip()
    if not body.startswith("##"):
        body = f"## {idea.get('title', 'Practice Negotiation')}\n\n{body}"
    return body


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def assemble_playbook_markdown(meta: NegoMeta, sections_md: list[str], sources: list[Source]) -> tuple[str, int]:
    body_words = sum(word_count(s) for s in sections_md)
    meta.word_count = body_words
    kw = ", ".join(meta.keywords) if meta.keywords else meta.title_or_default()
    cover = f"""# {meta.title_or_default()} — Negotiation Playbook

**Scenario:** {meta.title_or_default()}
**Your Stakeholder:** {meta.your_stakeholder or '—'}
**Other Parties:** {meta.other_parties or '—'}
**Round:** {meta.round_name or '—'}
**Team:** {meta.team_members or '—'}
**Institution:** {meta.institution or '—'}
**Time Limit:** {meta.time_limit or '—'}
**Keywords:** {kw}

> Game plan: read Section 1 and Section 7 if time is short; the rest when you can.

---

"""
    parts = [cover, *sections_md]
    if sources:
        parts.append(build_references(sources).markdown)
    return "\n\n".join(p.strip() for p in parts) + "\n", body_words


def assemble_practice_markdown(shared: str, brief_a: str, brief_b: str, judge: str) -> str:
    separator_a = "\n\n---\n\n*🔒 CONFIDENTIAL — for Team A only. Do not show the opposing team.*\n\n"
    separator_b = "\n\n---\n\n*🔒 CONFIDENTIAL — for Team B only. Do not show the opposing team.*\n\n"
    separator_j = "\n\n---\n\n*⚖️ JUDGES ONLY — read after the match concludes.*\n\n"
    return f"{shared.strip()}{separator_a}{brief_a.strip()}{separator_b}{brief_b.strip()}{separator_j}{judge.strip()}\n"
