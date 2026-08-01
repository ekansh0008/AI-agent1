"""Stage 2 - deep web research.

Generates targeted search queries with the LLM, runs them through
DuckDuckGo (no API key needed), fetches and extracts the most promising
pages, and returns a ranked, deduplicated source list covering
statistics, government policy, UN/World Bank/OECD material, case studies
and academic work.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests

from .llm import extract_json

MAX_TEXT_CHARS = 7000
REQUEST_TIMEOUT = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Authoritative sources get a ranking boost (policy papers need credible evidence).
AUTHORITATIVE_DOMAINS = {
    "un.org": "United Nations",
    "sdgs.un.org": "United Nations",
    "unstats.un.org": "UN Statistics Division",
    "unicef.org": "UNICEF",
    "undp.org": "UNDP",
    "unesco.org": "UNESCO",
    "unep.org": "UN Environment Programme",
    "unwomen.org": "UN Women",
    "unhabitat.org": "UN-Habitat",
    "unhcr.org": "UNHCR",
    "ilo.org": "International Labour Organization",
    "fao.org": "FAO",
    "who.int": "World Health Organization",
    "worldbank.org": "World Bank",
    "data.worldbank.org": "World Bank",
    "openknowledge.worldbank.org": "World Bank",
    "imf.org": "International Monetary Fund",
    "oecd.org": "OECD",
    "adb.org": "Asian Development Bank",
    "aiib.org": "Asian Infrastructure Investment Bank",
    "afdb.org": "African Development Bank",
    "weforum.org": "World Economic Forum",
    "reliefweb.int": "ReliefWeb (UN OCHA)",
    "ourworldindata.org": "Our World in Data",
    "wri.org": "World Resources Institute",
    "iea.org": "International Energy Agency",
    "irena.org": "IRENA",
    "niti.gov.in": "NITI Aayog",
    "mospi.gov.in": "Ministry of Statistics and Programme Implementation",
    "pib.gov.in": "Press Information Bureau, Government of India",
    "prsindia.org": "PRS Legislative Research",
    "egazette.gov.in": "The Gazette of India",
    "indiacode.nic.in": "India Code",
    "censusindia.gov.in": "Office of the Registrar General & Census Commissioner",
    "mohfw.gov.in": "Ministry of Health and Family Welfare",
    "education.gov.in": "Ministry of Education, Government of India",
    "moef.gov.in": "Ministry of Environment, Forest and Climate Change",
    "jal-shakti.gov.in": "Ministry of Jal Shakti",
    "sciencedirect.com": "ScienceDirect (Elsevier)",
    "springer.com": "Springer",
    "tandfonline.com": "Taylor & Francis",
    "nature.com": "Nature",
    "plos.org": "PLOS",
    "jstor.org": "JSTOR",
    "brookings.edu": "Brookings Institution",
    "orfonline.org": "Observer Research Foundation",
    "thehindu.com": "The Hindu",
    "indianexpress.com": "The Indian Express",
    "downtoearth.org.in": "Down To Earth",
    "economictimes.indiatimes.com": "The Economic Times",
}


def _base_domain(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?([^/]+)", url or "")
    return (m.group(1).lower() if m else "").lstrip("www.")


def publisher_for(domain: str) -> str:
    if domain in AUTHORITATIVE_DOMAINS:
        return AUTHORITATIVE_DOMAINS[domain]
    for known, name in AUTHORITATIVE_DOMAINS.items():
        if domain.endswith("." + known):
            return name
    stem = domain.split(".")[0]
    return stem.replace("-", " ").title() if stem else "Unknown"


@dataclass
class Source:
    title: str
    url: str
    domain: str
    publisher: str
    published: str = ""          # best-effort publication date/year
    snippet: str = ""
    text: str = ""               # extracted main content
    cite_key: str = ""           # e.g. "(World Bank, 2023a)"
    apa: str = ""                # ready-made APA 7 style reference line
    rank_score: float = 0.0

    @property
    def usable_text(self) -> str:
        return (self.text or self.snippet or "")[:MAX_TEXT_CHARS]


# Search engines to try, in order. DuckDuckGo goes first (the package's
# namesake), but it rate-limits aggressively, so we rotate through other
# metasearch backends on failure. All are free and keyless.
_SEARCH_BACKENDS = ["duckduckgo", "bing", "brave", "yahoo", "mojeek"]


def ddg_search(
    query: str, max_results: int = 5, retries: int | None = None
) -> tuple[list[dict], str | None]:
    """Search the web via the `ddgs` package.

    Rotates across free search backends (DuckDuckGo, Bing, Brave, Yahoo,
    Mojeek) when one fails or rate-limits. Returns (results, error_message).
    """
    try:
        from ddgs import DDGS as _DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS as _DDGS  # type: ignore
        except ImportError:
            raise RuntimeError(
                "Web search package missing. Run: pip install ddgs"
            )
    if retries is None:
        retries = len(_SEARCH_BACKENDS)
    last_err: Exception | None = None
    for attempt in range(retries):
        backend = _SEARCH_BACKENDS[attempt % len(_SEARCH_BACKENDS)]
        try:
            with _DDGS() as engine:
                try:
                    raw = engine.text(query, max_results=max_results, backend=backend)
                except TypeError:  # old SDK without `backend`
                    raw = engine.text(query, max_results=max_results)
            out = []
            for r in raw or []:
                url = r.get("href") or r.get("link") or ""
                title = r.get("title") or ""
                body = r.get("body") or ""
                if url and title:
                    out.append({"title": title.strip(), "url": url.strip(), "snippet": body.strip()})
            if out:
                return out, None
            last_err = RuntimeError(f"{backend}: no results")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(1.2 * (attempt + 1))
    err_text = str(last_err) if last_err else "unknown search error"
    return [], err_text


def fetch_page_text(url: str) -> tuple[str, str]:
    """Return (extracted_text, published_date). Empty strings on failure."""
    if re.search(r"\.pdf(\?|$)", url.lower()):
        return "", ""  # skip PDFs for speed; the snippet still informs the paper
    try:
        import trafilatura

        html = trafilatura.fetch_url(url)
        if html:
            meta_date = ""
            try:
                md = trafilatura.extract_metadata(html)
                if md and md.date:
                    meta_date = str(md.date)
            except Exception:  # noqa: BLE001
                pass
            text = trafilatura.extract(
                html, include_comments=False, include_tables=True,
                favor_recall=True,
            ) or ""
            if len(text) > 400:
                return text[:MAX_TEXT_CHARS], meta_date
    except Exception:  # noqa: BLE001
        pass
    # Fallback: requests + BeautifulSoup
    try:
        resp = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return text[:MAX_TEXT_CHARS], ""
    except Exception:  # noqa: BLE001
        return "", ""


_QUERY_PROMPT = """You are a research librarian preparing the evidence base for an academic policy paper.

