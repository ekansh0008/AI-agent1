"""The policy-paper template: sections, order, and drafting guidance.

Guidance text is intentionally detailed so the model follows the exact
recommended structure supplied for the competition.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Section definitions. `guidance` is injected verbatim into the writer prompt.
# word_min/word_max are for "Standard" depth; other depths scale them.
# ---------------------------------------------------------------------------

BODY_SECTIONS: list[dict] = [
    {
        "key": "problem_analysis",
        "number": "2",
        "title": "Problem Analysis",
        "word_min": 750,
        "word_max": 1000,
        "guidance": """Define the policy problem precisely and establish its significance through evidence and context. Use three sub-headings:
### Current Situation
Cover: relevant background; current statistics and trends (cite the digest); the existing policy environment; and the scope and significance of the problem. Identify the underlying GOVERNANCE challenge, not merely the visible symptoms.
### Stakeholder Analysis
Identify the major stakeholders: government institutions, citizens and communities, private sector actors, civil society organisations, international organisations, and vulnerable populations. Show their responsibilities, competing interests, and opportunities for collaboration. Prose preferred; a short table is acceptable if it sharpens the analysis.
### Root Cause Analysis
Investigate the underlying causes, using at least ONE named analytical framework (Systems Thinking, PESTLE Analysis, Fishbone Analysis, or Governance Mapping) as an organising device. Distinguish proximate causes from structural ones.""",
    },
    {
        "key": "policy_context",
        "number": "3",
        "title": "Policy Context & Evidence",
        "word_min": 700,
        "word_max": 900,
        "guidance": """Demonstrate command of the broader policy environment. Weave in, with in-text citations from the digest: existing laws and regulations; government programmes and initiatives; international agreements and conventions; relevant United Nations frameworks; at least two comparative international examples (what worked, what did not, and why); and a frank account of policy gaps and implementation challenges. Support every major argument with credible evidence (government publications, UN reports, World Bank, OECD, academic journals). Close by stating clearly what the evidence implies a new policy must do that existing ones do not.""",
    },
    {
        "key": "policy_proposal",
        "number": "4",
        "title": "Policy Proposal",
        "word_min": 850,
        "word_max": 1100,
        "guidance": """This is the core of the paper. Use three sub-headings:
### Policy Objectives
State 4-6 objectives in SMART form (Specific, Measurable, Achievable, Relevant, Time-bound) — phrase each with a number, a baseline, and a deadline where possible.
### Proposed Solution
Explain in concrete operational detail how the proposal works and how it attacks the root causes identified in Section 2. Draw as relevant from: institutional reforms; legal reforms; administrative mechanisms; digital governance tools; citizen participation mechanisms; capacity-building initiatives; financial models and funding structures. Name the responsible institutions, the implementation mechanisms, and the resource requirements.
### Innovation
Explain what makes the proposal distinctive, how it improves on existing approaches, and whether/how it could be replicated or adapted in other contexts.""",
    },
    {
        "key": "implementation",
        "number": "5",
        "title": "Implementation Strategy",
        "word_min": 650,
        "word_max": 900,
        "guidance": """Present a realistic, phased implementation plan with these phases: Preparation; Pilot Implementation; Scale-Up; Monitoring; Independent Evaluation. For each phase give the timeframe, key actions and the lead institution. Then address estimated budget requirements, funding sources (be specific: budget heads, centrally sponsored schemes, multilateral finance, CSR, municipal bonds, etc.), resource requirements, and financial sustainability. Include ONE markdown table titled 'Indicative Budget Summary' with columns: Component | Year 1 | Year 2 | Year 3 | Total (state the currency) and rows for the major cost heads. The strategy must demonstrate operational feasibility, not theoretical ambition.""",
    },
    {
        "key": "impact_risk_ethics",
        "number": "6",
        "title": "Impact, Risk & Ethics",
        "word_min": 750,
        "word_max": 1000,
        "guidance": """Use four sub-headings:
### Impact Assessment
Evaluate expected impact across: economic outcomes; social benefits; environmental implications; governance improvements; gender and inclusion considerations; technological accessibility; human rights implications. Give realistic magnitudes with reasoning, not vague optimism.
### Risk Assessment
Identify the major implementation risks among: political, financial, administrative, legal, technological, environmental. Use a markdown table: Risk | Likelihood | Impact | Mitigation Measure — 5-7 rows — followed by one short paragraph on the single greatest risk.
### Ethical Considerations
Examine privacy concerns, equity and accessibility, inclusion and representation, human rights considerations, and environmental justice implications, and state the safeguards the proposal builds in.
### Sustainable Development Goal (SDG) Alignment
Identify the SDGs the proposal supports (use the mapped goals provided) and explain concretely how each recommendation advances those goals and their targets, and contributes to the wider 2030 Agenda.""",
    },
    {
        "key": "monitoring",
        "number": "7",
        "title": "Monitoring & Evaluation Framework",
        "word_min": 300,
        "word_max": 450,
        "guidance": """First write 2-3 short paragraphs: the evaluation logic (results chain), who collects data and how often, and how findings feed back into policy (including independent evaluation). Then provide ONE markdown table with EXACTLY these columns:
| Indicator | Baseline | Target | Data Source | Timeline | Responsible Agency |
Provide 8-12 rows covering inputs, outputs, outcomes and at least one equity/gender-disaggregated indicator. Baselines should cite a source where the digest provides one (write e.g. '32% (NFHS-5, 2021)'); otherwise give a reasoned estimate marked '(est.)'.""",
    },
    {
        "key": "conclusion",
        "number": "8",
        "title": "Conclusion",
        "word_min": 320,
        "word_max": 450,
        "guidance": """Synthesise the central argument. Restate briefly: the problem being addressed; the proposed solution; the expected long-term outcomes; and a future vision resulting from successful implementation. End with a crisp, confident call to action for the committee. No new evidence or statistics here.""",
    },
]

EXEC_SUMMARY_SPEC = {
    "key": "executive_summary",
    "number": "1",
    "title": "Executive Summary",
    "word_min": 250,
    "word_max": 350,
}

ANNEXURES_SPEC = {
    "key": "annexures",
    "number": "",
    "title": "Annexures",
    "guidance": """Produce exactly three annexures, each with a '### Annexure A/B/C' heading:
### Annexure A: Implementation Timeline
A markdown table (Phase | Months | Key Milestones | Lead Agency) consistent with Section 5.
### Annexure B: Detailed Budget
A markdown table expanding the Section 5 budget into line items (Item | Cost | Unit basis | Notes), with the same totals as Section 5.
### Annexure C: Policy-to-SDG Target Map
A markdown table (SDG Target | Official description | How the proposal advances it) for 4-6 targets, using the mapped SDGs.""",
}


def scaled_words(spec: dict, multiplier: float) -> tuple[int, int]:
    wmin = int(spec["word_min"] * multiplier)
    wmax = int(spec["word_max"] * multiplier)
    return wmin, max(wmin + 60, wmax)
