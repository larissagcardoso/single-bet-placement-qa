# Single Bet Placement – QA

Risk-based test plan, execution results and a small Python automation framework for the
Single Bet Placement feature of https://qae-assignment-tau.vercel.app/.

## Deliverables

| Part | Deliverable | File |
|------|-------------|------|
| A1 | Test plan: 6 prioritised scenarios | [`docs/test-plan.md`](docs/test-plan.md) |
| A2 | Execution results and bug reports | [`docs/execution-results.md`](docs/execution-results.md) |
| B | Automation framework and 2 tests | [`framework/`](framework/), [`tests/`](tests/) |
| C | Strategy and recommendations | [`docs/strategy.md`](docs/strategy.md) |

**Results at a glance:** the top 3 scenarios all fail. 13 bugs reported (3 Critical, 4 High,
6 Medium) plus 8 minor findings, each with evidence in [`docs/evidence/`](docs/evidence/).
The Critical ones let money move against the business rules: negative stakes credit the
balance, the balance can go negative from the normal UI, and matches already played accept bets.

## Tech stack

Python 3.11 · Selenium 4 · pytest 9 · requests · desktop Chrome.

Extra tooling, kept small on purpose:

| Tool | Why |
|------|-----|
| `pytest-html` | One self-contained HTML report with the UI screenshots embedded; no Java needed (unlike Allure) |
| `python-dotenv` | Reads the user id from a local `.env` file, so it is never committed |
| Selenium Manager | Built into Selenium; downloads the matching chromedriver automatically |
| GitHub Actions | Runs the API tests on every push (see [CI](#ci)) |

## Setup

Requires Python 3.11+ and Google Chrome.

```bash
git clone https://github.com/larissagcardoso/single-bet-placement-qa.git
cd single-bet-placement-qa
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your user id:

```bash
USER_ID=<your-user-id>
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `USER_ID` | *(required)* | Sent as `?user-id=` in the UI and as the `x-user-id` header in the API |
| `BASE_URL` | `https://qae-assignment-tau.vercel.app` | Target environment |
| `HEADLESS` | `true` | Set `false` to watch the browser |
| `TIMEOUT` | `15` | Seconds for explicit waits and HTTP calls |

## Running the tests

```bash
pytest            # everything
pytest -m api     # API test only, no browser
pytest -m ui      # UI journey only
```

Every run writes `artifacts/report.html` (open it in a browser) with the UI screenshots: bet
slip, receipt, page after closing the receipt, and the page at the moment of a failure.

### Expected result against the current build

```
7 passed, 1 xfailed, 1 failed
```

| Test | Result | Why |
|------|--------|-----|
| `test_invalid_stake_is_rejected_without_moving_money` (8 cases) | 7 passed, 1 xfailed | `negative` is a strict `xfail` linked to BUG-01 |
| `test_placed_bet_matches_what_the_customer_was_shown` | failed | Catches BUG-05 (payout), BUG-06 (team order) and BUG-07 (stale balance), all reported in one message |

The UI failure is the test doing its job. When a bug is fixed, the matching check passes; when
BUG-01 is fixed, the `xfail` turns into "unexpectedly passed" and fails the run, so the marker
has to be removed.

**Note:** the tests share one account balance, so run them one at a time (the default). Each
UI run places a real €10.00 bet; tests reset the balance before they start.

## Project structure

```text
.
├── framework/                        # reusable test framework
│   ├── config.py                     # settings from environment variables / .env
│   ├── api_client.py                 # one method per endpoint; returns the raw response
│   ├── models.py                     # Match and Selection: typed view of the API payload
│   ├── money.py                      # Decimal parsing, rounding, payout formula
│   └── pages/                        # page objects (Selenium)
│       ├── base_page.py              # explicit-wait helpers
│       ├── betting_page.py           # header, match list, odds buttons
│       ├── bet_slip.py               # stake, totals, Place Bet
│       └── receipt_modal.py          # success receipt
├── tests/
│   ├── conftest.py                   # fixtures: settings, API client, balance, test match, browser
│   ├── api/test_stake_validation.py  # API test
│   └── ui/test_place_bet_e2e.py      # UI test
├── docs/
│   ├── test-plan.md                  # Part A1
│   ├── execution-results.md          # Part A2
│   ├── strategy.md                   # Part C
│   ├── evidence/                     # screenshots and API logs used by the bug reports
│   └── requirements/                 # assignment and feature specification
├── .github/workflows/tests.yml       # CI
├── pytest.ini                        # markers, HTML report, strict xfail
├── requirements.txt                  # pinned dependencies
└── .env.example                      # template for the local .env
```

## Design decisions

- **The API is the source of truth.** Expected values come from the match catalogue and the
  payout formula, and balances are checked on the backend, never only on the screen.
- **One cause per failure.** The test match is picked from the API with a kickoff date after
  today, so the pre-match rule cannot make a test fail for the wrong reason. The API test only
  sends invalid stakes: they must not move money, so a balance change is itself the defect.
- **Stable, explicit UI automation.** Page objects use the app's `id` attributes and explicit
  waits only; no `sleep`, no implicit waits. Page objects return values and never assert.
- **Money as `Decimal`**, so `24.50` never compares as `24.499999`.
- **All mismatches in one run.** The UI test collects every broken field before failing.
- **Setup does not trust the reset.** The reset response and the stored balance differ
  (BUG-12), so fixtures re-read `GET /api/balance`.

Why these two tests, and what stayed manual: [`docs/strategy.md`](docs/strategy.md).

## CI

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs the API test on every push and
pull request: fast, no browser, green while BUG-01 is open thanks to the `xfail`. The full suite,
including the UI journey, runs on demand from the Actions tab (*Run workflow*), because the UI
test fails on known product bugs. Both upload the HTML report as an artifact. The user id comes
from the `USER_ID` repository secret.
