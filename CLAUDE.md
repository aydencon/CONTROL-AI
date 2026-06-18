# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# From the project root
python -m streamlit run app.py

# Or double-click start.bat (installs deps + generates fake data first)
```

App runs on **http://localhost:8501**.

To reset all fake data to a clean state:
```bash
python fake_data_generator.py
```

## Architecture

This is a Streamlit multi-page app. The entry point is `app.py` (home dashboard). Pages live in `pages/` and are auto-discovered by Streamlit in filename order.

**Data flow:**
```
fake_data_generator.py  →  data/fake/*.csv
                                  ↓
                           data_loader.py          ← single load() entry point
                                  ↓
                           modules/*.py            ← pure pandas functions, no Streamlit
                                  ↓
                           app.py + pages/*.py     ← Streamlit UI only
```

**Key design rule:** Modules take DataFrames as input and return DataFrames or dicts. They have no Streamlit imports and no side effects. Pages handle all UI; modules handle all logic.

## Data source switching

`DATA_SOURCE` in `.env` controls where data comes from:
- `fake` — reads CSVs from `data/fake/` (auto-generated if missing)
- `pbs` — not yet implemented; raises `NotImplementedError` in `data_loader.py`

To add PBS live data, implement the `pbs` branch in `data_loader.load()`. The module and page code requires no changes.

## Modules

| Module | Key functions |
|---|---|
| `schedule_rec` | `reconcile(df_schedules, df_detail)` — returns variance + age buckets per schedule |
| `cash_forecast` | `get_current_position(df_gl)`, `forecast_30_days(...)` — 30-day daily cash projection |
| `month_end_report` | `get_department_summary(df_deals, start, end)`, `get_monthly_trend(df_deals)` |
| `statement_rec` | `match_bank_to_gl(df_bank, df_gl)` — returns (matched, bank_only, gl_only) |
| `ap_manager` | `get_aging_summary`, `detect_duplicates`, `get_overdue` |
| `email_automation` | `build_ap_reminder`, `build_ar_aging_email`, `send_email` |
| `variance_detector` | `get_all_alerts(rec, ap, dupes, position, floorplan, deals)` — aggregates all issues |

## Config

All thresholds and constants live in `config.py`. Key ones:
- `FLOORPLAN_CURTAILMENT_DAYS = 180` — vehicles older than this flag as curtailment due
- `SCHEDULE_AGE_WARNING = 30`, `SCHEDULE_AGE_CRITICAL = 60` — schedule item age thresholds
- `CASH_LOW_THRESHOLD = 50_000` — triggers cash alert
- `VENDORS` dict — maps vendor name → GL account number (used by AP Manager add-invoice form)

## Known hardcoded dates

`TODAY = date(2026, 6, 17)` is hardcoded in several modules (`cash_forecast.py`, `ap_manager.py`, `variance_detector.py`) and in `fake_data_generator.py`. When connecting to live PBS data, replace these with `date.today()`.

## Fake data schema

The 9 CSV tables and their key columns:

| Table | Key columns |
|---|---|
| `deals` | deal_number, date, department, front_gross, back_gross, funded_amount, funded_date, posted, status |
| `floorplan` | stock_number, floor_amount, days_floored, curtailment_due, days_over_curtailment |
| `ap_invoices` | vendor, invoice_number, invoice_date, due_date, amount, status, days_overdue |
| `ar_aging` | customer, contact_email, balance, days_outstanding, aging_bucket |
| `schedules` | schedule_name, gl_account, gl_balance |
| `schedule_detail` | schedule_name, gl_account, item_date, description, reference, amount, days_open |
| `gl_balances` | account_number, current_balance, ytd_balance, prior_ytd_balance, budget_ytd |
| `bank_transactions` | date, description, amount, reference, matched_to_gl |
| `gl_cash_transactions` | date, description, debit, credit, reference |

`gl_balances.account_number` is read by pandas as an integer — always cast with `.astype(str)` before string comparison (see `cash_forecast.get_current_position`).
