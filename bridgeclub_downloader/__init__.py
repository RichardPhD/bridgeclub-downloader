from __future__ import annotations

__all__ = [
    "BoardResult",
    "HistoricalBoard",
    "PlayerPairRecord",
]

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class BoardResult:
    board_number: str = ""
    dealer: str = ""
    vulnerability: str = ""
    contract: str = ""
    declarer: str = ""
    result: str = ""
    lead: str = ""
    notes: str = ""
    source_url: str = ""
    played_on: Optional[str] = None
    deal: str = ""
    raw_text: str = ""


@dataclass
class HistoricalBoard:
    board_number: str = ""
    event_name: str = ""
    session_date: Optional[date] = None
    raw_text: str = ""
    board_data: dict = field(default_factory=dict)


@dataclass
class PlayerPairRecord:
    player_id: str = ""
    pair_code: str = ""
    display_name: str = ""
    source_url: str = ""
    boards: list[BoardResult] = field(default_factory=list)
