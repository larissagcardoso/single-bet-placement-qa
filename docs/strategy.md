# Strategy and Recommendations

## Approach

Testing is **risk-based**: each scenario in the [test plan](test-plan.md) has a product-risk
score (likelihood × impact), and that score decides what is tested first, what is
automated and what stays manual. Automation follows the **test pyramid**: each risk is
checked at the cheapest test level that can detect it. Terms follow ISTQB CTFL v4.0.

## Why these two tests

**1. UI end-to-end: place a valid bet (TC-01)** — `tests/ui/test_place_bet_e2e.py`

- Highest-risk journey: every customer takes it, and it carries money (score 20).
- It is a **system-level** test because the risk sits in the integration: the slip, the
  receipt, the header and the API must agree. Only the browser can see all of them at once.
- One journey covers several requirements (§2.2–§2.4, Domain Context). Every field
  mismatch is collected before failing, so one run shows every broken field.
- The oracle comes from the API catalogue and the spec formula (stake × odds), never from
  values read on the same screen.

**2. API: invalid stakes are rejected and do not move money (TC-02)** —
`tests/api/test_stake_validation.py`

- The API is the real control. UI validation can be bypassed, and §4.1 requires every
  stake rule on both layers.
- Test data comes straight from the test plan's decision table: **equivalence partitions**
  (missing, non-numeric, negative) and **boundary values** (0.99, 100.01, 3 decimals).
- Only rejection cases are automated. They should not change state, so the test is
  repeatable on a shared account, and a balance change is itself the defect.
- Fast and browser-free: it can run on every commit.
- Known defects are marked `xfail(strict=True)` with their bug ID. When a fix lands, the
  test fails as "unexpectedly passed", which turns it into a **confirmation test** and then
  back into a plain **regression test**.
  <!-- TODO after execution: list which cases are xfail and their bug IDs. -->

**Candidates not chosen:** TC-03 needs a "today"-relative oracle that ages with the
calendar; the accepted stake cases spend balance on every run; TC-04 depends on timing and
would be flaky. Automation brings maintenance cost and can give false confidence, so the
suite is limited to two tests where each failure has a single cause.

## What stays manual, and why

| Area | Why manual for now |
|---|---|
| TC-03 Pre-match only | Oracle depends on the current date; needs a controllable clock or catalogue |
| TC-04 Duplicate submission | Concurrency is timing-dependent; an automated check would be flaky without a controlled environment |
| TC-05 Error modal and Rebet | Needs fault injection; stubbing network calls in Selenium is brittle |
| TC-06 Filters | Low risk (score 8); pure client logic that belongs in unit tests |
| Exploratory sessions | **Experience-based techniques** (error guessing, exploratory testing) find defects outside the written cases; their value is human judgement |
| UI copy and layout | Needs human review; automation would only compare strings |

## Where each scenario should live as the suite grows

| Scenario | Best test level | Reason |
|---|---|---|
| TC-01 | System (UI E2E) | Only the UI shows slip, receipt and header together |
| TC-02 | API + component | Business rules: many cheap, fast cases; UI messages in component tests |
| TC-03 | API, with controlled test data | Needs a fixed date or catalogue to stay deterministic |
| TC-04 | API / integration | Concurrency is a backend property |
| TC-05 | Component, with a mocked API | Failure can be forced reliably |
| TC-06 | Unit | Pure filtering logic |

## Recommendations if this project scales

### 1. Test data strategy

All tests share one user and one balance today, so they must run one at a time and a failed
run can leave dirty state. Recommended:

- one test user per run (or per parallel worker);
- setup endpoints to set an exact balance, fix the catalogue date, and force a placement
  failure.

This makes TC-03 to TC-05 automatable and allows parallel runs.
<!-- TODO after execution: add what was observed about reset-balance as evidence. -->

### 2. CI/CD and additional test layers

- **CI/CD:** API tests run on every pull request (seconds, no browser). The UI journey runs
  headless on merge and nightly; failure screenshots are kept as build artifacts.
- **Additional test layers:** move rules down the pyramid. Unit and component tests for
  stake validation, payout calculation and filters, written with the developers (shift
  left). Contract tests against the OpenAPI document catch response-schema drift, such as a
  missing field or an unexpected enum value, without any UI.

### 3. Spec clarifications

Assumptions A1–A7 in the test plan come from reviewing the spec (static testing). Agree on
them before adding more tests, so the suite does not automate a guess that later has to be
rewritten. The most urgent:

- minimum stake: €1.00 or €1.01 (A1);
- when betting closes, given that the API has no kickoff time (A2);
- error code for insufficient balance (A3);
- payout rounding rule (A4).
