from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bridgeclub_downloader.scraper import BridgeClubScraper
from bridgeclub_downloader.pbn_writer import PBNWriter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download bridge club results and export as PBN.")
    parser.add_argument("--url", type=str, help="A club result or player page URL to scrape.")
    parser.add_argument("--player-id", type=str, help="Bridge club player ID if the site uses player pages.")
    parser.add_argument("--pair-code", type=str, help="Optional pair code, for example ns-3 or ew-5.")
    parser.add_argument("--output", type=str, default="output.pbn", help="Output PBN file path.")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to inspect.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.url and not args.player_id:
        print("You must provide either --url or --player-id.", file=sys.stderr)
        return 2

    scraper = BridgeClubScraper()

    try:
        if args.url:
            page_html = scraper.fetch(args.url)
            boards = scraper.parse_page(args.url, page_html)
            history_urls = scraper.discover_history_urls(args.url, page_html)
            for item in history_urls[: args.max_pages]:
                try:
                    html = scraper.fetch(item)
                    boards.extend(scraper.parse_page(item, html))
                except Exception:
                    continue
        else:
            boards = scraper.scrape_player_pair(args.player_id, args.pair_code, max_pages=args.max_pages)

        if not boards:
            print("No result rows were discovered. The site structure may differ from the expected HTML layout.", file=sys.stderr)
            return 1

        output = Path(args.output)
        PBNWriter(boards).write(output)
        print(f"Exported {len(boards)} board(s) to {output}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
