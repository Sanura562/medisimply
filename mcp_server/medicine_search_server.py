"""
MediSimply MCP Server
======================
Exposes exactly ONE tool over the Model Context Protocol (MCP), via stdio
transport: `search_medicine`.

Why this exists:
    MediSimply's local databases (drug_data.json / medicines_db.json) only
    cover a fixed list of Sri Lanka essential medicines. When a user searches
    for something outside that list, this server lets Gemini (via function
    calling, see app.py) autonomously reach out to the LIVE openFDA API
    instead of the app silently falling back to unverified "AI knowledge".

Reuses the same request pattern as build_dataset.py's fetch_drug() (requests
to https://api.fda.gov/drug/label.json, same style of param/timeout/cleanup),
but adds a generic_name -> brand_name -> substance_name fallback chain so more
real-world drug names can be resolved live, not just generic-name matches.

Run standalone for a manual smoke test (it will then sit waiting on stdio for
an MCP client - see mcp_client.py - to connect; Ctrl+C to quit):
    python mcp_server/medicine_search_server.py
"""

import requests
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://api.fda.gov/drug/label.json"

# The openFDA label fields we surface to the LLM for grounding.
FIELDS = [
    "indications_and_usage",
    "dosage_and_administration",
    "warnings",
    "adverse_reactions",
    "contraindications",
    "active_ingredient",
]

mcp = FastMCP("medisimply-medicine-search")


def _clean_text(text: str) -> str:
    """Collapse whitespace and cap length (same idea as build_dataset.clean_text)."""
    cleaned = " ".join(text.split())
    if len(cleaned) > 1000:
        cleaned = cleaned[:1000] + "..."
    return cleaned


def _query_openfda(field: str, drug_name: str):
    """One openFDA lookup against openfda.<field>. Returns the first result dict, or None."""
    params = {"search": f'openfda.{field}:"{drug_name}"', "limit": 1}
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        results = data.get("results") or []
        return results[0] if results else None
    except requests.RequestException:
        return None


@mcp.tool()
def search_medicine(drug_name: str) -> dict:
    """
    Look up a medicine LIVE on openFDA when it is not in MediSimply's local
    databases. Tries generic_name, then brand_name, then substance_name, in
    that order (same fallback order as build_dataset.py's fetch_drug).

    Args:
        drug_name: The medicine name to look up.

    Returns:
        {"found": True, "drug_name": ..., "matched_by": <field>, ...openFDA fields...}
        or {"found": False, "drug_name": drug_name} if openFDA has nothing.
    """
    result = None
    matched_by = None
    for field in ("generic_name", "brand_name", "substance_name"):
        result = _query_openfda(field, drug_name)
        if result:
            matched_by = field
            break

    if not result:
        return {"found": False, "drug_name": drug_name}

    info = {"found": True, "drug_name": drug_name, "matched_by": matched_by}
    for field in FIELDS:
        values = result.get(field)
        if values:
            info[field] = _clean_text(values[0])

    return info


if __name__ == "__main__":
    mcp.run(transport="stdio")
