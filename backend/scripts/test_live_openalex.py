"""Manual Live Connectivity Test Script for OpenAlex and Crossref.

Run directly via CLI to verify live network connectivity, polite pool response,
and inverted abstract index reconstruction:

    .venv\\Scripts\\python backend/scripts/test_live_openalex.py

DO NOT run during automated CI/pytest runs.
"""

__test__ = False

import asyncio
from backend.app.connectors.crossref_client import crossref_client
from backend.app.connectors.openalex_client import openalex_client


async def run_live_connections_check():
    print("===================================================================")
    print("Testing Live Scholarly Metadata APIs (Polite Pool)")
    print("===================================================================")

    # 1. Test OpenAlex Works Search
    query = "graph neural networks"
    print(f"\n[1/3] Querying OpenAlex Works API for query='{query}'...")
    try:
        works = await openalex_client.search_works(query=query, per_page=2)
        print(f"  [SUCCESS] OpenAlex returned {works['total_count']:,} total works.")
        if works["results"]:
            w = works["results"][0]
            print(f"  Top Result: \"{w['title']}\" ({w['publication_year']})")
            print(f"  DOI: {w['doi']} | Citations: {w['citation_count']:,}")
            print(f"  Reconstructed Abstract snippet: {w['abstract'][:120]}...")
    except Exception as e:
        print(f"  [FAILED] OpenAlex Works query failed: {e}")

    # 2. Test OpenAlex Authors Search
    print(f"\n[2/3] Querying OpenAlex Authors API for query='Yann LeCun'...")
    try:
        authors = await openalex_client.search_authors(query="Yann LeCun", per_page=1)
        if authors["results"]:
            a = authors["results"][0]
            print(f"  [SUCCESS] Found Author: {a['display_name']}")
            print(f"  Affiliation: {a['institution_name']}")
            print(f"  Works Count: {a['works_count']:,} | Citations: {a['cited_by_count']:,}")
    except Exception as e:
        print(f"  [FAILED] OpenAlex Authors query failed: {e}")

    # 3. Test Crossref DOI Lookup
    test_doi = "10.1145/3097983.3098194"
    print(f"\n[3/3] Querying Crossref API for DOI='{test_doi}'...")
    try:
        cr_work = await crossref_client.get_work_by_doi(test_doi)
        if cr_work:
            print(f"  [SUCCESS] Crossref resolved: \"{cr_work['title']}\"")
            print(f"  Venue / Container: {cr_work['venue']}")
            print(f"  Publication Year: {cr_work['publication_year']}")
        else:
            print("  [WARNING] Crossref returned no record for test DOI.")
    except Exception as e:
        print(f"  [FAILED] Crossref query failed: {e}")

    print("\n===================================================================")
    print("Live connectivity verification completed.")
    print("===================================================================")


if __name__ == "__main__":
    asyncio.run(run_live_connections_check())
