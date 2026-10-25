"""Typed views of API payloads, so tests read as business rules instead of dict lookups."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from framework.money import to_money


class Selection(StrEnum):
    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


@dataclass(frozen=True)
class Match:
    id: str
    competition: str
    kickoff_date: date
    home_team: str
    away_team: str
    odds: dict[Selection, Decimal]

    @classmethod
    def from_json(cls, data: dict) -> "Match":
        return cls(
            id=data["id"],
            competition=data["competition"],
            kickoff_date=date.fromisoformat(data["kickoffDate"]),
            home_team=data["homeTeam"],
            away_team=data["awayTeam"],
            odds={selection: to_money(data["odds"][selection.value.lower()]) for selection in Selection},
        )

    @property
    def label(self) -> str:
        """Home team first, as the match list and the receipt must show it."""
        return f"{self.home_team} vs {self.away_team}"

    def odds_for(self, selection: Selection) -> Decimal:
        return self.odds[selection]
