"""OpenAlex API Client.

Modular, production-ready client for the official OpenAlex REST API (https://api.openalex.org).
Provides scholarly entity search for Works, Authors, and Institutions, with:
- Polite pool compliance via configured mailto email
- Abstract reconstruction from OpenAlex inverted index
- Robust error handling, timeouts, and exponential backoff
- Full provenance preservation and clean record parsing
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def reconstruct_abstract_from_inverted_index(
    inverted_index: Optional[Dict[str, List[int]]],
) -> str:
    """Reconstructs linear text from OpenAlex's abstract_inverted_index.

    In OpenAlex works payloads:
    abstract_inverted_index = {"The": [0], "model": [1, 5], "demonstrates": [2], ...}
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""

    position_map: Dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            position_map[pos] = word

    if not position_map:
        return ""

    max_pos = max(position_map.keys())
    # Reconstruct array in order, falling back to empty string if a position was missed
    words = [position_map.get(i, "") for i in range(max_pos + 1)]
    return " ".join(w for w in words if w).strip()


class OpenAlexClient:
    """Async client for querying the official OpenAlex API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        mailto: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.OPENALEX_BASE_URL).rstrip("/")
        self.mailto = mailto or settings.OPENALEX_MAILTO
        self.api_key = api_key or settings.OPENALEX_API_KEY
        self.timeout = timeout_seconds or settings.SCHOLARLY_REQUEST_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": f"CollabMatch/1.0 (mailto:{self.mailto})",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["api_key"] = self.api_key
        return headers

    def _get_params(self, extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = {"mailto": self.mailto}
        if extra_params:
            for k, v in extra_params.items():
                if v is not None and v != "":
                    params[k] = v
        return params

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Executes an HTTP GET request with exponential backoff on 429 / 5xx."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        query_params = self._get_params(params)
        headers = self._get_headers()

        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=query_params, headers=headers)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", 2 ** attempt))
                        logger.warning(
                            "OpenAlex rate limit encountered (429). Retrying after %.2fs...",
                            retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    elif response.status_code >= 500:
                        logger.warning(
                            "OpenAlex server error %d. Retrying (attempt %d/%d)...",
                            response.status_code,
                            attempt + 1,
                            max_retries,
                        )
                        await asyncio.sleep(2 ** attempt)
                        continue
                    elif response.status_code == 404:
                        return {"meta": {"count": 0}, "results": []}
                    else:
                        response.raise_for_status()

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                logger.warning(
                    "Network error connecting to OpenAlex: %s. Retrying...", str(exc)
                )
                await asyncio.sleep(1.5 ** attempt)

        logger.error("Failed to query OpenAlex endpoint %s after %d retries.", endpoint, max_retries)
        if last_error:
            raise last_error
        return {"meta": {"count": 0}, "results": [], "error": "Request failed after retries"}

    async def search_works(
        self,
        query: str,
        institution_ror: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
        from_publication_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Searches OpenAlex works (publications) with optional institution & year filters."""
        params: Dict[str, Any] = {
            "search": query,
            "page": page,
            "per_page": min(per_page, 50),
        }

        # Build filter argument
        filters = []
        if institution_ror:
            filters.append(f"institutions.ror:{institution_ror}")
        if from_publication_year:
            filters.append(f"from_publication_date:{from_publication_year}-01-01")

        if filters:
            params["filter"] = ",".join(filters)

        raw = await self._request("works", params=params)
        results = [self.parse_work_preview(w) for w in raw.get("results", [])]
        meta = raw.get("meta", {})

        return {
            "total_count": meta.get("count", 0),
            "page": meta.get("page", page),
            "per_page": per_page,
            "results": results,
        }

    async def search_authors(
        self,
        query: str,
        institution_ror: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """Searches OpenAlex authors (researchers) with optional institution filter."""
        params: Dict[str, Any] = {
            "search": query,
            "page": page,
            "per_page": min(per_page, 50),
        }

        if institution_ror:
            params["filter"] = f"last_known_institutions.ror:{institution_ror}"

        raw = await self._request("authors", params=params)
        results = [self.parse_author_preview(a) for a in raw.get("results", [])]
        meta = raw.get("meta", {})

        return {
            "total_count": meta.get("count", 0),
            "page": meta.get("page", page),
            "per_page": per_page,
            "results": results,
        }

    async def search_institutions(
        self,
        query: str,
        page: int = 1,
        per_page: int = 5,
    ) -> List[Dict[str, Any]]:
        """Searches academic institutions to look up ROR identifiers."""
        params = {"search": query, "page": page, "per_page": per_page}
        raw = await self._request("institutions", params=params)
        out = []
        for inst in raw.get("results", []):
            out.append({
                "openalex_id": inst.get("id"),
                "display_name": inst.get("display_name"),
                "ror": inst.get("ror"),
                "country_code": inst.get("country_code"),
                "works_count": inst.get("works_count", 0),
                "cited_by_count": inst.get("cited_by_count", 0),
                "homepage_url": inst.get("homepage_url"),
            })
        return out

    async def get_work_by_id(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single work by OpenAlex ID or DOI."""
        clean_id = openalex_id.strip()
        endpoint = f"works/{clean_id}"
        data = await self._request(endpoint)
        if not data or "id" not in data:
            return None
        return self.parse_work_preview(data)

    async def get_author_by_id(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single author profile by OpenAlex ID."""
        clean_id = openalex_id.strip()
        endpoint = f"authors/{clean_id}"
        data = await self._request(endpoint)
        if not data or "id" not in data:
            return None
        return self.parse_author_preview(data)

    @staticmethod
    def parse_work_preview(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts canonical work metadata and linearizes inverted abstract index."""
        inverted = raw.get("abstract_inverted_index")
        abstract = reconstruct_abstract_from_inverted_index(inverted)

        # Primary location venue
        venue = None
        primary_loc = raw.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        if source:
            venue = source.get("display_name")

        # Authors
        authors = []
        for authorship in raw.get("authorships", []):
            author_info = authorship.get("author") or {}
            authors.append({
                "name": author_info.get("display_name", "Unknown Author"),
                "openalex_id": author_info.get("id"),
                "institutions": [
                    inst.get("display_name")
                    for inst in authorship.get("institutions", [])
                    if inst.get("display_name")
                ],
            })

        # Concepts / Topics
        concepts = [
            c.get("display_name")
            for c in raw.get("concepts", [])
            if c.get("display_name")
        ]

        doi = raw.get("doi")
        if doi and "doi.org/" in doi:
            doi = doi.split("doi.org/")[-1]

        return {
            "openalex_id": raw.get("id"),
            "title": raw.get("title") or "Untitled Publication",
            "abstract": abstract or "No abstract provided in OpenAlex record.",
            "publication_year": raw.get("publication_year"),
            "venue": venue,
            "doi": doi,
            "citation_count": raw.get("cited_by_count", 0),
            "url": raw.get("doi") or raw.get("id"),
            "authors": authors,
            "topics": concepts[:8],
            "raw_payload": raw,
        }

    @staticmethod
    def parse_author_preview(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts canonical researcher metadata from author payload."""
        # Last known institution
        last_inst = raw.get("last_known_institution") or {}
        institution_name = last_inst.get("display_name")
        institution_ror = last_inst.get("ror")

        # Topics / Concepts
        topics = [
            t.get("display_name")
            for t in raw.get("x_concepts", [])
            if t.get("display_name")
        ]

        display_name = raw.get("display_name", "Unknown Researcher")
        parts = display_name.split()
        first_name = parts[0] if parts else "Unknown"
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        return {
            "openalex_id": raw.get("id"),
            "display_name": display_name,
            "first_name": first_name,
            "last_name": last_name,
            "works_count": raw.get("works_count", 0),
            "cited_by_count": raw.get("cited_by_count", 0),
            "institution_name": institution_name,
            "institution_ror": institution_ror,
            "orcid": raw.get("orcid"),
            "topics": topics[:8],
            "raw_payload": raw,
        }


openalex_client = OpenAlexClient()
