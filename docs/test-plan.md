# Test Plan – Single Bet Placement

**Application:** https://qae-assignment-tau.vercel.app/
**Scope:** pre-match single football bets on desktop Chrome, through the UI and the API behind it.
**Out of scope:** live betting, accumulators, other sports, mobile UX.
**References:** `§` = section of the Feature Specification. "Domain Context" = section of the HQA Take-Home Task.

Where a rule must hold on both layers (§4.1), both are tested. UI validation can be bypassed,
so the API is the real line of defence.

## Summary

| ID | Title | Priority | Score | Layer | Technique |
|----|-------|----------|-------|-------|-----------|
| TC-01 | Valid bet: slip, receipt and balance agree | Critical | 20 | UI + API | State transition |
| TC-02 | Stake rules are enforced on UI and API | Critical | 20 | UI + API | Decision table, BVA, EP |
| TC-03 | Only pre-match events accept bets | Critical | 20 | UI + API | Equivalence partitioning |
| TC-04 | A bet cannot be placed twice | High | 15 | UI + API | Error guessing |
| TC-05 | Failed placement recovers safely | High | 12 | UI | State transition |
| TC-06 | Filters include their bounds and reject invalid ranges | Medium | 8 | UI | BVA |

**Executed in Part A2:** TC-01, TC-02 and TC-03. They tie on score; the order follows exposure:
TC-01 is the path every customer takes, TC-02 can be exploited by anyone with browser dev
tools, TC-03 needs knowledge of a result.

## How priority was set

**Score = Impact × Likelihood**, each from 1 to 5. These are estimates made before execution.

- **Impact:** 5 = money moves incorrectly or regulatory exposure · 4 = user sees wrong
  financial data · 3 = core flow confusing, workaround exists · 2 = secondary feature
  degraded · 1 = cosmetic.
- **Likelihood** grows with the number of risk factors: rule implemented twice (UI and API),
  async or concurrent behaviour, money arithmetic, date logic, ambiguity in the spec.
- **Priority:** Critical ≥ 20 · High 12–19 · Medium 6–11 · Low ≤ 5.

## Before every scenario

- Run one scenario at a time; nobody else uses the same user id.
- **Baseline balance (B):** call `POST /api/reset-balance`, then read `GET /api/balance`.
  Use the value read back, not the reset response (A6).
- **Test match:** pick one from `GET /api/matches` with a kickoff date after today. Never
  hard-code an id (A2).
- Read `GET /api/balance` after every step that may move money.
- If a precondition cannot be set up, record the scenario as **Blocked**, never Passed.

---

## TC-01 – Valid bet: slip, receipt and balance agree

**Priority:** Critical · score 20 (impact 5 × likelihood 4)

**Risk rationale:** This is the revenue path. If the slip, the receipt and the stored bet
disagree, the customer is promised one payout and settled on another. The same data passes
through four places (catalogue, slip, API, receipt) with money arithmetic and an async
submit, so a mismatch is likely. (§2.2–§2.4; Domain Context "Payout", "Bet Receipt",
"Match Ordering")

**Preconditions**
- Baseline balance B and test match M.
- Note M's home team, away team and home odds. With two-decimal odds, 10.00 × odds is exact
  in cents, so no rounding rule is needed (A4).

**Steps**
1. Open the app with `?user-id=<id>`.
2. Click odds **1** on match M.
3. Enter stake `10.00`.
4. Click **Place Bet** and watch the button.
5. Read every field of the receipt, and the `POST /api/place-bet` response in DevTools → Network.
6. Without reloading, check the header and slip balance, then call `GET /api/balance`.
7. Close the receipt.

**Expected result**
- The header shows B when the page opens.
- The slip shows one selection: M, Home, home odds.
- The slip shows stake €10.00, available balance B and potential payout = 10.00 × odds.
- The button shows `Placing...`, then exactly one outcome: the success receipt.
- The receipt shows a Bet ID, **"Home vs Away"** with the home team first, selection Home,
  stake €10.00, the same odds, payout = 10.00 × odds and a timestamp.
