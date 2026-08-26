"""
MediSimply MCP Client
======================
Thin async wrapper so app.py can call the `search_medicine` tool exposed by
mcp_server/medicine_search_server.py over real MCP (stdio transport), without
app.py needing to know anything about the MCP protocol itself.

Design note: each call spins up a short-lived subprocess + MCP session rather
than keeping one connection open for the app's whole lifetime. For a single
on-demand tool call this is the simplest correct option - no shared session
state to manage across FastAPI's synchronous request handlers - and the extra
subprocess-startup latency (well under a second) is a fine trade-off for this
project's scope.
"""

import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = Path(__file__).parent / "mcp_server" / "medicine_search_server.py"

_server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER_SCRIPT)],
)


async def call_search_medicine(drug_name: str) -> dict:
    """
    Call the `search_medicine` MCP tool for `drug_name`.

    Returns the tool's JSON result as a dict, e.g.
    {"found": True, "drug_name": ..., "indications_and_usage": ..., ...}
    or {"found": False, "drug_name": drug_name} if openFDA had nothing.

    On any connection/protocol failure this returns
    {"found": False, "error": str(e)} instead of raising, so a live-lookup
    failure degrades gracefully (the caller falls back to "ai_knowledge_only")
    rather than crashing the /lookup request.
    """
    try:
        async with stdio_client(_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("search_medicine", {"drug_name": drug_name})

                if result.isError:
                    detail = result.content[0].text if result.content else "Unknown MCP tool error"
                    return {"found": False, "error": detail}

                for content in result.content:
                    if content.type == "text":
                        return json.loads(content.text)

                return {"found": False, "error": "Empty MCP tool response"}
    except Exception as e:
        return {"found": False, "error": str(e)}
