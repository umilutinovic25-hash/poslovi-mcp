from pathlib import Path

from poslovi_mcp.boards import parse_details, parse_listing

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="ignore")


def test_parse_infostud_listing():
    jobs = parse_listing(_read("infostud.html"), "infostud")
    assert len(jobs) >= 5
    assert all(j.url.startswith("https://poslovi.infostud.com/posao/") for j in jobs)
    assert all(j.id.isdigit() for j in jobs)
    assert all(j.title and j.company for j in jobs)


def test_parse_helloworld_listing():
    jobs = parse_listing(_read("helloworld.html"), "helloworld")
    assert len(jobs) >= 10
    assert all(j.url.startswith("https://www.helloworld.rs/posao/") for j in jobs)
    assert all(j.board == "helloworld" for j in jobs)


def test_listing_deduplicates_by_id():
    jobs = parse_listing(_read("infostud.html"), "infostud")
    ids = [j.id for j in jobs]
    assert len(ids) == len(set(ids))


def test_parse_details():
    d = parse_details(_read("detail.html"), "https://poslovi.infostud.com/posao/x/y/741465")
    assert "Data Engineer" in d.title
    assert d.company == "Keba d.o.o."
    assert "Novi Sad" in d.location
    assert d.date_posted == "2026-06-30"
    assert d.apply_by == "2026-07-30"
    assert len(d.description) > 500
