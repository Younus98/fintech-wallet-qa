# Bug Report – Mini Wallet API

Defects found during manual exploratory testing of the Mini Wallet API (via Swagger UI).
Each bug will be linked to the automated test that catches it and the commit that fixes it.

**Environment:** local, `uvicorn app.main:app --reload`, Swagger UI at `http://127.0.0.1:8000/docs`
**Tested by:** Muhammad Younus Safdar
**Test type:** Exploratory (manual), session 1

## Severity scale

| Severity | Meaning |
|---|---|
| **Critical** | Direct financial loss or unauthorised movement of money |
| **High** | Incorrect money values or data that breaks financial integrity |
| **Medium** | Invalid data accepted; compliance or data-quality risk |
| **Low** | Minor issue, little direct impact |

## Summary

| ID | Title | Severity | Status | Test | Fix |
|---|---|---|---|---|---|
| BUG-01 | Account can be created with empty owner | Medium | Open | – | – |
| BUG-02 | Invalid currency code accepted | Medium | Open | – | – |
| BUG-03 | Empty currency accepted | Medium | Open | – | – |
| BUG-04 | Unknown fields silently ignored | Medium | Open | – | – |
| BUG-05 | Deposit currency ignored – JPY credited as EUR | Critical | Open | – | – |
| BUG-06 | No maximum deposit amount | Medium | Open | – | – |
| BUG-07 | Negative deposit reduces balance | Critical | Open | – | – |
| BUG-08 | Zero-amount deposit accepted | Low | Open | – | – |
| BUG-09 | Amounts with more than 2 decimal places accepted | High | Open | – | – |
| BUG-10 | Negative transfer pulls money from receiver | Critical | Open | – | – |
| BUG-11 | Transfer to the same account accepted | Medium | Open | – | – |
| BUG-12 | Transfer between different currencies | TBD | Not yet verified | – | – |

---

## BUG-01: Account can be created with empty owner

- **Endpoint:** `POST /accounts`
- **Severity:** Medium
- **Steps:**
  1. Send `POST /accounts` with body `{"owner": ""}`
- **Expected:** `422`, account not created
- **Actual:** `201`, account created with `"owner": ""`
- **Notes:** A missing `owner` correctly returns `422`; only the *empty* value is accepted. Also check whitespace-only (`"   "`).
- **Impact:** Accounts without a holder name – breaks KYC/compliance and statements.

## BUG-02: Invalid currency code accepted

- **Endpoint:** `POST /accounts`
- **Severity:** Medium
- **Steps:**
  1. Send `POST /accounts` with body `{"owner": "Alice", "currency": "JPN"}`
- **Expected:** `422` – only valid ISO 4217 codes (e.g. EUR, USD, GBP, JPY) accepted
- **Actual:** `201`, account created with currency `JPN`
- **Impact:** Accounts in non-existent currencies; downstream payment and FX failures.

## BUG-03: Empty currency accepted

- **Endpoint:** `POST /accounts`
- **Severity:** Medium
- **Steps:**
  1. Send `POST /accounts` with body `{"owner": "Alice", "currency": ""}`
- **Expected:** `422`
- **Actual:** `201`, account created with `"currency": ""`
- **Impact:** Account balance has no defined currency.

## BUG-04: Unknown fields silently ignored

- **Endpoint:** `POST /accounts` (and all POST endpoints)
- **Severity:** Medium
- **Steps:**
  1. Send `POST /accounts` with body `{"owner": "Alice", "balance": "1000.00"}`
- **Expected:** `422` – `balance` is not a client-settable field
- **Actual:** `201`, `balance` silently dropped, account created with `"0.00"`
- **Root cause:** Pydantic models ignore extra fields by default.
- **Impact:** Client believes a value was applied when it was not. Silent failures are high-risk in financial systems. Root cause of BUG-05.

## BUG-05: Deposit currency ignored – JPY credited as EUR

