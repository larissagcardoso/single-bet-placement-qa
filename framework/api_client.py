"""Thin client for the betting API.

Endpoint methods return the raw Response so tests own the assertions.
Setup helpers raise on failure, so a broken precondition never looks like a product defect.
"""
from decimal import Decimal

import requests

from framework.models import Match
from framework.money import to_money


class BettingApi:
    def __init__(self, base_url: str, user_id: str, timeout: float):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["x-user-id"] = user_id

    def close(self) -> None:
        self.session.close()

    def _call(self, method: str, path: str, **kwargs) -> requests.Response:
        return self.session.request(method, self.base_url + path, timeout=self.timeout, **kwargs)

    def get_matches(self) -> requests.Response:
        return self._call("GET", "/api/matches")

    def get_balance(self) -> requests.Response:
        return self._call("GET", "/api/balance")

    def reset_balance(self) -> requests.Response:
        return self._call("POST", "/api/reset-balance")

    def place_bet(self, payload: dict) -> requests.Response:
        """Sends the body as-is, so tests can omit fields or send wrong types."""
        return self._call("POST", "/api/place-bet", json=payload)

    def matches(self) -> list[Match]:
        response = self.get_matches()
        response.raise_for_status()
        return [Match.from_json(item) for item in response.json()]

    def balance(self) -> Decimal:
        response = self.get_balance()
        response.raise_for_status()
        return to_money(response.json()["balance"])

    def reset_and_read_balance(self) -> Decimal:
        """Reads the persisted balance back instead of trusting the reset response."""
        self.reset_balance().raise_for_status()
        return self.balance()
