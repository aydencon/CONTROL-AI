"""
Single entry point for all data access.
Swap DATA_SOURCE in .env from 'fake' to 'pbs' when ready for live data.
"""

import pandas as pd
from pathlib import Path
from config import FAKE_DATA_DIR, DATA_SOURCE
import subprocess, sys, os

_TABLES = {
    "deals":               "deals.csv",
    "floorplan":           "floorplan.csv",
    "ap_invoices":         "ap_invoices.csv",
    "ar_aging":            "ar_aging.csv",
    "schedules":           "schedules.csv",
    "schedule_detail":     "schedule_detail.csv",
    "gl_balances":         "gl_balances.csv",
    "bank_transactions":   "bank_transactions.csv",
    "gl_cash_transactions":"gl_cash_transactions.csv",
}

_DATE_COLS = {
    "deals":               ["date", "funded_date"],
    "floorplan":           ["floored_date"],
    "ap_invoices":         ["invoice_date", "due_date", "paid_date"],
    "ar_aging":            ["invoice_date"],
    "schedule_detail":     ["item_date"],
    "bank_transactions":   ["date"],
    "gl_cash_transactions":["date"],
}


def _ensure_data():
    """Auto-generate fake data if the files don't exist yet."""
    if not (FAKE_DATA_DIR / "deals.csv").exists():
        script = Path(__file__).parent / "fake_data_generator.py"
        subprocess.run([sys.executable, str(script)], check=True)


def load(table: str) -> pd.DataFrame:
    if DATA_SOURCE == "fake":
        _ensure_data()
        path = FAKE_DATA_DIR / _TABLES[table]
        df = pd.read_csv(path)
        for col in _DATE_COLS.get(table, []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    else:
        raise NotImplementedError("PBS live connection not yet implemented. Set DATA_SOURCE=fake in .env")


def reload(table: str) -> pd.DataFrame:
    """Force a fresh read (bypasses any external caching)."""
    return load(table)