Topic: "{topic}"
Country/Region focus: {country}
Mapped SDGs: {sdgs}
Research keywords: {keywords}

Generate {n} distinct, high-value web search queries that together will build a deep evidence base covering:
1. The latest statistics, trends and scale of the problem ({year_range})
2. Existing national laws, schemes and programmes in {country}
3. UN / World Bank / OECD / other international organisation reports and frameworks
4. Comparative international case studies (what other countries did, with results)
5. Academic research, evaluations and peer-reviewed evidence
6. Costs, budgets and financing data relevant to interventions

Make queries specific (include the country/region where useful), and phrase them the way a skilled researcher would type them into a search engine. Do not number them.

Respond with ONLY minified JSON: {{"queries":["...","..."]}}"""


def generate_queries(
    topic: str,
    country: str,
    sdg_labels: list[str],
    keywords: list[str],
    n: int,
    llm,
    year_range: str = "2022-2026",
) -> list[str]:
    prompt = _QUERY_PROMPT.format(
        topic=topic,
        country=country or "India",
        sdgs=", ".join(sdg_labels),
        keywords=", ".join(keywords) or topic,
        n=n,
        year_range=year_range,
    )
    queries: list[str] = []
    try:
        raw = llm.generate(prompt, temperature=0.4, max_output_tokens=4096)
        data = extract_json(raw)
        queries = [str(q).strip() for q in data.get("queries", []) if str(q).strip()]
    except Exception:  # noqa: BLE001
        queries = []

    # Deterministic safety-net queries (always included; research still works if the
    # LLM call above failed).
    c = (country or "India").strip()
    base = [
        f"{topic} statistics {c} 2024 2025",
        f"{topic} policy {c} government scheme",
        f"{topic} report site:un.org",
        f"{topic} site:worldbank.org {c}",
        f"{topic} case study evaluation impact",
        f"{topic} research journal evidence review",
    ]
    seen, out = set(), []
    for q in queries + base:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            out.append(q)
    return out[: max(n, 8)]


def _score(domain: str, url: str) -> float:
    score = 0.0
    if domain in AUTHORITATIVE_DOMAINS:
        score += 3.0
    elif re.search(r"\.gov(\.[a-z]{2})?$", domain) or ".gov." in domain:
        score += 2.5
    elif domain.endswith(".edu") or domain.endswith(".ac.in") or domain.endswith(".ac.uk"):
        score += 1.5
    elif domain.endswith(".org") or domain.endswith(".int"):
        score += 1.0
    if "report" in url.lower() or "policy" in url.lower() or "publication" in url.lower():
        score += 0.5
    if re.search(r"/20(2[2-6])\b", url):
        score += 0.4  # recent
    return score


def deep_research(
    topic: str,
    country: str,
    sdg_labels: list[str],
    keywords: list[str],
    llm,
    n_queries: int = 12,
    results_per_query: int = 4,
    max_sources: int = 18,
    progress=None,
) -> tuple[list[Source], list[str]]:
    """Full research pass. Returns (ranked sources, queries used)."""
    log = progress or (lambda msg: None)

    log("🧭 Generating research queries…")
    queries = generate_queries(topic, country, sdg_labels, keywords, n_queries, llm)
    log(f"🧭 {len(queries)} search queries planned")

    # --- search ---
    found: dict[str, dict] = {}
    failures = 0
    for i, q in enumerate(queries, 1):
        log(f"🔎 [{i}/{len(queries)}] {q}")
        hits, err = ddg_search(q, max_results=results_per_query)
        if err:
            failures += 1
            log(f"   ⚠️ search issue: {err[:140]}")
        for hit in hits:
            if hit["url"] not in found:
                found[hit["url"]] = hit
        time.sleep(0.7)  # be polite to the search engines

    if not found:
        log(
            "⛔ Web search returned nothing. Your internet connection may be "
            "restricted, or the free search backends are rate-limiting. Check the "
            "connection and retry after a few minutes."
        )
    elif failures:
        log(f"ℹ️ {failures}/{len(queries)} queries hit search issues; continuing with {len(found)} hits.")

    # --- rank & pick ---
    candidates = []
    for hit in found.values():
        domain = _base_domain(hit["url"])
        candidates.append((hit, domain, _score(domain, hit["url"])))
    candidates.sort(key=lambda t: t[2], reverse=True)

    def _has_enough_auth(pool) -> bool:
        auths = [c for c in pool if c[2] >= 3.0]
        return len(auths) >= 5

    pool = candidates[: max_sources * 2]
    if not _has_enough_auth(pool) and len(candidates) > len(pool):
        extra = [c for c in candidates[len(pool):] if c[2] >= 3.0]
        pool.extend(extra[: max_sources])

    # --- fetch & extract concurrently ---
    log(f"📚 Fetching & reading {min(len(pool), max_sources * 2)} candidate pages…")
    results: list[Source] = []
    top_pool = pool[: max_sources * 2]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(fetch_page_text, hit["url"]): (hit, domain, score)
            for (hit, domain, score) in top_pool
        }
        for fut in as_completed(futures):
            hit, domain, score = futures[fut]
            try:
                text, published = fut.result(timeout=REQUEST_TIMEOUT + 8)
            except Exception:  # noqa: BLE001
                text, published = "", ""
            src = Source(
                title=hit["title"],
                url=hit["url"],
                domain=domain,
                publisher=publisher_for(domain),
                published=published,
                snippet=hit.get("snippet", ""),
                text=text,
                rank_score=score + (1.0 if len(text) > 1200 else 0.0),
            )
            results.append(src)

    results.sort(key=lambda s: s.rank_score, reverse=True)
    sources = results[:max_sources]
    _assign_cite_keys(sources)
    for s in sources:
        s.apa = format_apa(s)
    log(f"✅ Research complete: {len(sources)} usable sources "
        f"({sum(1 for s in sources if s.rank_score >= 3)} from authoritative organisations)")
    return sources, queries


def _year_of(src: Source) -> str:
    for blob in (src.published, src.url, src.text[:600], src.snippet):
        m = re.search(r"\b(20[12]\d)\b", blob or "")
        if m:
            return m.group(1)
    return "n.d."


def _assign_cite_keys(sources: list[Source]) -> None:
    """Create unique APA in-text keys like (World Bank, 2023) / (UNDP, 2024a)."""
    seen: dict[str, int] = {}
    for s in sources:
        year = _year_of(s)
        base = f"{s.publisher}, {year}"
        idx = seen.get(base, 0)
        seen[base] = idx + 1
        key = base if idx == 0 else f"{base}{chr(ord('a') + idx - 1)}"
        s.cite_key = f"({key})"


def format_apa(src: Source) -> str:
    """Deterministic APA 7-ish reference line built from real page metadata."""
    year = _year_of(src)
    title = src.title.rstrip(".")
    site = src.publisher
    url = src.url
    if site.lower() in title.lower()[: len(site) + 4]:
        return f"{site}. ({year}). *{title}*. {url}"
    return f"{site}. ({year}). *{title}*. {site}. {url}"


def build_digest(sources: list[Source], per_source_chars: int = 1100) -> str:
    """Compact evidence digest injected into the writer prompts."""
    blocks = []
    for i, s in enumerate(sources, 1):
        excerpt = re.sub(r"\s+", " ", s.usable_text).strip()[:per_source_chars]
        blocks.append(
            f"[S{i}] Citation key: {s.cite_key}\n"
            f"Title: {s.title}\n"
            f"Source: {s.publisher} | URL: {s.url}\n"
            f"Excerpt: {excerpt}"
        )
    return "\n\n".join(blocks)