- The API response has the same stake, odds and payout, and `currency: "EUR"`.
- Header, slip and API all show **B − 10.00**.
- After closing, there is no active selection and the stake is cleared.

---

## TC-02 – Stake rules are enforced on UI and API

**Priority:** Critical · score 20 (impact 5 × likelihood 4)

**Risk rationale:** Stake limits are the platform's financial guardrail. A gap lets a user bet
outside the limits, bet money they do not have, or credit the account with a negative stake.
Each rule is implemented twice, the boundaries are money values, and the spec contradicts
itself on the minimum (A1). (§3, §4.1, §4.4)

**Preconditions**
- Baseline balance B and test match M.
- Step order matters: the accepted `100.00` bet also brings the balance below €100, so the
  balance rule can then be tested apart from the maximum rule.

**Test data** – decision table conditions: numeric? · ≤ 2 decimals? · ≥ minimum? · ≤ €100.00? · ≤ balance?

| Stake | Partition | UI expected | API expected |
|-------|-----------|-------------|--------------|
| *(empty / omitted)* | missing | Place Bet disabled | 422 |
| `abc` / `"10"` | non-numeric | not accepted, Place Bet disabled | 422 `invalid_stake_type` |
| `-5` | negative | not accepted | 422 `invalid_stake_min` |
| `0` | zero | "Minimum stake is €1.00" | 422 `invalid_stake_min` |
| `0.99` | just below minimum | "Minimum stake is €1.00" | 422 `invalid_stake_min` |
| `1.00` | minimum (A1) | accepted | 200 |
| `1.01` | just above minimum | accepted | 200 |
| `100.00` | maximum | accepted | 200 (run first) |
| `100.01` | just above maximum | "Maximum stake is €100.00" | 422 `invalid_stake_max` |
| `1.005` | 3 decimals | third decimal not accepted; value shown = value placed | 422 `invalid_stake_precision` |
| current balance | equal to balance | accepted | 200 (run last) |
| current balance + 0.01 | above balance | "Insufficient balance" | 4xx (A3) |

**Steps**
1. API: right after the reset, place `100.00`. The balance is now below €100.
2. UI: reload, select odds on M and enter each value. Record the message and whether Place
   Bet is enabled. Accepted values are not placed from the UI.
3. API: send every rejection case and read `GET /api/balance` after each one.
4. API: place `1.00` and `1.01`, then a stake equal to the current balance.

**Expected result**
- Every row behaves as in the table. Error codes are the ones documented in the OpenAPI contract.
- Every rejected case leaves the balance **unchanged**.
- The balance never goes below €0.00.

---

## TC-03 – Only pre-match events accept bets

**Priority:** Critical · score 20 (impact 5 × likelihood 4)

**Risk rationale:** A bet on a match that has already been played is a guaranteed win for
anyone who knows the result: direct loss and a licensing issue. It relies on date logic, the
API exposes no kickoff time (A2), and API validation does not list the rule (A5).
(§1, §3 "Event type")

**Preconditions**
- Baseline balance B.
- From `GET /api/matches`, note a match **P** dated before today and a match **F** dated after today.

**Steps**
1. UI: check whether P appears in the match list.
2. If it does, select odds on P, enter `5.00` and click Place Bet.
3. API: `POST /api/place-bet` for P (HOME, stake 5), then `GET /api/balance`.
4. Control: repeat step 3 for F.

**Expected result**
- P is not listed, or cannot be selected; the UI does not place the bet.
- The API rejects P with a 4xx and the balance is unchanged.
- F is accepted (200), which shows the rejection of P is caused by its date.
- Matches dated *today* are not judged (A2).

---

## TC-04 – A bet cannot be placed twice

**Priority:** High · score 15 (impact 5 × likelihood 3)

**Risk rationale:** Double clicks, slow networks and retries send duplicate requests. A gap
charges the customer twice for one bet. The spec defines `409` for "bet already in
progress". (§2.3, §5.3)

**Preconditions**
- Baseline balance B and test match M.

