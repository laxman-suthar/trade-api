import logging
from duckduckgo_search import DDGS
from typing import Optional

logger = logging.getLogger(__name__)


# ---------- Search queries builder ----------

def build_search_queries(sector: str) -> list[str]:
    """
    Build multiple targeted search queries for a sector.
    More queries = richer context for Gemini.
    """
    return [
        f"{sector} sector India stock market 2026",
        f"{sector} industry India latest news trade opportunities",
        f"BSE NSE {sector} sector performance outlook",
        f"India {sector} sector FDI investment trends 2026",
    ]


# ---------- Core search function ----------

def search_sector_data(sector: str, max_results_per_query: int = 5) -> list[dict]:
    """
    Run multiple DuckDuckGo searches for the sector.
    Returns a flat list of result dicts: {title, href, body}
    """
    queries = build_search_queries(sector)
    all_results = []
    seen_urls = set()  # avoid duplicate URLs across queries

    for query in queries:
        try:
            logger.info(f"Searching: {query}")
            results = DDGS().text(query, max_results=max_results_per_query)

            for r in results:
                url = r.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "snippet": r.get("body", ""),
                    })

        except Exception as e:
            # Don't crash if one query fails — just log and continue
            logger.warning(f"Search failed for query '{query}': {str(e)}")
            continue

    logger.info(f"Total results collected for '{sector}': {len(all_results)}")
    return all_results


# ---------- Format for Gemini ----------

def format_for_llm(sector: str, results: list[dict]) -> Optional[str]:
    """
    Takes raw search results and formats them into a clean
    context string that we'll pass to Gemini.
    """
    if not results:
        return None

    lines = [
        f"MARKET RESEARCH DATA FOR SECTOR: {sector.upper()}",
        f"Total sources collected: {len(results)}",
        "=" * 60,
        ""
    ]

    for i, r in enumerate(results, start=1):
        lines.append(f"[Source {i}]")
        lines.append(f"Title   : {r['title']}")
        lines.append(f"URL     : {r['url']}")
        lines.append(f"Snippet : {r['snippet']}")
        lines.append("")  # blank line between sources

    return "\n".join(lines)


# ---------- Main entry point ----------

def collect_sector_data(sector: str) -> Optional[str]:
    """
    Full pipeline:
      1. Search DuckDuckGo for the sector
      2. Deduplicate results
      3. Format into LLM-ready context string

    Returns formatted string, or None if no data found.
    """
    results = search_sector_data(sector)

    if not results:
        logger.error(f"No search results found for sector: {sector}")
        return None

    return format_for_llm(sector, results)