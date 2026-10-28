from __future__ import annotations

from pathlib import Path
from typing import Iterable

from bridgeclub_downloader import BoardResult


class PBNWriter:
    def __init__(self, board_results: Iterable[BoardResult]):
        self.board_results = list(board_results)

    def write(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "% PBN 2.1",
            "[Generator \"Bridge Club Downloader\"]",
            "",
        ]

        for result in self.board_results:
            lines.extend([
                f"[Board \"{result.board_number or 'unknown'}\"]",
                f"[Dealer \"{result.dealer or '?'}\"]",
                f"[Vulnerable \"{result.vulnerability or '?'}\"]",
                f"[Deal \"{result.deal or 'N:????????'}\"]",
                f"[Contract \"{result.contract or '?'}\"]",
                f"[Declarer \"{result.declarer or '?'}\"]",
                f"[Result \"{result.result or '?'}\"]",
            ])

            if result.lead:
                lines.append(f"[Lead \"{result.lead}\"]")
            if result.source_url:
                lines.append(f"[Source \"{result.source_url}\"]")
            if result.played_on:
                lines.append(f"[Date \"{result.played_on}\"]")

            lines.append("")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
