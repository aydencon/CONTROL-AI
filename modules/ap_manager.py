import pandas as pd
from datetime import date, timedelta

TODAY = date(2026, 6, 17)


def get_aging_summary(df_ap: pd.DataFrame) -> pd.DataFrame:
    unpaid = df_ap[df_ap["status"] == "Unpaid"].copy()
    unpaid["due_date"] = pd.to_datetime(unpaid["due_date"])
    today_ts = pd.Timestamp(TODAY)

    def bucket(row):
        overdue = (today_ts - row["due_date"]).days
        if overdue <= 0:
            return "Current"
        elif overdue <= 30:
            return "1-30 Days"
        elif overdue <= 60:
            return "31-60 Days"
        else:
            return "60+ Days"

    unpaid["aging_bucket"] = unpaid.apply(bucket, axis=1)

    bucket_order = ["Current", "1-30 Days", "31-60 Days", "60+ Days"]
    summary = (
        unpaid.groupby("aging_bucket")
        .agg(invoices=("invoice_id", "count"), total=("amount", "sum"))
        .reindex(bucket_order)
        .fillna(0)
        .reset_index()
    )
    summary["invoices"] = summary["invoices"].astype(int)
    return summary


def detect_duplicates(df_ap: pd.DataFrame, days_window: int = 45) -> pd.DataFrame:
    unpaid = df_ap[df_ap["status"] != "Paid"].copy()
    unpaid["invoice_date"] = pd.to_datetime(unpaid["invoice_date"])
    dupes = []

    for i, row_a in unpaid.iterrows():
        for j, row_b in unpaid.iterrows():
            if j <= i:
                continue
            if row_a["vendor"] != row_b["vendor"]:
                continue
            if abs(row_a["amount"] - row_b["amount"]) > 0.01:
                continue
            date_diff = abs((row_a["invoice_date"] - row_b["invoice_date"]).days)
            if date_diff > days_window:
                continue
            dupes.append({
                "invoice_a":   row_a["invoice_id"],
                "invoice_b":   row_b["invoice_id"],
                "vendor":      row_a["vendor"],
                "amount":      row_a["amount"],
                "date_a":      row_a["invoice_date"].date(),
                "date_b":      row_b["invoice_date"].date(),
                "days_apart":  date_diff,
                "inv_num_a":   row_a["invoice_number"],
                "inv_num_b":   row_b["invoice_number"],
            })

    return pd.DataFrame(dupes)


def get_due_soon(df_ap: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    unpaid = df_ap[df_ap["status"] == "Unpaid"].copy()
    unpaid["due_date"] = pd.to_datetime(unpaid["due_date"])
    today_ts = pd.Timestamp(TODAY)
    cutoff   = pd.Timestamp(TODAY + timedelta(days=days))
    due = unpaid[unpaid["due_date"] <= cutoff].copy()
    due["days_until_due"] = (due["due_date"] - today_ts).dt.days
    return due.sort_values("due_date")


def get_overdue(df_ap: pd.DataFrame) -> pd.DataFrame:
    unpaid = df_ap[df_ap["status"] == "Unpaid"].copy()
    unpaid["due_date"] = pd.to_datetime(unpaid["due_date"])
    today_ts = pd.Timestamp(TODAY)
    overdue = unpaid[unpaid["due_date"] < today_ts].copy()
    overdue["days_overdue"] = (today_ts - overdue["due_date"]).dt.days
    return overdue.sort_values("days_overdue", ascending=False)
