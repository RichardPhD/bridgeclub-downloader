from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from bridgeclub_downloader import BoardResult


class BridgeClubScraper:
    """Scrape HTML result pages and discover historical board links."""

    def __init__(self, base_url: str = "https://undercroft.bridgeaustralia.org"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Accept-Language": "en-AU,en;q=0.9",
        })

    def fetch(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def build_player_pair_url(self, player_id: str, pair_code: str | None = None) -> str:
        if pair_code:
            return f"{self.base_url}/showplayer.asp?id={player_id}&pair={pair_code}"
        return f"{self.base_url}/showplayer.asp?id={player_id}"

    def discover_history_urls(self, page_url: str, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: List[str] = []
        seen = set()

        for link in soup.select("a[href]"):
            href = link.get("href", "")
            text = (link.get_text(" ", strip=True) or "").lower()
            if not href:
                continue

            lower = href.lower()
            if any(token in lower for token in ["showplayer", "board", "history", "result", "pair", "round"]):
                full_url = urljoin(page_url, href)
                parsed = urlparse(full_url)
                if parsed.scheme and parsed.netloc and full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)
                    continue

            if any(token in text for token in ["history", "previous", "board", "result", "round"]):
                full_url = urljoin(page_url, href)
                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)

        return urls

    def parse_page(self, page_url: str, html: str) -> List[BoardResult]:
        soup = BeautifulSoup(html, "html.parser")
        rows = self._find_result_rows(soup)
        results: List[BoardResult] = []

        for row in rows:
            board = self._row_to_board_result(row, page_url)
            if board and (board.board_number or board.contract or board.result or board.deal):
                results.append(board)

        if not results:
            text = soup.get_text(" ", strip=True)
            if re.search(r"\bboard\b|\bcontract\b|\bdealer\b|\bvulnerable\b", text, re.I):
                results.append(
                    BoardResult(
                        board_number="unknown",
                        raw_text=text,
                        source_url=page_url,
                    )
                )

        return results

    def _find_result_rows(self, soup: BeautifulSoup):
        candidates = []
        for table in soup.select("table"):
            rows = table.select("tr")
            if len(rows) < 2:
                continue
            candidates.extend(rows)

        if not candidates:
            return soup.select("tr")
        return candidates

    def _row_to_board_result(self, row, page_url: str) -> BoardResult | None:
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            return None

        row_text = " ".join(cell.get_text(" ", strip=True) for cell in cells)
        if not re.search(r"\b(board|contract|dealer|result|vulnerable)\b", row_text, re.I):
            return None

        board_number = self._extract_board_number(row_text)
        dealer = self._extract_from_text(row_text, [r"\bdealer\s*[:\-]?\s*([A-Z])", r"\bdealer\b\s*([A-Z])"]) or ""
        vulnerability = self._extract_from_text(row_text, [r"\bvulnerable\s*[:\-]?\s*([A-Za-z\- ]+)", r"\bvul\s*[:\-]?\s*([A-Za-z\- ]+)"]) or ""
        contract = self._extract_from_text(row_text, [r"\b([1-7][A-Z]+|PASS|1NT|2NT|3NT|4NT|5NT|6NT|7NT)\b", r"\b((?:[1-7])\s*(?:C|D|H|S|NT))\b"]) or ""
        declarer = self._extract_from_text(row_text, [r"\bdeclarer\s*[:\-]?\s*([NESW])", r"\bdecl\s*[:\-]?\s*([NESW])"]) or ""
        result = self._extract_from_text(row_text, [r"\bresult\s*[:\-]?\s*([+-]?\d+)", r"\bscore\s*[:\-]?\s*([+-]?\d+)"]) or ""
        lead = self._extract_from_text(row_text, [r"\blead\s*[:\-]?\s*([A-Z0-9]+)"]) or ""
        deal = self._extract_deal(row_text, row)

        if not any([board_number, dealer, contract, result, deal]):
            return None

        return BoardResult(
            board_number=board_number or "unknown",
            dealer=dealer,
            vulnerability=vulnerability,
            contract=contract,
            declarer=declarer,
            result=result,
            lead=lead,
            source_url=page_url,
            raw_text=row_text,
            deal=deal,
            played_on=self._extract_date(row_text),
        )

    def _extract_board_number(self, text: str) -> str:
        match = re.search(r"\bboard\s*[:#-]?\s*(\d+)", text, re.I)
        if match:
            return match.group(1)
        match = re.search(r"\b(\d{1,3})\s*(?:board|hand)\b", text, re.I)
        if match:
            return match.group(1)
        return ""

    def _extract_deal(self, text: str, row) -> str:
        match = re.search(r"(?:N:|S:|E:|W:)[^\n]+", text, re.I)
        if match:
            return match.group(0).strip()

        for candidate in row.find_all(string=True):
            piece = str(candidate).strip()
            if re.search(r"(?:N:|S:|E:|W:)", piece, re.I):
                return piece
        return ""

    def _extract_date(self, text: str) -> str:
        patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(\w+\s+\d{1,2},\s*\d{4})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1)
        return ""

    def _extract_from_text(self, text: str, patterns: Iterable[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return ""

    def scrape_player_pair(self, player_id: str, pair_code: str | None = None, max_pages: int = 10):
        page_urls = [self.build_player_pair_url(player_id, pair_code)]
        results: List[BoardResult] = []

        for page_url in page_urls[:max_pages]:
            html = self.fetch(page_url)
            results.extend(self.parse_page(page_url, html))

            for history_url in self.discover_history_urls(page_url, html):
                if history_url not in page_urls:
                    page_urls.append(history_url)
                if len(page_urls) >= max_pages:
                    break

            if len(page_urls) >= max_pages:
                break

            for next_page in page_urls:
                if next_page == page_url:
                    continue
                try:
                    html = self.fetch(next_page)
                    results.extend(self.parse_page(next_page, html))
                except requests.HTTPError:
                    continue

        return results


def extract_history_links_from_url(url: str) -> List[str]:
    scraper = BridgeClubScraper()
    try:
        html = scraper.fetch(url)
    except Exception:
        return []
    return scraper.discover_history_urls(url, html)
