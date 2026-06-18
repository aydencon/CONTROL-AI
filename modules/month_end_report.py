import pandas as pd
from datetime import date


def get_department_summary(df_deals: pd.DataFrame, period_start: date, period_end: date) -> pd.DataFrame:
    mask = (
        (pd.to_datetime(df_deals["date"]).dt.date >= period_start) &
        (pd.to_datetime(df_deals["date"]).dt.date <= period_end) &
        (df_deals["posted"] == True)
    )
    period = df_deals[mask].copy()

    if period.empty:
        return pd.DataFrame()

    summary = (
        period.groupby("department")
        .agg(
            units=("deal_number", "count"),
            front_gross=("front_gross", "sum"),
            back_gross=("back_gross", "sum"),
            total_gross=("total_gross", "sum"),
        )
        .reset_index()
    )
    summary["avg_pvr"] = (summary["total_gross"] / summary["units"]).round(0).astype(int)
    summary = summary.sort_values("total_gross", ascending=False)
    totals = pd.DataFrame([{
        "department":  "TOTAL",
        "units":       summary["units"].sum(),
        "front_gross": summary["front_gross"].sum(),
        "back_gross":  summary["back_gross"].sum(),
        "total_gross": summary["total_gross"].sum(),
        "avg_pvr":     int(summary["total_gross"].sum() / summary["units"].sum()) if summary["units"].sum() else 0,
    }])
    return pd.concat([summary, totals], ignore_index=True)


def get_monthly_trend(df_deals: pd.DataFrame) -> pd.DataFrame:
    posted = df_deals[df_deals["posted"] == True].copy()
    posted["month"] = pd.to_datetime(posted["date"]).dt.to_period("M")
    trend = (
        posted.groupby("month")
        .agg(
            units=("deal_number", "count"),
            total_gross=("total_gross", "sum"),
            front_gross=("front_gross", "sum"),
            back_gross=("back_gross", "sum"),
        )
        .reset_index()
    )
    trend["month_label"] = trend["month"].dt.strftime("%b %Y")
    trend["avg_pvr"] = (trend["total_gross"] / trend["units"]).round(0).astype(int)
    return trend.sort_values("month")


def get_salesperson_summary(df_deals: pd.DataFrame, period_start: date, period_end: date) -> pd.DataFrame:
    mask = (
        (pd.to_datetime(df_deals["date"]).dt.date >= period_start) &
        (pd.to_datetime(df_deals["date"]).dt.date <= period_end) &
        (df_deals["posted"] == True)
    )
    period = df_deals[mask]
    if period.empty:
        return pd.DataFrame()
    return (
        period.groupby("salesperson")
        .agg(
            units=("deal_number", "count"),
            total_gross=("total_gross", "sum"),
            avg_pvr=("total_gross", "mean"),
        )
        .reset_index()
        .sort_values("total_gross", ascending=False)
    )


def get_ytd_gl_summary(df_gl: pd.DataFrame) -> pd.DataFrame:
    income_rows = df_gl[df_gl["account_number"].astype(str).str.startswith(("4", "5"))].copy()
    income_rows["variance_to_budget"] = income_rows["ytd_balance"] - income_rows["budget_ytd"]
    income_rows["pct_of_budget"] = (
        income_rows["ytd_balance"] / income_rows["budget_ytd"].replace(0, pd.NA) * 100
    ).round(1)
    return income_rows[["account_number", "account_name", "department",
                         "ytd_balance", "prior_ytd_balance", "budget_ytd",
                         "variance_to_budget", "pct_of_budget"]]


def get_finance_company_mix(df_deals: pd.DataFrame, period_start: date, period_end: date) -> pd.DataFrame:
    mask = (
        (pd.to_datetime(df_deals["date"]).dt.date >= period_start) &
        (pd.to_datetime(df_deals["date"]).dt.date <= period_end) &
        (df_deals["posted"] == True)
    )
    period = df_deals[mask]
    if period.empty:
        return pd.DataFrame()
    return (
        period.groupby("finance_company")
        .agg(deals=("deal_number", "count"), funded=("funded_amount", "sum"))
        .reset_index()
        .sort_values("deals", ascending=False)
    )
