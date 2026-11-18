import re
import unicodedata
import hashlib
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Normalizes arbitrary input text:
    - Replaces unicode variants with standard ASCII/NFKC normalization.
    - Converts multiple consecutive whitespace, tab, and newline characters into a single space.
    - Strips leading and trailing whitespace.
    Returns empty string if input is None.
    """
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Collapse multiple whitespace characters into single space
    text = re.sub(r"[\s\u00a0\u200b]+", " ", text)
    return text.strip()


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Normalizes a DOI string:
    - Trims whitespace.
    - Strips 'https://doi.org/' or 'http://dx.doi.org/' or 'doi:' prefix.
    - Converts to lowercase.
    Returns None if empty or invalid.
    """
    if not doi:
        return None
    cleaned = doi.strip().lower()
    cleaned = re.sub(r"^https?://(dx\.)?doi\.org/", "", cleaned)
    cleaned = re.sub(r"^doi:\s*", "", cleaned)
    cleaned = cleaned.strip()
    return cleaned if cleaned else None


def generate_title_hash(title: str, year: Optional[int] = None) -> str:
    """Generates a deterministic SHA-256 hash for deduplication:
    - Normalizes text.
    - Retains only lowercase alphanumeric characters.
    - Appends publication year if provided.
    """
    clean_title = normalize_text(title).lower()
    alphanumeric = re.sub(r"[^a-z0-9]", "", clean_title)
    seed = f"{alphanumeric}:{year or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    """Converts a title or name to a lowercase, hyphen-delimited slug.
    Example: 'Natural Language Processing' -> 'natural-language-processing'
    """
    normalized = normalize_text(text).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized)
    return slug.strip("-")
