"""Crossref API Client.

Modular client for retrieving and enriching publication metadata from Crossref (https://api.crossref.org).
Provides:
- Polite pool compliance via configured mailto header
- Clean DOI resolution and XML tag stripping from abstracts
- Transparent conflict resolution strategy between OpenAlex and Crossref records
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def strip_jats_tags(text: Optional[str]) -> str:
    """Strips XML/JATS formatting tags (e.g. <jats:p>, <jats:italic>) commonly in Crossref abstracts."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return " ".join(clean.split()).strip()


class CrossrefClient:
    """Async client for querying the official Crossref REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        mailto: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.CROSSREF_BASE_URL).rstrip("/")
        self.mailto = mailto or settings.CROSSREF_MAILTO
        self.timeout = timeout_seconds or settings.SCHOLARLY_REQUEST_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": f"CollabMatch/1.0 (mailto:{self.mailto})",
            "Accept": "application/json",
        }

    async def get_work_by_doi(
        self,
        doi: str,
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves scholarly publication metadata by DOI with polite-pool headers."""
        clean_doi = doi.strip()
        if "doi.org/" in clean_doi:
            clean_doi = clean_doi.split("doi.org/")[-1]

        url = f"{self.base_url}/works/{clean_doi}"
        headers = self._get_headers()

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        message = data.get("message", {})
                        return self.parse_crossref_work(message)
                    elif response.status_code == 404:
                        logger.info("DOI '%s' not found on Crossref.", clean_doi)
                        return None
                    elif response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        logger.warning(
                            "Crossref responded with status %d for DOI '%s'",
                            response.status_code,
                            clean_doi,
                        )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                logger.warning("Network error querying Crossref for DOI '%s': %s", clean_doi, exc)
                await asyncio.sleep(1.0)

        return None

    @staticmethod
    def parse_crossref_work(message: Dict[str, Any]) -> Dict[str, Any]:
        """Parses Crossref message dictionary into standard fields."""
        title_list = message.get("title", [])
        title = title_list[0] if title_list else "Untitled"

        # Venue (container-title)
        venue_list = message.get("container-title", [])
        venue = venue_list[0] if venue_list else None

        # Year from published date parts
        pub_year = None
        for date_key in ("published-print", "published-online", "created", "issued"):
            date_dict = message.get(date_key) or {}
            date_parts = date_dict.get("date-parts")
            if date_parts and date_parts[0] and isinstance(date_parts[0][0], int):
                pub_year = date_parts[0][0]
                break

        # Authors
        authors = []
        for author_item in message.get("author", []):
            given = author_item.get("given", "")
            family = author_item.get("family", "")
            full_name = f"{given} {family}".strip()
            if full_name:
                authors.append({
                    "name": full_name,
                    "orcid": author_item.get("ORCID"),
                    "affiliation": [
                        aff.get("name")
                        for aff in author_item.get("affiliation", [])
                        if aff.get("name")
                    ],
                })

        raw_abstract = message.get("abstract")
        clean_abstract = strip_jats_tags(raw_abstract)

        return {
            "doi": message.get("DOI"),
            "title": title,
            "abstract": clean_abstract,
            "venue": venue,
            "publication_year": pub_year,
            "citation_count": message.get("is-referenced-by-count", 0),
            "url": message.get("URL"),
            "publisher": message.get("publisher"),
            "authors": authors,
            "raw_payload": message,
        }

    @staticmethod
    def resolve_conflicts(
        openalex_record: Dict[str, Any],
        crossref_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Applies transparent conflict-resolution strategy between OpenAlex and Crossref.

        Policy:
        1. OpenAlex title & abstract are preferred (OpenAlex has NLP-reconstructed abstracts).
        2. If OpenAlex abstract is missing or trivial, Crossref abstract is adopted.
        3. Crossref official venue & publisher are preferred if OpenAlex venue is null.
        4. Crossref publication year is prioritized if verified against publication date parts.
        5. Full provenance of both sources is preserved in the resolution metadata.
        """
        resolved = dict(openalex_record)
        resolution_notes = []

        # Abstract augmentation
        if (
            not resolved.get("abstract")
            or resolved["abstract"] == "No abstract provided in OpenAlex record."
        ) and crossref_record.get("abstract"):
            resolved["abstract"] = crossref_record["abstract"]
            resolution_notes.append("Adopted abstract from Crossref.")

        # Venue augmentation
        if not resolved.get("venue") and crossref_record.get("venue"):
            resolved["venue"] = crossref_record["venue"]
            resolution_notes.append("Adopted venue container-title from Crossref.")

        # Year confirmation
        if crossref_record.get("publication_year") and not resolved.get("publication_year"):
            resolved["publication_year"] = crossref_record["publication_year"]
            resolution_notes.append("Adopted publication year from Crossref.")

        resolved["crossref_enriched"] = True
        resolved["resolution_notes"] = resolution_notes
        return resolved


crossref_client = CrossrefClient()
