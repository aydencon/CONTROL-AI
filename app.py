import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from config import DEALERSHIP_NAME
from data_loader import load
from modules import schedule_rec, cash_forecast, ap_manager, variance_detector
from datetime import date

st.set_page_config(
    page_title=f"{DEALERSHIP_NAME} — Controller Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)

TODAY = date(2026, 6, 17)

st.title(f"{DEALERSHIP_NAME} — Controller Dashboard")
st.caption(f"Today: {TODAY.strftime('%B %d, %Y')}")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_all():
    return {
        "deals":        load("deals"),
        "floorplan":    load("floorplan"),
        "ap":           load("ap_invoices"),
        "ar":           load("ar_aging"),
        "schedules":    load("schedules"),
        "detail":       load("schedule_detail"),
        "gl":           load("gl_balances"),
        "bank":         load("bank_transactions"),
        "gl_cash":      load("gl_cash_transactions"),
    }

data = load_all()

# ── KPI Row ───────────────────────────────────────────────────────────────────
position   = cash_forecast.get_current_position(data["gl"])
fp_summary = cash_forecast.get_floorplan_summary(data["floorplan"])
rec        = schedule_rec.reconcile(data["schedules"], data["detail"])
dupes      = ap_manager.detect_duplicates(data["ap"])
alerts_df  = variance_detector.get_all_alerts(
    rec, data["ap"], dupes, position, data["floorplan"], data["deals"]
)

mtd_deals  = data["deals"][
    (data["deals"]["posted"] == True) &
    (data["deals"]["date"].dt.month == TODAY.month) &
    (data["deals"]["date"].dt.year  == TODAY.year)
]
mtd_units  = len(mtd_deals)
mtd_gross  = mtd_deals["total_gross"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Operating Cash",    f"${position['cash_operating']:,.0f}")
c2.metric("Floorplan Balance", f"${fp_summary['total_floor_amount']:,.0f}",
          delta=f"{fp_summary['total_units']} units")
c3.metric("Open AP",           f"${data['ap'][data['ap']['status']=='Unpaid']['amount'].sum():,.0f}")
c4.metric("MTD Units",         f"{mtd_units}",
          delta=f"${mtd_gross:,.0f} gross")
c5.metric("Active Alerts",     f"{len(alerts_df)}",
          delta=f"{len(alerts_df[alerts_df['severity']=='High'])} high" if len(alerts_df) else None,
          delta_color="inverse")

st.divider()

# ── Alerts ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Active Alerts")
    if alerts_df.empty:
        st.success("No issues detected — everything looks clean.")
    else:
        for _, row in alerts_df.iterrows():
            icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(row["severity"], "⚪")
            with st.expander(f"{icon} [{row['severity']}] {row['category']} — {row['title']}"):
                st.write(row["detail"])
                if row.get("amount"):
                    st.write(f"**Amount:** ${row['amount']:,.2f}")

with col_right:
    st.subheader("Schedule Status")
    for _, row in rec.iterrows():
        status_icon = {"Reconciled": "✅", "Variance": "🔴", "Aged Items": "🟡", "Warning": "🟡"}.get(row["status"], "⚪")
        variance_str = f"  Variance: ${row['variance']:,.2f}" if abs(row["variance"]) > 0.01 else ""
        st.write(f"{status_icon} **{row['schedule_name']}** — {row['status']}{variance_str}")

st.divider()

# ── Quick Summary Tables ───────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("AP Due This Week")
    due_soon = ap_manager.get_due_soon(data["ap"], days=7)
    if due_soon.empty:
        st.info("No AP due in next 7 days.")
    else:
        st.dataframe(
            due_soon[["vendor", "invoice_number", "due_date", "amount", "days_until_due"]],
            use_container_width=True, hide_index=True,
        )

with col_b:
    st.subheader("Floorplan — Curtailments Due")
    curt = cash_forecast.get_curtailments_due(data["floorplan"])
    if curt.empty:
        st.info("No curtailments due.")
    else:
        st.dataframe(
            curt[["stock_number", "year", "make", "model", "floor_amount",
                  "days_floored", "days_over_curtailment"]],
            use_container_width=True, hide_index=True,
        )

st.divider()
st.caption("Use the sidebar to navigate to each module. Data source: Fake (demo mode)")
