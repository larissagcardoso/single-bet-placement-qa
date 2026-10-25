"""API: invalid stakes are rejected and never move money.

Why this test: stake limits are the platform's financial guardrail, and the API is the
real control, because UI validation can be bypassed with browser dev tools. The cases are
the rejection rows of TC-02's decision table (equivalence partitions and boundary values).
Only rejections are automated: they should not change state, so the test is repeatable,
and a balance change is itself the defect.
"""
import pytest

from framework.models import Selection

pytestmark = pytest.mark.api

MISSING = object()


@pytest.mark.parametrize(
    ("stake", "expected_error"),
    [
        pytest.param(MISSING, None, id="missing"),
        pytest.param("abc", "invalid_stake_type", id="non-numeric"),
        pytest.param("10", "invalid_stake_type", id="numeric-string"),
        pytest.param(
            -5,
            "invalid_stake_min",
            id="negative",
            marks=pytest.mark.xfail(reason="BUG-01: negative stake is accepted and credits the balance"),
        ),
        pytest.param(0, "invalid_stake_min", id="zero"),
        pytest.param(0.99, "invalid_stake_min", id="below-minimum"),
        pytest.param(100.01, "invalid_stake_max", id="above-maximum"),
        pytest.param(1.005, "invalid_stake_precision", id="three-decimals"),
    ],
)
def test_invalid_stake_is_rejected_without_moving_money(api, baseline_balance, future_match, stake, expected_error):
    body = {"matchId": future_match.id, "selection": Selection.HOME.value}
    if stake is not MISSING:
        body["stake"] = stake

    response = api.place_bet(body)

    assert response.status_code == 422, f"stake={stake!r}: {response.status_code} {response.text}"
    if expected_error is not None:
        assert response.json().get("error") == expected_error
    assert api.balance() == baseline_balance, "a rejected bet must not change the balance"
