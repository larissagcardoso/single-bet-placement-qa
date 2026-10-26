import base64
import re
from datetime import UTC, datetime
from pathlib import Path

import allure
import pytest
import pytest_html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from framework.api_client import BettingApi
from framework.config import Settings
from framework.models import Match

ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"
SCREENSHOTS = pytest.StashKey[list]()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def api(settings):
    client = BettingApi(settings.base_url, settings.user_id, settings.timeout)
    yield client
    client.close()


@pytest.fixture
def baseline_balance(api):
    """Known starting balance for a test that moves money."""
    return api.reset_and_read_balance()


@pytest.fixture
def future_match(api) -> Match:
    """First match dated after today (UTC), so the pre-match rule cannot cause a failure.

    Today is excluded: the API has no kickoff time, so a match dated today may have started.
    """
    today = datetime.now(UTC).date()
    match = next((m for m in api.matches() if m.kickoff_date > today), None)
    if match is None:
        pytest.fail("No future match in the catalogue; cannot build test data.")
    return match


@pytest.fixture
def driver(settings):
    options = Options()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--lang=en-US")  # same date and number format on every machine
    browser = webdriver.Chrome(options=options)  # Selenium Manager resolves chromedriver
    yield browser
    browser.quit()


@pytest.fixture
def screenshot(request, driver):
    """Captures a named screenshot: saved to artifacts/ and attached to both reports."""

    def capture(name: str) -> None:
        _store(request.node, name, driver.get_screenshot_as_base64())

    return capture


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    driver = item.funcargs.get("driver")
    if report.failed and driver is not None:
        # Taken here, not in teardown, so it shows the page at the moment of failure.
        _store(item, "at failure", driver.get_screenshot_as_base64())
    shots = item.stash.get(SCREENSHOTS, [])
    if shots:
        report.extras = getattr(report, "extras", []) + [pytest_html.extras.png(png, name) for name, png in shots]


def _store(item, name: str, png_base64: str) -> None:
    item.stash.setdefault(SCREENSHOTS, []).append((name, png_base64))
    png = base64.b64decode(png_base64)
    allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    ARTIFACTS.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", f"{item.name} {name}".lower()).strip("-")
    (ARTIFACTS / f"{slug}.png").write_bytes(png)
