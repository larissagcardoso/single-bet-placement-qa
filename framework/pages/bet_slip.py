from decimal import Decimal

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from framework.money import parse_money
from framework.pages.base_page import BasePage, by_id


class BetSlip(BasePage):
    COUNT = by_id("bet-slip-count")
    STAKE_INPUT = by_id("bet-slip-stake-input")
    TOTAL_STAKE = by_id("bet-slip-total-stake")
    POTENTIAL_PAYOUT = by_id("bet-slip-potential-payout")
    PLACE_BET = by_id("bet-slip-place-bet")

    def selection_count(self) -> int:
        return int(self._text(self.COUNT))

    @allure.step("Enter stake {stake}")
    def enter_stake(self, stake: str) -> None:
        field = self._visible(self.STAKE_INPUT)
        # Delete key by key: clear() does not trigger React's change handler.
        current = field.get_attribute("value") or ""
        field.send_keys(Keys.END, Keys.BACK_SPACE * len(current))
        field.send_keys(stake)

    def total_stake(self) -> Decimal:
        return parse_money(self._text(self.TOTAL_STAKE))

    def potential_payout(self) -> Decimal:
        return parse_money(self._text(self.POTENTIAL_PAYOUT))

    @allure.step("Place the bet")
    def place_bet(self) -> None:
        self._click(self.PLACE_BET)

    def shows_placing(self) -> bool:
        """True if the button switches to 'Placing...' after submit."""
        try:
            # Case-insensitive: CSS may render the label in upper case.
            self.wait.until(lambda _: "placing" in self._text(self.PLACE_BET).lower())
            return True
        except TimeoutException:
            return False
