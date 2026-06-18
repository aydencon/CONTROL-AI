import pandas as pd
import numpy as np


def match_bank_to_gl(
    df_bank: pd.DataFrame, df_gl: pd.DataFrame, date_tolerance: int = 3
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns (matched, bank_only, gl_only).
    Matches on amount + date within tolerance.
    """
    bank = df_bank.copy()
    gl   = df_gl.copy()

    bank["_amount"] = bank["amount"].apply(_num)
    gl["_net"] = gl["debit"].apply(_num) - gl["credit"].apply(_num)

    bank["_date"] = pd.to_datetime(bank["date"])
    gl["_date"]   = pd.to_datetime(gl["date"])

    bank_used = [False] * len(bank)
    gl_used   = [False] * len(gl)
    matched_rows = []

    for bi, brow in bank.iterrows():
        for gi, grow in gl.iterrows():
            if gl_used[gi]:
                continue
            if abs(brow["_amount"] - grow["_net"]) > 0.01:
                continue
            date_diff = abs((brow["_date"] - grow["_date"]).days)
            if date_diff > date_tolerance:
                continue
            matched_rows.append({
                "bank_date":        brow["date"],
                "bank_description": brow["description"],
                "bank_amount":      brow["amount"],
                "bank_ref":         brow.get("reference", ""),
                "gl_date":          grow["date"],
                "gl_description":   grow["description"],
                "gl_debit":         grow.get("debit", 0),
                "gl_credit":        grow.get("credit", 0),
                "gl_ref":           grow.get("reference", ""),
            })
            bank_used[bi] = True
            gl_used[gi]   = True
            break

    bank_only = bank[[not u for u in bank_used]].drop(columns=["_amount", "_date"])
    gl_only   = gl[[not u for u in gl_used]].drop(columns=["_net", "_date"])
    matched   = pd.DataFrame(matched_rows)
    return matched, bank_only, gl_only


def get_rec_summary(matched, bank_only, gl_only, df_bank, df_gl) -> dict:
    bank_total = df_bank["amount"].sum()
    gl_total   = (df_gl["debit"].apply(_num) - df_gl["credit"].apply(_num)).sum()
    return {
        "matched_count":      len(matched),
        "bank_only_count":    len(bank_only),
        "gl_only_count":      len(gl_only),
        "bank_total":         round(bank_total, 2),
        "gl_total":           round(gl_total, 2),
        "difference":         round(bank_total - gl_total, 2),
    }


def _num(v) -> float:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0.0
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except Exception:
        return 0.0
