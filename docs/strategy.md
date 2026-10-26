# Strategy and Recommendations

Testing is risk-based: each scenario in the [test plan](test-plan.md) has a risk score
(impact × likelihood) that decides what is tested first, what is automated and what stays
manual. Automation follows the test pyramid: each risk is checked at the cheapest level that
can catch it. Terms follow ISTQB CTFL v4.0.

## Why these two tests over other candidates

**1. UI end-to-end: place a valid bet (TC-01)** – `tests/ui/test_place_bet_e2e.py`

- The highest-risk journey: every customer takes it and it moves money.
- A system-level test, because the risk sits in the integration: slip, receipt, header and
  backend must agree, and only the browser sees them all. Every mismatch is reported in one run.
- Expected values come from the API catalogue and the payout formula, never from the screen
  being checked. It is not marked `xfail`: it fails today on BUG-05, BUG-06 and BUG-07, and
  marking the whole journey would hide a new regression in any other field.

**2. API: invalid stakes are rejected and do not move money (TC-02)** – `tests/api/test_stake_validation.py`

- The API is the real control: UI validation can be bypassed, and §4.1 requires every stake
  rule on both layers. Fast and browser-free, so it runs on every commit.
- Cases come from the test plan's decision table: equivalence partitions (missing,
  non-numeric, negative) and boundary values (0.99, 100.01, three decimals). Only rejections
  are automated, so the test does not spend balance and a balance change is itself the defect.
- Known defects are strict `xfail` with their bug ID (today: `negative`, BUG-01). When the fix
  lands the run fails as "unexpectedly passed", turning the case into a confirmation test and
  then back into a regression test.

**Not chosen:** TC-03 needs an oracle tied to today's date, which ages with the calendar;
TC-04 depends on timing and would be flaky; the accepted stake cases spend balance on every
run. Automation has a maintenance cost, so the suite stays at two tests where each failure
has a single cause.

## What stays manual-only, and why

| Area | Why manual for now | Where it belongs as the suite grows |
|------|--------------------|-------------------------------------|
| TC-03 Pre-match only | The oracle depends on the current date | API test with a fixed date or catalogue |
| TC-04 Duplicate submission | Timing-dependent; flaky without a controlled environment | API / integration test |
| TC-05 Error modal and Rebet | Needs fault injection; stubbing the network in Selenium is brittle | Component test with a mocked API |
| TC-06 Filters | Low risk (score 8); pure client logic | Unit tests on the filter function |
| Exploratory testing | Error guessing and exploration find what the written cases miss | Stays manual |
| UI copy and layout | Needs human review | Stays manual |

## Top recommendations if this scales

### 1. Test data strategy

All tests share one account, so they run one at a time and a failed run can leave dirty state.
The only setup tool is unreliable too: the reset reports €125.50 but stores €120.00 (BUG-12),
so the suite re-reads the balance after every reset. Recommended: one test user per run (or
per parallel worker), and setup endpoints to set an exact balance, fix the catalogue date and
force a placement failure. This makes TC-03 to TC-05 automatable and allows parallel runs.

### 2. CI/CD and additional test layers

- **CI/CD:** already in place, the API test runs on every push and the full suite on demand,
  publishing an Allure report to GitHub Pages. Next: run the UI journey nightly and keep the
  Allure history, so trends and flaky tests become visible once the suite grows.
- **Additional test layers:** move rules down the pyramid. Unit and component tests for stake
  validation, payout and filters, written with the developers. Contract tests against the
  OpenAPI document catch schema drift, such as a missing field or an unexpected enum value,
  without any UI.

### 3. Spec clarifications

Assumptions A1–A7 in the test plan come from reviewing the spec (static testing). Agree on
them before adding tests, so the suite does not automate a guess. Most urgent: the minimum
stake, €1.00 or €1.01 (A1); when betting closes, given the API has no kickoff time (A2); the
error code for insufficient balance (A3); and the payout rounding rule (A4).
