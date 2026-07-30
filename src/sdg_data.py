"""United Nations Sustainable Development Goal (SDG) reference data.

Used by the classifier for the LLM prompt and for the keyword-based
fallback when the LLM is unavailable.
"""

from __future__ import annotations

SDGS: dict[int, dict] = {
    1: {
        "name": "No Poverty",
        "description": "End poverty in all its forms everywhere.",
        "keywords": [
            "poverty", "extreme poverty", "social protection", "welfare",
            "below poverty line", "cash transfer", "livelihood", "income support",
            "poverty alleviation", "social safety net", "universal basic income",
            "deprivation", "financial inclusion",
        ],
    },
    2: {
        "name": "Zero Hunger",
        "description": "End hunger, achieve food security and improved nutrition and promote sustainable agriculture.",
        "keywords": [
            "hunger", "malnutrition", "stunting", "food security", "agriculture",
            "food system", "famine", "nutrition", "crop yield", "food waste",
            "farmers", "agricultural productivity", "wasting", "anaemia",
        ],
    },
    3: {
        "name": "Good Health and Well-Being",
        "description": "Ensure healthy lives and promote well-being for all at all ages.",
        "keywords": [
            "health", "healthcare", "hospital", "vaccination", "disease",
            "mortality", "mental health", "pandemic", "universal health coverage",
            "medicine", "primary health", "maternal health", "child health",
            "epidemic", "antimicrobial resistance", "wellbeing",
        ],
    },
    4: {
        "name": "Quality Education",
        "description": "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all.",
        "keywords": [
            "education", "school", "literacy", "teacher", "learning",
            "digital education", "vocational training", "skills", "dropout",
            "university", "higher education", "early childhood education",
            "curriculum", "enrolment", "scholarship",
        ],
    },
    5: {
        "name": "Gender Equality",
        "description": "Achieve gender equality and empower all women and girls.",
        "keywords": [
            "gender", "women", "girls", "sex discrimination", "women empowerment",
            "violence against women", "equal pay", "female labour force",
            "patriarchy", "women's rights", "gender gap", "gender-based violence",
            "girl child", "women in leadership",
        ],
    },
    6: {
        "name": "Clean Water and Sanitation",
        "description": "Ensure availability and sustainable management of water and sanitation for all.",
        "keywords": [
            "water", "sanitation", "drinking water", "hygiene", "wastewater",
            "groundwater", "water scarcity", "toilet", "water quality",
            "desalination", "water management", "safe drinking water",
            "open defecation", "irrigation efficiency",
        ],
    },
    7: {
        "name": "Affordable and Clean Energy",
        "description": "Ensure access to affordable, reliable, sustainable and modern energy for all.",
        "keywords": [
            "energy", "electricity", "renewable energy", "solar", "wind energy",
            "power grid", "energy access", "clean cooking", "energy efficiency",
            "fossil fuel subsidy", "electrification", "green hydrogen",
            "energy poverty", "battery storage",
        ],
    },
    8: {
        "name": "Decent Work and Economic Growth",
        "description": "Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all.",
        "keywords": [
            "employment", "job", "economic growth", "labour", "unemployment",
            "youth employment", "msme", "entrepreneurship", "informal economy",
            "labour rights", "productivity", "decent work", "wage",
            "gig economy", "child labour",
        ],
    },
    9: {
        "name": "Industry, Innovation and Infrastructure",
        "description": "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation.",
        "keywords": [
            "industry", "innovation", "infrastructure", "manufacturing",
            "research and development", "technology adoption", "industrialisation",
            "broadband", "startup", "industrial policy", "logistics",
            "digital infrastructure", "small-scale industry",
        ],
    },
    10: {
        "name": "Reduced Inequalities",
        "description": "Reduce inequality within and among countries.",
        "keywords": [
            "inequality", "inequalities", "migration", "refugee", "migrant",
            "income inequality", "social inclusion", "discrimination",
            "disability inclusion", "equitable", "marginalised", "caste",
            "wealth gap", "remittance",
        ],
    },
    11: {
        "name": "Sustainable Cities and Communities",
        "description": "Make cities and human settlements inclusive, safe, resilient and sustainable.",
        "keywords": [
            "city", "cities", "urban", "housing", "slum", "public transport",
            "urban planning", "smart city", "municipal", "waste management",
            "urbanisation", "air pollution", "urban resilience",
            "affordable housing", "cultural heritage",
        ],
    },
    12: {
        "name": "Responsible Consumption and Production",
        "description": "Ensure sustainable consumption and production patterns.",
        "keywords": [
            "consumption", "production pattern", "recycling", "circular economy",
            "plastic waste", "e-waste", "sustainable consumption",
            "resource efficiency", "supply chain", "food loss", "packaging",
            "single-use plastic", "extended producer responsibility",
        ],
    },
    13: {
        "name": "Climate Action",
        "description": "Take urgent action to combat climate change and its impacts.",
        "keywords": [
            "climate change", "emission", "carbon", "global warming",
            "climate adaptation", "mitigation", "net zero", "climate finance",
            "greenhouse gas", "cop29", "climate resilience", "disaster risk",
            "extreme weather", "heatwave", "carbon market",
        ],
    },
    14: {
        "name": "Life Below Water",
        "description": "Conserve and sustainably use the oceans, seas and marine resources for sustainable development.",
        "keywords": [
            "ocean", "marine", "fisheries", "coral", "marine pollution",
            "coastal", "blue economy", "overfishing", "ocean plastic",
            "aquaculture", "marine protected area", "sea level",
        ],
    },
    15: {
        "name": "Life on Land",
        "description": "Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt biodiversity loss.",
        "keywords": [
            "forest", "biodiversity", "deforestation", "desertification",
            "land degradation", "wildlife", "ecosystem", "conservation",
            "poaching", "afforestation", "endangered species", "wetland",
            "soil health", "reforestation",
        ],
    },
    16: {
        "name": "Peace, Justice and Strong Institutions",
        "description": "Promote peaceful and inclusive societies, provide access to justice for all and build effective, accountable and inclusive institutions at all levels.",
        "keywords": [
            "governance", "corruption", "rule of law", "justice", "institution",
            "transparency", "accountability", "conflict", "human rights",
            "democracy", "public service delivery", "digital governance",
            "access to justice", "peace", "bribery", "civic space",
        ],
    },
    17: {
        "name": "Partnerships for the Goals",
        "description": "Strengthen the means of implementation and revitalize the global partnership for sustainable development.",
        "keywords": [
            "partnership", "international cooperation", "capacity building",
            "technology transfer", "sdg financing", "development aid",
            "multi-stakeholder", "global cooperation", "data for development",
            "south-south cooperation", "official development assistance",
            "trade facilitation", "policy coherence",
        ],
    },
}


def sdg_label(number: int) -> str:
    """'Goal 4: Quality Education' style label."""
    return f"Goal {number}: {SDGS[number]['name']}"


def sdg_catalogue_text() -> str:
    """Compact list of all goals, for the classifier prompt."""
    lines = []
    for n in range(1, 18):
        lines.append(f"{n}. {SDGS[n]['name']} — {SDGS[n]['description']}")
    return "\n".join(lines)
