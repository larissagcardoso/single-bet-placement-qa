"""Money helpers. Amounts are compared as Decimal, never float."""
import re
from decimal import ROUND_HALF_UP, Decimal

_AMOUNT = re.compile(r"-?\d+(?:\.\d+)?")
CENT = Decimal("0.01")


def to_money(value) -> Decimal:
    """Rounds to cents, half-up (assumed: no rounding rule is defined)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_money(text: str) -> Decimal:
    """Reads the amount from UI text such as 'Balance: €108.90' or '€-10.00'."""
    found = _AMOUNT.search(text.replace(",", ""))
    if found is None:
        raise ValueError(f"No amount found in {text!r}")
    return to_money(found.group())


def expected_payout(stake, odds) -> Decimal:
    """Payout includes the stake: stake x odds."""
    return to_money(Decimal(str(stake)) * Decimal(str(odds)))