**Steps**
1. UI: enter stake `5.00` and double-click Place Bet; count `place-bet` requests in DevTools.
2. API: send three identical `POST /api/place-bet` requests in parallel.
3. Call `GET /api/balance`.

**Expected result**
- UI: the button is disabled while `Placing...`; only one request is sent.
- API: exactly one `200`, the others `409`.
- Balance = B − 5.00.

> Sending requests together does not prove the server processed them at the same time. If
> more than one returns `200`, compare their timings before reporting a defect.

---

## TC-05 – Failed placement recovers safely

**Priority:** High · score 12 (impact 4 × likelihood 3)

**Risk rationale:** After a failure the customer must know the bet was not placed and must have
a safe retry. A wrong retry path creates duplicates or loses the stake. (§2.3, §2.5)

**Preconditions**
- A valid selection and stake.
- Failure forced with DevTools → Network → block request URL `/api/place-bet`.

**Steps**
1. Click Place Bet and read the modal.
2. Click **Rebet** while still blocked; then unblock and click **Rebet** again.
3. Force a new failure and click **Close**. Repeat with the top-right **X**.
4. Call `GET /api/balance` after each step.

**Expected result**
- Modal title is "Something went wrong"; the body says the bet could not be processed and
  suggests trying again.
- Rebet closes the modal and sends one new request; after unblocking, one bet is placed and
  charged once.
- Close and X close the modal and clear the selection and stake.
- Failed attempts never change the balance.

> A blocked request never reaches the server, so this does not cover a bet that the server
> stored but whose response was lost. The spec does not define that case.

---

## TC-06 – Filters include their bounds and reject invalid ranges

**Priority:** Medium · score 8 (impact 2 × likelihood 4)

**Risk rationale:** Wrong filtering hides matches the user is looking for, but moves no money.
Inclusive bounds and date handling are classic off-by-one sources. (§2.6)

**Preconditions**
- From `GET /api/matches`, pick a match **Q** and note its lowest and highest odds.
- Pick a date **D** with at least one match.

**Steps**
1. Odds filter: min = Q's lowest odd, max = Q's highest odd.
2. Odds filter: min 5.00, max 2.00.
3. Date filter: single day D.
4. Date filter: a range whose first and last days both have matches.

**Expected result**
- Q is shown. All its odds are inside or on the bounds, so this holds whichever way the
  filter combines odds (A7).
- The reversed range is rejected with clear feedback, and the list is not filtered.
- Matches on D are shown.
- Matches on both edge days of the range are shown.

---

## Assumptions and open questions

| # | Gap in the spec | Assumption used | Question for Product |
|---|-----------------|-----------------|----------------------|
| A1 | Minimum stake is €1.00 in §3, §4.4 and the OpenAPI contract (§5.2), but €1.01 in §4.1 | €1.00 is valid | Which is correct? |
| A2 | §2.1 asks for a kickoff date/time; the API has only `kickoffDate` | Matches dated today are not judged | When does betting close for a match? |
| A3 | No error code for insufficient balance | Any 4xx, with balance unchanged | Should it be `422 insufficient_balance`? |
| A4 | No payout rounding rule | Avoided in TC-01; half-up assumed while exploring | Which rule, and the same in UI and API? |
| A5 | "Upcoming only" (§2.1, §3) is not listed in API validation (§4.2) | The API must reject past matches | Confirm the API enforces it |
| A6 | OpenAPI says the reset response "may differ from persisted balance"; §5.3 says it must match | §5.3 wins | Fix the API docs |
| A7 | Odds filter (§2.6): does a match qualify when *any* or *all* of its odds are in range? | TC-06 uses data valid either way | Which rule applies? |

## Considered, not prioritized

- **API protocol checks** (400 / 401 / 405, §4.3) – low business impact; covered while exploring.
- **Replacing and removing a selection** (§2.1, §2.2) – simple client state; partly covered by TC-01.
- **Reset balance consistency** (§5.3) – a test-support endpoint; checked as a precondition in every scenario.
- **Odds range and static odds** (§3) – catalogue data, not user input.
- **Kickoff time label** (§2.1) – cosmetic, and blocked by A2.
