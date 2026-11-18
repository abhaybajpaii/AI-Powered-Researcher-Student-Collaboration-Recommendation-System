import pytest
from backend.app.ingestion.preprocessing import (
    generate_title_hash,
    normalize_doi,
    normalize_text,
    slugify,
)


def test_normalize_text():
    raw = "   This   is   a   \n\t  messy   string   with   extra \u00a0 spaces.  "
    expected = "This is a messy string with extra spaces."
    assert normalize_text(raw) == expected
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1000/182") == "10.1000/182"
    assert normalize_doi("http://dx.doi.org/10.1000/182") == "10.1000/182"
    assert normalize_doi("DOI: 10.1000/182 ") == "10.1000/182"
    assert normalize_doi(" 10.1000/182 ") == "10.1000/182"
    assert normalize_doi(None) is None
    assert normalize_doi("") is None


def test_generate_title_hash():
    title1 = "Scalable Graph Neural Networks for Biological Structures!"
    title2 = "scalable graph neural networks for biological structures"
    title3 = "  Scalable, Graph-Neural Networks: for Biological Structures... "

    hash1 = generate_title_hash(title1, 2024)
    hash2 = generate_title_hash(title2, 2024)
    hash3 = generate_title_hash(title3, 2024)

    # Hashes should be identical regardless of punctuation, case, and whitespace
    assert hash1 == hash2 == hash3
    assert len(hash1) == 64

    # Different year yields different hash
    diff_year_hash = generate_title_hash(title1, 2023)
    assert hash1 != diff_year_hash


def test_slugify():
    assert slugify("Natural Language Processing (NLP)") == "natural-language-processing-nlp"
    assert slugify("Zero-Knowledge Proofs & Cryptography!") == "zero-knowledge-proofs-cryptography"
    assert slugify("   Deep   Learning   ") == "deep-learning"
