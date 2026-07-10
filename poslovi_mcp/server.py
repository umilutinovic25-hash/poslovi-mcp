"""MCP server exposing Serbian job-board search to any MCP client."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import boards

mcp = FastMCP(
    "poslovi",
    instructions=(
        "Search Serbian job boards (poslovi.infostud.com and helloworld.rs). "
        "Use search_jobs to find postings, then get_job for the full text of "
        "one posting."
    ),
)


@mcp.tool()
def search_jobs(query: str, board: str = "all", page: int = 1) -> str:
    """Search job postings on Serbian job boards.

    Args:
        query: Search terms, e.g. "python developer" or "AI engineer".
        board: "infostud", "helloworld", or "all" (default) for both.
        page: Results page, starting at 1.

    Returns:
        JSON list of postings with title, company, url, board, and id.
    """
    if board == "all":
        jobs = boards.search_all(query, page=page)
    else:
        jobs = boards.search(query, board=board, page=page)
    return json.dumps([j.to_dict() for j in jobs], ensure_ascii=False, indent=1)


@mcp.tool()
def get_job(url: str) -> str:
    """Fetch one job posting and return its full details.

    Args:
        url: Posting URL returned by search_jobs.

    Returns:
        JSON object with title, company, location, dates, employment type,
        qualifications, and the posting text.
    """
    return json.dumps(boards.fetch_details(url).to_dict(), ensure_ascii=False, indent=1)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
