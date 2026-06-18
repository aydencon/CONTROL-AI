import pandas as pd
from datetime import date
from config import SCHEDULE_AGE_WARNING, SCHEDULE_AGE_CRITICAL, CASH_LOW_THRESHOLD

TODAY = date(2026, 6, 17)


def _alert(severity: str, category: str, title: str, detail: str, amount: float = None) -> dict:
    return {
        "severity": severity,
        "category": category,
        "title":    title,
        "detail":   detail,
        "amount":   amount,
    }


def detect_schedule_issues(df_rec: pd.DataFrame) -> list[dict]:
    alerts = []
    for _, row in df_rec.iterrows():
        if abs(row["variance"]) > 0.01:
            alerts.append(_alert(
                "High", "Schedule",
                f"Variance on {row['schedule_name']}",
                f"GL balance ${row['gl_balance']:,.2f} vs detail sum ${row['detail_sum']:,.2f}",
                amount=row["variance"],
            ))
        if row["aged_90"] > 0:
            alerts.append(_alert(
                "High", "Schedule",
                f"{row['aged_90']} item(s) over 90 days — {row['schedule_name']}",
                f"Items aged 90+ days require immediate follow-up",
            ))
        elif row["aged_60"] > 0:
            alerts.append(_alert(
                "Medium", "Schedule",
                f"{row['aged_60']} item(s) over 60 days — {row['schedule_name']}",
                f"Items approaching 90-day threshold",
            ))
        elif row["aged_30"] > 0:
            alerts.append(_alert(
                "Low", "Schedule",
                f"{row['aged_30']} item(s) over 30 days — {row['schedule_name']}",
                f"Monitor — items approaching 60-day threshold",
            ))
    return alerts


def detect_ap_issues(df_ap: pd.DataFrame, df_dupes: pd.DataFrame) -> list[dict]:
    alerts = []
    overdue = df_ap[(df_ap["status"] == "Unpaid") & (df_ap["days_overdue"] > 30)]
    if len(overdue):
        total = overdue["amount"].sum()
        alerts.append(_alert(
            "High", "AP",
            f"{len(overdue)} invoice(s) over 30 days past due",
            f"Vendors: {', '.join(overdue['vendor'].unique()[:3])}",
            amount=total,
        ))

    warn = df_ap[(df_ap["status"] == "Unpaid") & (df_ap["days_overdue"].between(1, 30))]
    if len(warn):
        alerts.append(_alert(
            "Medium", "AP",
            f"{len(warn)} invoice(s) past due (1–30 days)",
            f"Total: ${warn['amount'].sum():,.2f}",
            amount=warn["amount"].sum(),
        ))

    if len(df_dupes):
        for _, dup in df_dupes.iterrows():
            alerts.append(_alert(
                "High", "AP",
                f"Possible duplicate invoice — {dup['vendor']}",
                f"{dup['inv_num_a']} and {dup['inv_num_b']} — same amount ${dup['amount']:,.2f}, {dup['days_apart']} days apart",
                amount=dup["amount"],
            ))
    return alerts


def detect_cash_issues(position: dict) -> list[dict]:
    alerts = []
    if position["total_cash"] < CASH_LOW_THRESHOLD:
        alerts.append(_alert(
            "High", "Cash",
            f"Cash below threshold",
            f"Total cash ${position['total_cash']:,.2f} is below ${CASH_LOW_THRESHOLD:,.0f} minimum",
            amount=position["total_cash"],
        ))
    return alerts


def detect_floorplan_issues(df_floorplan: pd.DataFrame) -> list[dict]:
    alerts = []
    due = df_floorplan[df_floorplan["curtailment_due"] == True]
    if len(due):
        alerts.append(_alert(
            "High", "Floorplan",
            f"{len(due)} vehicle(s) require curtailment payment",
            f"Units: {', '.join(due['stock_number'].tolist()[:5])}{'...' if len(due) > 5 else ''}",
            amount=due["floor_amount"].sum(),
        ))
    over_210 = df_floorplan[df_floorplan["days_floored"] > 210]
    if len(over_210):
        alerts.append(_alert(
            "High", "Floorplan",
            f"{len(over_210)} vehicle(s) over 210 days — risk of forced paydown",
            f"Units: {', '.join(over_210['stock_number'].tolist())}",
        ))
    return alerts


def detect_deal_issues(df_deals: pd.DataFrame) -> list[dict]:
    alerts = []
    unposted = df_deals[df_deals["status"] == "Unposted"]
    if len(unposted):
        alerts.append(_alert(
            "Medium", "Deals",
            f"{len(unposted)} unposted deal(s)",
            f"Deals not yet posted to GL: {', '.join(unposted['deal_number'].tolist())}",
        ))

    # Funded but not deposited for more than 5 days
    funded_not_cleared = df_deals[
        (df_deals["funded_amount"] > 0) &
        (df_deals["funded_date"].notna()) &
        (df_deals["status"] == "Posted")
    ].copy()
    funded_not_cleared["days_since_funded"] = (
        pd.Timestamp(TODAY) - pd.to_datetime(funded_not_cleared["funded_date"])
    ).dt.days
    stale_cit = funded_not_cleared[funded_not_cleared["days_since_funded"] > 7]
    if len(stale_cit):
        alerts.append(_alert(
            "Medium", "Deals",
            f"{len(stale_cit)} deal(s) funded 7+ days ago — verify CIT cleared",
            f"Deals: {', '.join(stale_cit['deal_number'].tolist()[:5])}",
        ))
    return alerts


def get_all_alerts(
    df_rec: pd.DataFrame,
    df_ap: pd.DataFrame,
    df_dupes: pd.DataFrame,
    position: dict,
    df_floorplan: pd.DataFrame,
    df_deals: pd.DataFrame,
) -> pd.DataFrame:
    alerts = (
        detect_schedule_issues(df_rec) +
        detect_ap_issues(df_ap, df_dupes) +
        detect_cash_issues(position) +
        detect_floorplan_issues(df_floorplan) +
        detect_deal_issues(df_deals)
    )
    if not alerts:
        return pd.DataFrame()
    df = pd.DataFrame(alerts)
    order = {"High": 0, "Medium": 1, "Low": 2}
    df["_sort"] = df["severity"].map(order)
    return df.sort_values(["_sort", "category"]).drop(columns=["_sort"]).reset_index(drop=True)
