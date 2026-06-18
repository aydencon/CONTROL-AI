import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from data_loader import load
from modules import schedule_rec
from config import DEALERSHIP_NAME

st.set_page_config(page_title="Schedule Rec | " + DEALERSHIP_NAME, layout="wide")
st.title("Schedule Reconciliation")
st.caption("Compare GL balances to schedule detail. Flag variances and aged items.")

@st.cache_data(ttl=60)
def get_data():
    return load("schedules"), load("schedule_detail")

df_schedules, df_detail = get_data()
rec     = schedule_rec.reconcile(df_schedules, df_detail)
aged    = schedule_rec.get_aged_items(df_detail)

# ── Summary cards ─────────────────────────────────────────────────────────────
cols = st.columns(len(rec))
for col, (_, row) in zip(cols, rec.iterrows()):
    status = row["status"]
    color  = "🔴" if status == "Variance" else ("🟡" if "Aged" in status or "Warning" in status else "✅")
    col.metric(
        label=f"{color} {row['schedule_name']}",
        value=f"${row['gl_balance']:,.2f}",
        delta=f"Variance ${row['variance']:,.2f}" if abs(row['variance']) > 0.01 else "Reconciled",
        delta_color="inverse" if abs(row['variance']) > 0.01 else "normal",
    )

st.divider()

# ── Reconciliation Table ───────────────────────────────────────────────────────
st.subheader("Reconciliation Summary")

display_rec = rec.copy()
display_rec["gl_balance"]   = display_rec["gl_balance"].map("${:,.2f}".format)
display_rec["detail_sum"]   = display_rec["detail_sum"].map("${:,.2f}".format)
display_rec["variance"]     = display_rec["variance"].map("${:,.2f}".format)

def color_status(val):
    if val == "Variance":
        return "background-color: #fce4d6; color: #c00000; font-weight: bold"
    if val in ("Aged Items", "Warning"):
        return "background-color: #fff2cc; color: #7f6000"
    return "background-color: #e2efda; color: #375623"

st.dataframe(
    display_rec[["schedule_name","gl_account","gl_balance","detail_sum","variance",
                 "item_count","aged_30","aged_60","aged_90","oldest_item","status"]],
    use_container_width=True, hide_index=True,
)

# ── Drill-down ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Schedule Detail")

selected = st.selectbox("Select schedule to review:", rec["schedule_name"].tolist())
items    = schedule_rec.get_schedule_items(df_detail, selected)
gl_row   = rec[rec["schedule_name"] == selected].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("GL Balance",   f"${gl_row['gl_balance']:,.2f}")
c2.metric("Detail Sum",   f"${gl_row['detail_sum']:,.2f}")
c3.metric("Variance",     f"${gl_row['variance']:,.2f}",
          delta_color="inverse" if abs(gl_row["variance"]) > 0.01 else "normal",
          delta="OPEN" if abs(gl_row["variance"]) > 0.01 else "Balanced")

def style_age(val):
    if isinstance(val, (int, float)):
        if val >= 60:
            return "background-color: #fce4d6; color: #c00000"
        if val >= 30:
            return "background-color: #fff2cc"
    return ""

styled = items[["item_date","description","reference","amount","days_open"]].style.applymap(
    style_age, subset=["days_open"]
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Aged Items ────────────────────────────────────────────────────────────────
if len(aged):
    st.divider()
    st.subheader("All Aged Items (30+ days)")
    tab_warn, tab_crit = st.tabs(["Warning (30–59 days)", "Critical (60+ days)"])

    with tab_warn:
        warn = aged[aged["severity"] == "Warning"]
        st.dataframe(warn[["schedule_name","item_date","description","reference","amount","days_open"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"{len(warn)} items  |  ${warn['amount'].sum():,.2f} total")

    with tab_crit:
        crit = aged[aged["severity"] == "Critical"]
        st.dataframe(crit[["schedule_name","item_date","description","reference","amount","days_open"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"{len(crit)} items  |  ${crit['amount'].sum():,.2f} total")

# ── Age distribution chart ─────────────────────────────────────────────────────
st.divider()
st.subheader("Age Distribution by Schedule")

age_data = []
for sched in df_detail["schedule_name"].unique():
    s_items = df_detail[df_detail["schedule_name"] == sched]
    age_data.append({
        "Schedule":  sched,
        "0-29 days": (s_items["days_open"] < 30).sum(),
        "30-59 days":(s_items["days_open"].between(30,59)).sum(),
        "60+ days":  (s_items["days_open"] >= 60).sum(),
    })

age_df = pd.DataFrame(age_data).melt("Schedule", var_name="Age Bucket", value_name="Items")
fig = px.bar(age_df, x="Schedule", y="Items", color="Age Bucket",
             color_discrete_map={"0-29 days":"#70ad47","30-59 days":"#ffc000","60+ days":"#c00000"},
             title="Schedule Items by Age Bucket")
st.plotly_chart(fig, use_container_width=True)

# ── Excel export ───────────────────────────────────────────────────────────────
st.divider()
if st.button("Export to Excel"):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        rec.to_excel(writer, sheet_name="Summary", index=False)
        df_detail.to_excel(writer, sheet_name="All Items", index=False)
        aged.to_excel(writer, sheet_name="Aged Items", index=False)
    st.download_button("Download Schedule_Rec.xlsx", buf.getvalue(),
                       file_name="Schedule_Rec.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
