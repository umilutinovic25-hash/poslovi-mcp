"""Scrapers for Serbian job boards.

Both boards (poslovi.infostud.com and helloworld.rs) run on the same
platform, so listing pages share the posting-URL pattern
``/posao/{slug}/{company-slug}/{id}`` and detail pages embed a
schema.org ``JobPosting`` JSON-LD block.
"""

from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .models import Job, JobDetails

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "poslovi-mcp/0.1 (+https://github.com/umilutinovic25-hash/poslovi-mcp)"
)

BOARDS = {
    "infostud": "https://poslovi.infostud.com",
    "helloworld": "https://www.helloworld.rs",
}

_POSAO_RE = re.compile(r"/posao/([^/]+)/([^/]+)/(\d+)")


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=20,
    )


def _slug_to_words(slug: str) -> str:
    return unescape(slug).replace("-", " ").strip()


def parse_listing(html: str, board: str) -> list[Job]:
    """Extract job listings from a search-results page."""
    base = BOARDS[board]
    soup = BeautifulSoup(html, "html.parser")
    jobs: dict[str, Job] = {}
    for a in soup.find_all("a", href=True):
        m = _POSAO_RE.search(a["href"])
        if not m:
            continue
        slug, company_slug, job_id = m.groups()
        text = a.get_text(" ", strip=True)
        # Anchor text is the card title when present; slug is the fallback.
        title = text if 5 <= len(text) <= 120 else _slug_to_words(slug).title()
        url = urljoin(base, urlparse(a["href"]).path)
        if job_id not in jobs or (text and len(text) > len(jobs[job_id].title)):
            jobs[job_id] = Job(
                title=title,
                company=_slug_to_words(company_slug).title(),
                url=url,
                board=board,
                id=job_id,
            )
    return list(jobs.values())


def parse_details(html: str, url: str) -> JobDetails:
    """Extract full posting details from a job page (JSON-LD first)."""
    posting: dict = {}
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    ):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                posting = item
                break

    org = posting.get("hiringOrganization") or {}
    loc = posting.get("jobLocation") or {}
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    address = (loc.get("address") or {}) if isinstance(loc, dict) else {}
    locality = address.get("addressLocality") or address.get("streetAddress") or ""
    if isinstance(locality, list):
        locality = ", ".join(dict.fromkeys(locality))

    qualifications = posting.get("qualifications") or []
    if isinstance(qualifications, str):
        qualifications = [qualifications]
    elif isinstance(qualifications, dict):
        qualifications = [
            str(v) for k, v in qualifications.items()
            if k != "@type" and isinstance(v, str)
        ]

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    body_text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))

    return JobDetails(
        title=(posting.get("title") or soup.title.get_text(strip=True) if soup.title else "").strip(),
        company=(org.get("name") or "").strip(),
        url=url,
        location=str(locality),
        date_posted=str(posting.get("datePosted") or ""),
        apply_by=str(posting.get("validThrough") or "")[:10],
        employment_type=str(posting.get("employmentType") or ""),
        description=body_text[:6000],
        qualifications=[str(q) for q in qualifications],
    )


def search(query: str, board: str = "infostud", page: int = 1) -> list[Job]:
    """Search one board for ``query`` and return parsed listings."""
    if board not in BOARDS:
        raise ValueError(f"Unknown board {board!r}; choose from {sorted(BOARDS)}")
    url = f"{BOARDS[board]}/oglasi-za-posao?q={quote_plus(query)}"
    if page > 1:
        url += f"&page={page}"
    with _client() as client:
        resp = client.get(url)
        resp.raise_for_status()
    return parse_listing(resp.text, board)


def search_all(query: str, page: int = 1) -> list[Job]:
    """Search every supported board, de-duplicated by posting id."""
    seen: dict[str, Job] = {}
    for board in BOARDS:
        for job in search(query, board=board, page=page):
            seen.setdefault(job.id, job)
    return list(seen.values())


def fetch_details(url: str) -> JobDetails:
    """Fetch and parse a single posting page."""
    host = urlparse(url).netloc
    if not any(urlparse(base).netloc == host for base in BOARDS.values()):
        raise ValueError(f"URL host {host!r} is not a supported job board")
    with _client() as client:
        resp = client.get(url)
        resp.raise_for_status()
    return parse_details(resp.text, url)
