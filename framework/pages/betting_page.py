from decimal import Decimal

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from framework.models import Selection
from framework.money import parse_money
from framework.pages.base_page import BasePage, by_id
from framework.pages.bet_slip import BetSlip
from framework.pages.receipt_modal import ReceiptModal


class BettingPage(BasePage):
    """The single page of the app: header, match list, bet slip and receipt."""

    HEADER_BALANCE = by_id("header-balance")
    MATCH_LIST = by_id("match-list")
    MATCH_LIST_LOADING = by_id("match-list-loading")

    def __init__(self, driver, timeout: float):
        super().__init__(driver, timeout)
        self.bet_slip = BetSlip(driver, timeout)
        self.receipt = ReceiptModal(driver, timeout)

    @staticmethod
    def odds_button(match_id: str, selection: Selection):
        return by_id(f"odds-{match_id}-{selection.value.lower()}")

    def open(self, url: str) -> "BettingPage":
        self.driver.get(url)
        self._wait_until_gone(self.MATCH_LIST_LOADING)
        self._visible(self.MATCH_LIST)
        return self

    def header_balance(self) -> Decimal:
        return parse_money(self._text(self.HEADER_BALANCE))

    def wait_for_header_balance(self, expected: Decimal, timeout: float = 5) -> Decimal:
        """Gives the header a moment to update, then returns what it shows."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda _: self.header_balance() == expected)
        except TimeoutException:
            pass
        return self.header_balance()

    def select_odds(self, match_id: str, selection: Selection) -> None:
        self._click(self.odds_button(match_id, selection))
        self.wait.until(lambda _: self.bet_slip.selection_count() == 1)
