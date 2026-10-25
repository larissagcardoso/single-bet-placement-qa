# Feature Specification

## Single Bet Placement

## 1. Feature Overview

Users can place a single bet on a sports event outcome. This is the core betting functionality that allows customers to wager money on match results with odds.

- **Platform:** Desktop web application
- **Sport:** Soccer/Football only
- **Event Type:** Upcoming/Pre-match events only (no live betting)
- **Bet Type:** Single bet only (no accumulator/multi-bets)

**Out of scope:**

- Live betting
- Multi-bets/accumulators
- Other sports
- Mobile-specific UX requirements

## 2. Functional Requirements

### 2.1 Match List

- Display upcoming football matches.
- Each match shows:
  - home team vs away team
  - kickoff date/time label
  - three selectable odds buttons: `1`, `X`, `2`
- Selecting a new odds button replaces the previous selection.
- User clicks on odds to select outcome for betting.
- Clicking new odds replaces previous selection.

### 2.2 Bet Slip

- Right-side fixed bet slip.
- Shows one active selection at a time.
- Shows entered stake, available balance, and computed potential payout.
- Includes:
  - `Place Bet`
  - `Remove All`
  - per-selection remove (`x`)

### 2.3 Place Bet Interaction

- On submit, button enters loading state (`Placing...`).
- After submit, the UI must show an in-progress state and resolve to one final outcome (success or failure).
- On success:
  - stake is deducted
  - success receipt modal appears
- On failure:
  - error modal appears with retry option

### 2.4 Success Receipt

Receipt must show:

- Bet ID
- Match details
- Selection
- Stake
- Odds at placement
- Potential payout
- Placement timestamp

Closing receipt returns user to main flow without active selection.

### 2.5 Error Modal

- Modal title: `Something went wrong`.
- Modal body explains that the bet could not be processed and suggests trying again.
- Actions:
  - `Rebet` (primary): on click it closes the modal and retries placement.
  - `Close` (secondary): closes modal and clears current selection/stake.
  - top-right `X`: same behavior as `Close`.

### 2.6 Filters

- Date filter supports single day or date range (inclusive).
- Odds filter supports min/max range (inclusive) and must reject invalid ranges with clear feedback.

## 3. Business Rules

| Rule | Expected Behavior |
|---|---|
| Sport | Football/Soccer only |
| Event type | Upcoming matches only |
| Bet type | Single bet only |
| Stake min (per bet) | €1.00 |
| Stake max (per bet) | €100.00 |
| Stake precision | Up to 2 decimal places |
| Minimum odds | 1.01 |
| Maximum odds | 1000.00 |
| Odds behavior | Static for session |
| Currency | EUR (€) |

## 4. Validation Rules

### 4.1 Stake Validation (UI and API)

| Field | Rule | Layer | Expected Result |
|---|---|---|---|
| Stake | Required to place bet | UI + API | Placement blocked/rejected if missing |
| Stake | Must be numeric | UI + API | Reject non-numeric values |
| Stake | Minimum €1.01 (positive values) | UI + API | Show/reject with minimum message |
| Stake | Maximum €100.00 | UI + API | Show/reject with maximum message |
| Stake | Max 2 decimal places | UI + API | Reject invalid precision |
| Stake | Must not exceed available balance | UI + API | Show/reject as insufficient balance |

### 4.2 Selection and Match Validation

| Field | Rule | Layer | Expected Result |
|---|---|---|---|
| Selection | Required | UI + API | Placement blocked/rejected if missing |
| Selection | Must be one of `HOME`, `DRAW`, `AWAY` | API | Reject invalid values |
| Match ID | Required and non-empty | API | Reject missing/blank value |
| Match ID | Must exist in match catalog | API | Reject unknown match |

### 4.3 Request/Protocol Validation

| Rule | Layer | Expected Result |
|---|---|---|
| Request body must be valid JSON object | API | Reject malformed/non-object payloads |
| Unsupported HTTP method | API | Return method-not-allowed response |
| Missing/invalid user context (`x-user-id`) | API | Reject as unauthorized |

### 4.4 UI Error Messaging (minimum expected copy)

- `Minimum stake is €1.00`
- `Maximum stake is €100.00`
- `Insufficient balance`

**UI input format behavior:**

- Stake input accepts numeric values with a single decimal separator and up to 2 decimal places.

## 5. Backend API

### 5.1 Authentication / User Context

All API endpoints require:

`x-user-id: <string>`

### 5.2 API Documentation

- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/docs?format=json`

### 5.3 Endpoints

#### `GET /api/matches`

Returns match list.

**200 response:**

```text
id: string
competition: string
kickoffDate: string (YYYY-MM-DD)
homeTeam: string
awayTeam: string
odds: { home: number; draw: number; away: number }
```

#### `GET /api/balance`

Returns user balance.

**200 response:**

```text
balance: number
currency: "EUR"
```

#### `POST /api/place-bet`

Places one bet.

**Request body:**

```text
matchId: string
selection: "HOME" | "DRAW" | "AWAY"
stake: number
```

Extra fields may be ignored by the API.

**200 response:**

```text
message: string
matchId: string
selection: "HOME" | "DRAW" | "AWAY"
stake: number
odds: number
payout: number
balance: number
currency: "EUR"
```

**Expected error classes:**

| HTTP status | Description |
|---|---|
| 400 | malformed payload |
| 401 | unauthorized user context |
| 405 | method not allowed |
| 409 | bet already in progress (same user) |
| 422 | semantic validation failures (selection/stake/match) |
| 500 | unexpected server failure |

#### `POST /api/reset-balance`

Resets user balance to initial configured value.

**200 response:**

```text
message: string
balance: number
currency: "EUR"
```

Response body and persisted state must be consistent after reset.