- **Endpoint:** `POST /accounts/{account_id}/deposit`
- **Severity:** Critical
- **Steps:**
  1. Create an account (currency `EUR`)
  2. Send deposit with body `{"amount": "100165.00", "currency": "JPY"}`
- **Expected:** `422` (currency mismatch) or conversion at the correct FX rate
- **Actual:** `200`, balance increased by €100,165 (≈ €600 worth of JPY sent)
- **Root cause:** Same as BUG-04 – `currency` is an unknown field and is dropped.
- **Impact:** Direct financial loss. Ranked separately from BUG-04 due to impact.

## BUG-06: No maximum deposit amount

- **Endpoint:** `POST /accounts/{account_id}/deposit`
- **Severity:** Medium
- **Steps:**
  1. Deposit very large amounts repeatedly
- **Expected:** Deposits above a defined limit rejected
- **Actual:** `200`; account balance reached €500,928,450
- **Impact:** No transaction limits – anti-money-laundering (AML) risk.

## BUG-07: Negative deposit reduces balance

- **Endpoint:** `POST /accounts/{account_id}/deposit`
- **Severity:** Critical
- **Steps:**
  1. Note account balance
  2. Send deposit with body `{"amount": "-500.00"}`
- **Expected:** `422` – deposit amount must be greater than 0
- **Actual:** `200`, balance reduced by €500 (`500928450.00` → `500927950.00`)
- **Impact:** Deposit acts as an unchecked withdrawal and bypasses the insufficient-funds check; balance could go negative.

## BUG-08: Zero-amount deposit accepted

- **Endpoint:** `POST /accounts/{account_id}/deposit`
- **Severity:** Low
- **Steps:**
  1. Send deposit with body `{"amount": "0"}`
- **Expected:** `422`
- **Actual:** `200`
- **Impact:** Meaningless transactions; zero/micro transactions are a known pattern for testing stolen accounts.

## BUG-09: Amounts with more than 2 decimal places accepted

- **Endpoint:** `POST /accounts/{account_id}/deposit` (likely also `/transfers`)
- **Severity:** High
- **Steps:**
  1. Send deposit with body `{"amount": "10.999"}`
- **Expected:** `422` – EUR supports max 2 decimal places
- **Actual:** `200`; balance later shown as `500927910.999`
- **Impact:** Sub-cent balances; fractional amounts can accumulate (“salami attack”). Note: decimal rules differ by currency (JPY has 0 decimals).

## BUG-10: Negative transfer pulls money from receiver

- **Endpoint:** `POST /transfers`
- **Severity:** Critical
- **Steps:**
  1. Alice has €70, Bob has a positive balance
  2. Send transfer from Alice to Bob with `"amount": "-50.00"`
- **Expected:** `422` – transfer amount must be greater than 0
- **Actual:** `200`; Alice `70.00` → `120.00`, Bob loses €50
- **Root cause:** Insufficient-funds check `if sender.balance < amount` assumes a positive amount (`70 < -50` is False), then `70 - (-50) = 120`.
- **Impact:** Anyone who knows an account ID can take money from it.

## BUG-11: Transfer to the same account accepted

- **Endpoint:** `POST /transfers`
- **Severity:** Medium
- **Steps:**
  1. Send transfer with `from_account_id` = `to_account_id`, `"amount": "100.00"`
- **Expected:** `422` / `400` – sender and receiver must differ
- **Actual:** `200`, balance unchanged
- **Impact:** Fake transactions; can inflate transaction volumes or exploit future fees/rewards.

## BUG-12: Transfer between different currencies

- **Endpoint:** `POST /transfers`
- **Severity:** TBD
- **Status:** Not yet verified
- **Steps:**
  1. Create a `EUR` account (funded) and a `JPY` account
  2. Transfer `10.00` from EUR account to JPY account
  3. Check receiver balance
- **Expected:** `422` (currency mismatch) or conversion at the correct FX rate
- **Actual:** _to be filled in after testing_