"""Standalone CLI — works without any MCP client or API key."""

from __future__ import annotations

import argparse
import sys

from . import boards


def _print_jobs(jobs) -> None:
    if not jobs:
        print("Nema rezultata.")
        return
    width = max(len(j.title) for j in jobs)
    width = min(width, 60)
    for i, j in enumerate(jobs, 1):
        title = j.title if len(j.title) <= 60 else j.title[:57] + "..."
        print(f"{i:3d}. {title:<{width}}  {j.company}  [{j.board}]")
        print(f"     {j.url}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="poslovi",
        description="Pretraga srpskih job board-ova (Infostud, HelloWorld.rs).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="pretraži oglase")
    p_search.add_argument("query", help='npr. "python developer"')
    p_search.add_argument(
        "--board",
        choices=[*boards.BOARDS, "all"],
        default="all",
        help="koji board (podrazumevano: svi)",
    )
    p_search.add_argument("--page", type=int, default=1, help="strana rezultata")

    p_show = sub.add_parser("show", help="prikaži ceo oglas")
    p_show.add_argument("url", help="URL oglasa iz rezultata pretrage")

    args = parser.parse_args(argv)

    if args.command == "search":
        if args.board == "all":
            jobs = boards.search_all(args.query, page=args.page)
        else:
            jobs = boards.search(args.query, board=args.board, page=args.page)
        _print_jobs(jobs)
    elif args.command == "show":
        d = boards.fetch_details(args.url)
        print(f"{d.title}")
        print(f"Firma:      {d.company}")
        print(f"Lokacija:   {d.location}")
        print(f"Objavljeno: {d.date_posted}    Rok: {d.apply_by}")
        if d.employment_type:
            print(f"Tip:        {d.employment_type}")
        if d.qualifications:
            print(f"Uslovi:     {', '.join(d.qualifications)}")
        print("-" * 60)
        print(d.description)
    return 0


if __name__ == "__main__":
    sys.exit(main())
