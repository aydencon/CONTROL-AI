import pandas as pd
import numpy as np
from datetime import date, timedelta


TODAY = date(2026, 6, 17)


def get_current_position(gl_balances: pd.DataFrame) -> dict:
    def bal(acct):
        row = gl_balances[gl_balances["account_number"].astype(str) == str(acct)]
        return float(row["current_balance"].iloc[0]) if len(row) else 0.0

    cash_operating = bal("1010")
    cash_payroll   = bal("1020")
    floorplan_pay  = abs(bal("2310"))
    total_cash     = cash_operating + cash_payroll

    return {
        "cash_operating": cash_operating,
        "cash_payroll":   cash_payroll,
        "total_cash":     total_cash,
        "floorplan_payable": floorplan_pay,
        "net_position":   total_cash - floorplan_pay,
    }


def get_floorplan_summary(df_floorplan: pd.DataFrame) -> dict:
    total_floor   = df_floorplan["floor_amount"].sum()
    total_interest = df_floorplan["interest_accrued"].sum()
    curtailment   = df_floorplan[df_floorplan["curtailment_due"] == True]
    return {
        "total_units":        len(df_floorplan),
        "total_floor_amount": round(total_floor, 2),
        "total_interest":     round(total_interest, 2),
        "total_outstanding":  round(total_floor + total_interest, 2),
        "curtailment_count":  len(curtailment),
        "curtailment_amount": round(curtailment["floor_amount"].sum(), 2),
    }


def get_curtailments_due(df_floorplan: pd.DataFrame) -> pd.DataFrame:
    due = df_floorplan[df_floorplan["curtailment_due"] == True].copy()
    return due.sort_values("days_over_curtailment", ascending=False)


def forecast_30_days(
    current_balance: float,
    df_ap: pd.DataFrame,
    df_deals: pd.DataFrame,
    df_floorplan: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    running = current_balance

    unpaid_ap = df_ap[df_ap["status"] == "Unpaid"].copy()
    unpaid_ap["due_date"] = pd.to_datetime(unpaid_ap["due_date"])

    # Unfunded deals expected to clear
    pending_funding = df_deals[
        (df_deals["status"] == "Posted") &
        (df_deals["funded_amount"] > 0) &
        (df_deals["funded_date"].isna() | (pd.to_datetime(df_deals["funded_date"]) >= pd.Timestamp(TODAY)))
    ].copy()

    for i in range(31):
        day = TODAY + timedelta(days=i)
        day_ts = pd.Timestamp(day)

        # Expected receipts: deal fundings due on this day
        fundings = pending_funding[
            pd.to_datetime(pending_funding["funded_date"]).dt.date == day
        ]["funded_amount"].sum() if len(pending_funding) else 0.0

        # Expected disbursements: AP due on this day
        ap_due = unpaid_ap[unpaid_ap["due_date"].dt.date == day]["amount"].sum()

        # Floorplan payments: curtailments + estimate weekly floor payments
        fp_payment = 0.0
        if day.weekday() == 4:  # Fridays — floorplan usually sweeps weekly
            fp_payment = df_floorplan[
                (df_floorplan["curtailment_due"] == True) &
                (df_floorplan["days_over_curtailment"] > 0)
            ]["floor_amount"].sum() * 0.10  # 10% curtailment payment estimate

        # Payroll: bi-weekly Fridays
        payroll = 84_200.0 if (day.weekday() == 4 and i % 14 in [0, 14]) else 0.0

        receipts      = round(fundings, 2)
        disbursements = round(ap_due + fp_payment + payroll, 2)
        net           = round(receipts - disbursements, 2)
        running       = round(running + net, 2)

        rows.append({
            "date":           day,
            "receipts":       receipts,
            "disbursements":  disbursements,
            "net":            net,
            "running_balance": running,
        })

    return pd.DataFrame(rows)


def get_ap_due_soon(df_ap: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    unpaid = df_ap[df_ap["status"] == "Unpaid"].copy()
    unpaid["due_date"] = pd.to_datetime(unpaid["due_date"])
    cutoff = pd.Timestamp(TODAY + timedelta(days=days))
    today_ts = pd.Timestamp(TODAY)
    due = unpaid[unpaid["due_date"] <= cutoff].copy()
    due["days_until_due"] = (due["due_date"] - today_ts).dt.days
    return due.sort_values("due_date")
