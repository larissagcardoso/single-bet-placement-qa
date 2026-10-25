"""E2E: place a valid bet and check that what the customer saw is what was recorded.

Why this test: it is the revenue path that every customer takes. The slip, the receipt,
the header and the backend must agree on match, odds, payout and balance, and only the
browser can see all of them together. Expected values come from the API catalogue and
the payout formula, never from the same screen being checked.

Every mismatch is collected before failing, so one run shows every broken field.
"""
from decimal import Decimal

import pytest
from selenium.common.exceptions import TimeoutException

from framework.models import Selection
from framework.money import expected_payout
from framework.pages.betting_page import BettingPage

pytestmark = pytest.mark.ui

STAKE = Decimal("10.00")
SELECTION = Selection.HOME


def test_placed_bet_matches_what_the_customer_was_shown(
    settings, api, driver, screenshot, baseline_balance, future_match
):
    odds = future_match.odds_for(SELECTION)
    payout = expected_payout(STAKE, odds)
    balance_after = baseline_balance - STAKE
    mismatches: list[str] = []

    def check(label, actual, expected):
        if actual != expected:
            mismatches.append(f"{label}: expected {expected!r}, got {actual!r}")

    page = BettingPage(driver, settings.timeout).open(settings.app_url)
    check("header balance before the bet", page.wait_for_header_balance(baseline_balance), baseline_balance)

    page.select_odds(future_match.id, SELECTION)
    page.bet_slip.enter_stake(str(STAKE))
    check("slip potential payout", page.bet_slip.potential_payout(), payout)
    screenshot("bet slip before placing")

    page.bet_slip.place_bet()
    try:
        page.bet_slip.wait_until_placing()
    except TimeoutException:
        mismatches.append("Place Bet never showed the 'Placing...' state")

    receipt = page.receipt.wait_until_open().read()
    screenshot("receipt")
    check("receipt match (home first)", receipt.match, future_match.label)
    check("receipt stake", receipt.stake, STAKE)
    check("receipt odds", receipt.odds, odds)
    check("receipt potential payout", receipt.payout, payout)
    if not receipt.bet_id:
        mismatches.append("receipt has no bet id")
    if not receipt.placed_at:
        mismatches.append("receipt has no placement timestamp")
    # The receipt has no element for the selection, so that field is checked manually.

    check("backend balance after the bet", api.balance(), balance_after)
    check("header balance after the bet", page.wait_for_header_balance(balance_after), balance_after)

    page.receipt.close()
    screenshot("after closing the receipt")
    check("selections left after closing the receipt", page.bet_slip.selection_count(), 0)

    assert not mismatches, "Placed bet does not match what the customer was shown:\n- " + "\n- ".join(mismatches)
