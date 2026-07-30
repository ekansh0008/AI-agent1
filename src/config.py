"""Configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv optional
    pass

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Depth presets: (n_queries, results_per_query, max_sources, fetch_workers, word_multiplier)
DEPTH_PRESETS: dict[str, dict] = {
    "Quick draft (~3,000 words)": {
        "n_queries": 8,
        "results_per_query": 3,
        "max_sources": 12,
        "word_multiplier": 0.75,
    },
    "Standard (~4,500 words)": {
        "n_queries": 12,
        "results_per_query": 4,
        "max_sources": 18,
        "word_multiplier": 1.0,
    },
    "Deep research (~6,000 words)": {
        "n_queries": 16,
        "results_per_query": 5,
        "max_sources": 24,
        "word_multiplier": 1.25,
    },
}

MIN_REFERENCES = 15


@dataclass
class PaperMeta:
    """User-supplied + agent-derived cover-page metadata."""

    topic: str
    title: str = ""
    policy_area: str = ""
    country_region: str = "India"
    committee_event: str = ""
    participant_name: str = ""
    institution: str = ""
    keywords: list[str] = field(default_factory=list)
    word_count: int = 0

    def title_or_default(self) -> str:
        return self.title.strip() or self.topic.strip().rstrip(".")


def env_api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key or None
