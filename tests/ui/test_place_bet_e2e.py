"""E2E: place a valid bet and check that what the customer saw is what was recorded.

Why this test: it is the revenue path that every customer takes. The slip, the receipt,
the header and the backend must agree on match, odds, payout and balance, and only the
browser can see all of them together. Expected values come from the API catalogue and
the payout formula, never from the same screen being checked.

Every mismatch is collected before failing, so one run shows every broken field.
"""
from decimal import Decimal

import allure
import pytest

from framework.models import Selection
from framework.money import expected_payout
from framework.pages.betting_page import BettingPage
from framework.soft_checks import SoftChecks

pytestmark = [
    pytest.mark.ui,
    allure.feature("Bet placement UI"),
    allure.story("Place a valid single bet"),
    allure.severity(allure.severity_level.CRITICAL),
]

STAKE = Decimal("10.00")
SELECTION = Selection.HOME


@allure.title("Placed bet matches what the customer was shown")
def test_placed_bet_matches_what_the_customer_was_shown(
    settings, api, driver, screenshot, baseline_balance, future_match
):
    odds = future_match.odds_for(SELECTION)
    payout = expected_payout(STAKE, odds)
    balance_after = baseline_balance - STAKE
    soft = SoftChecks()

    page = BettingPage(driver, settings.timeout).open(settings.app_url)
    soft.check("header balance before the bet", page.wait_for_header_balance(baseline_balance), baseline_balance)

    page.select_odds(future_match.id, SELECTION)
    page.bet_slip.enter_stake(str(STAKE))
    soft.check("slip potential payout", page.bet_slip.potential_payout(), payout)
    screenshot("bet slip before placing")

    page.bet_slip.place_bet()
    soft.check("Place Bet shows 'Placing...'", page.bet_slip.shows_placing(), True)

    receipt = page.receipt.wait_until_open().read()
    screenshot("receipt")
    soft.check("receipt match (home first)", receipt.match, future_match.label)
    soft.check("receipt stake", receipt.stake, STAKE)
    soft.check("receipt odds", receipt.odds, odds)
    soft.check("receipt potential payout", receipt.payout, payout)
    soft.check("receipt has a bet id", bool(receipt.bet_id), True)
    soft.check("receipt has a placement time", bool(receipt.placed_at), True)
    # The receipt has no element for the selection, so that field is checked manually.

    soft.check("backend balance after the bet", api.balance(), balance_after)
    soft.check("header balance after the bet", page.wait_for_header_balance(balance_after), balance_after)

    page.receipt.close()
    screenshot("after closing the receipt")
    soft.check("selections left after closing the receipt", page.bet_slip.selection_count(), 0)

    soft.assert_all("Placed bet does not match what the customer was shown")
