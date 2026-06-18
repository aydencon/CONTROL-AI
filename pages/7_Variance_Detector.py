import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from data_loader import load
from modules import schedule_rec, cash_forecast, ap_manager, variance_detector
from config import DEALERSHIP_NAME

st.set_page_config(page_title="Variance Detector | " + DEALERSHIP_NAME, layout="wide")
st.title("Variance & Anomaly Detector")
st.caption("Automated scan across all modules. Surfaces mistakes, inconsistencies, and items requiring action.")

@st.cache_data(ttl=60)
def get_data():
    return {
        "deals":     load("deals"),
        "floorplan": load("floorplan"),
        "ap":        load("ap_invoices"),
        "schedules": load("schedules"),
        "detail":    load("schedule_detail"),
        "gl":        load("gl_balances"),
    }

data = get_data()

rec      = schedule_rec.reconcile(data["schedules"], data["detail"])
position = cash_forecast.get_current_position(data["gl"])
dupes    = ap_manager.detect_duplicates(data["ap"])
alerts   = variance_detector.get_all_alerts(
    rec, data["ap"], dupes, position, data["floorplan"], data["deals"]
)

# ── Alert Counts ───────────────────────────────────────────────────────────────
high   = alerts[alerts["severity"] == "High"]   if not alerts.empty else pd.DataFrame()
medium = alerts[alerts["severity"] == "Medium"] if not alerts.empty else pd.DataFrame()
low    = alerts[alerts["severity"] == "Low"]    if not alerts.empty else pd.DataFrame()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Alerts",   len(alerts))
c2.metric("High",   len(high),   delta_color="inverse" if len(high)   else "normal", delta="Action Required" if len(high) else "None")
c3.metric("Medium", len(medium), delta_color="off")
c4.metric("Low",    len(low),    delta_color="off")

st.divider()

# ── Alert Feed ─────────────────────────────────────────────────────────────────
if alerts.empty:
    st.success("No issues detected across all modules. Everything looks clean.")
else:
    tab_all, tab_high, tab_by_cat = st.tabs(["All Alerts", "High Priority", "By Category"])

    with tab_all:
        for _, row in alerts.iterrows():
            icon = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(row["severity"],"⚪")
            with st.expander(f"{icon} **[{row['severity']}] [{row['category']}]** — {row['title']}"):
                st.write(row["detail"])
                if pd.notna(row.get("amount")) and row["amount"]:
                    st.write(f"**Amount:** ${float(row['amount']):,.2f}")

    with tab_high:
        if high.empty:
            st.success("No high-priority alerts.")
        else:
            for _, row in high.iterrows():
                with st.expander(f"🔴 **[{row['category']}]** {row['title']}"):
                    st.write(row["detail"])
                    if pd.notna(row.get("amount")) and row["amount"]:
                        st.write(f"**Amount:** ${float(row['amount']):,.2f}")

    with tab_by_cat:
        categories = alerts["category"].unique().tolist()
        for cat in categories:
            cat_alerts = alerts[alerts["category"] == cat]
            st.subheader(f"{cat} ({len(cat_alerts)})")
            for _, row in cat_alerts.iterrows():
                icon = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(row["severity"],"⚪")
                st.write(f"{icon} **{row['title']}** — {row['detail']}")
            st.write("")

st.divider()

# ── Detailed Sections ──────────────────────────────────────────────────────────
tab_sched, tab_ap_d, tab_fp_d, tab_deals_d = st.tabs([
    "Schedule Detail", "AP Detail", "Floorplan Detail", "Deals Detail"
])

with tab_sched:
    st.subheader("Schedule Reconciliation Status")
    st.dataframe(
        rec[["schedule_name","gl_balance","detail_sum","variance","item_count",
             "aged_30","aged_60","aged_90","status"]],
        use_container_width=True, hide_index=True,
    )

    aged = schedule_rec.get_aged_items(data["detail"])
    if not aged.empty:
        st.subheader("Aged Schedule Items")
        st.dataframe(
            aged[["schedule_name","item_date","description","reference","amount","days_open","severity"]],
            use_container_width=True, hide_index=True,
        )

with tab_ap_d:
    st.subheader("AP — Overdue Invoices")
    overdue = ap_manager.get_overdue(data["ap"])
    if overdue.empty:
        st.success("No overdue AP.")
    else:
        st.dataframe(
            overdue[["vendor","invoice_number","invoice_date","due_date","amount","days_overdue"]],
            use_container_width=True, hide_index=True,
        )

    st.subheader("AP — Duplicate Flags")
    if dupes.empty:
        st.success("No duplicates detected.")
    else:
        st.dataframe(dupes, use_container_width=True, hide_index=True)

with tab_fp_d:
    st.subheader("Floorplan — Curtailments Due")
    curt = data["floorplan"][data["floorplan"]["curtailment_due"] == True]
    if curt.empty:
        st.success("No curtailments due.")
    else:
        st.dataframe(
            curt[["stock_number","year","make","model","floored_date","days_floored",
                  "floor_amount","days_over_curtailment"]],
            use_container_width=True, hide_index=True,
        )
    st.caption(f"New vehicle rate: 8.25% | Used vehicle rate: 9.25% | Curtailment threshold: 180 days")

with tab_deals_d:
    st.subheader("Deals — Unposted")
    unposted = data["deals"][data["deals"]["status"] == "Unposted"]
    if unposted.empty:
        st.success("All deals posted.")
    else:
        st.dataframe(
            unposted[["deal_number","date","customer","salesperson","department",
                      "make","model","total_gross","status"]],
            use_container_width=True, hide_index=True,
        )

    st.subheader("Deals — Funded But CIT Not Cleared (7+ days)")
    funded = data["deals"][
        (data["deals"]["funded_amount"] > 0) &
        (data["deals"]["funded_date"].notna()) &
        (data["deals"]["status"] == "Posted")
    ].copy()
    funded["days_since_funded"] = (
        pd.Timestamp("2026-06-17") - pd.to_datetime(funded["funded_date"])
    ).dt.days
    stale = funded[funded["days_since_funded"] > 7]
    if stale.empty:
        st.success("No stale CIT items.")
    else:
        st.dataframe(
            stale[["deal_number","date","customer","finance_company","funded_amount",
                   "funded_date","days_since_funded"]],
            use_container_width=True, hide_index=True,
        )

# ── Alert Breakdown Chart ──────────────────────────────────────────────────────
if not alerts.empty:
    st.divider()
    st.subheader("Alert Breakdown")
    breakdown = alerts.groupby(["category","severity"]).size().reset_index(name="count")
    fig = px.bar(breakdown, x="category", y="count", color="severity",
                 color_discrete_map={"High":"#c00000","Medium":"#ffc000","Low":"#70ad47"},
                 title="Alerts by Category and Severity",
                 labels={"count":"Number of Alerts"})
    st.plotly_chart(fig, use_container_width=True)
