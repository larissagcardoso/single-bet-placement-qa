from dataclasses import dataclass
from decimal import Decimal

import allure

from framework.money import parse_money, to_money
from framework.pages.base_page import BasePage, by_id


@dataclass(frozen=True)
class Receipt:
    bet_id: str
    match: str
    stake: Decimal
    odds: Decimal
    payout: Decimal
    placed_at: str


class ReceiptModal(BasePage):
    ROOT = by_id("modal-success")
    BET_ID = by_id("modal-success-bet-id")
    MATCH = by_id("modal-success-match")
    STAKE = by_id("modal-success-stake")
    ODDS = by_id("modal-success-odds")
    PAYOUT = by_id("modal-success-payout")
    PLACED_AT = by_id("modal-success-placed-at")
    CLOSE = by_id("modal-success-close")

    def wait_until_open(self) -> "ReceiptModal":
        self._visible(self.ROOT)
        return self

    @allure.step("Read the receipt")
    def read(self) -> Receipt:
        return Receipt(
            bet_id=self._text(self.BET_ID),
            match=self._text(self.MATCH),
            stake=parse_money(self._text(self.STAKE)),
            odds=to_money(self._text(self.ODDS)),
            payout=parse_money(self._text(self.PAYOUT)),
            placed_at=self._text(self.PLACED_AT),
        )

    @allure.step("Close the receipt")
    def close(self) -> None:
        self._click(self.CLOSE)
        self._wait_until_gone(self.ROOT)
