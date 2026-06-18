import pandas as pd
from datetime import date


def reconcile(df_schedules: pd.DataFrame, df_detail: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per schedule with GL balance, detail sum, variance, age buckets, and status.
    """
    summary = (
        df_detail.groupby("schedule_name")
        .agg(
            detail_sum=("amount", "sum"),
            item_count=("amount", "count"),
            aged_30=("days_open", lambda x: (x >= 30).sum()),
            aged_60=("days_open", lambda x: (x >= 60).sum()),
            aged_90=("days_open", lambda x: (x >= 90).sum()),
            oldest_item=("days_open", "max"),
        )
        .reset_index()
    )

    merged = df_schedules.merge(summary, on="schedule_name", how="left")
    merged["detail_sum"]  = merged["detail_sum"].fillna(0)
    merged["item_count"]  = merged["item_count"].fillna(0).astype(int)
    merged["aged_30"]     = merged["aged_30"].fillna(0).astype(int)
    merged["aged_60"]     = merged["aged_60"].fillna(0).astype(int)
    merged["aged_90"]     = merged["aged_90"].fillna(0).astype(int)
    merged["oldest_item"] = merged["oldest_item"].fillna(0).astype(int)

    merged["variance"] = (merged["gl_balance"] - merged["detail_sum"]).round(2)

    def _status(row):
        if abs(row["variance"]) > 0.01:
            return "Variance"
        if row["aged_60"] > 0:
            return "Aged Items"
        if row["aged_30"] > 0:
            return "Warning"
        return "Reconciled"

    merged["status"] = merged.apply(_status, axis=1)
    return merged


def get_aged_items(df_detail: pd.DataFrame, warning: int = 30, critical: int = 60) -> pd.DataFrame:
    aged = df_detail[df_detail["days_open"] >= warning].copy()
    aged["severity"] = aged["days_open"].apply(
        lambda d: "Critical" if d >= critical else "Warning"
    )
    return aged.sort_values("days_open", ascending=False)


def get_schedule_items(df_detail: pd.DataFrame, schedule_name: str) -> pd.DataFrame:
    return df_detail[df_detail["schedule_name"] == schedule_name].copy().sort_values(
        "days_open", ascending=False
    )
