import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
from datetime import date
from data_loader import load
from modules import month_end_report
from config import DEALERSHIP_NAME

st.set_page_config(page_title="Month-End Report | " + DEALERSHIP_NAME, layout="wide")
st.title("Month-End & YTD Reporting")
st.caption("Department P&L, unit summaries, PVR metrics, and YTD trends.")

TODAY = date(2026, 6, 17)

@st.cache_data(ttl=60)
def get_data():
    return load("deals"), load("gl_balances")

df_deals, df_gl = get_data()

# ── Period Selector ────────────────────────────────────────────────────────────
st.subheader("Select Reporting Period")
col_p1, col_p2 = st.columns([2, 4])

with col_p1:
    period_opt = st.selectbox("Period", [
        "June 2026 (Current Month)",
        "May 2026 (Prior Month)",
        "YTD Jan–Jun 2026",
        "Q2 2026 (Apr–Jun)",
        "Custom Range",
    ])

if period_opt == "June 2026 (Current Month)":
    p_start, p_end = date(2026, 6, 1), date(2026, 6, 17)
    label = "June 2026 MTD"
elif period_opt == "May 2026 (Prior Month)":
    p_start, p_end = date(2026, 5, 1), date(2026, 5, 31)
    label = "May 2026"
elif period_opt == "YTD Jan–Jun 2026":
    p_start, p_end = date(2026, 1, 1), date(2026, 6, 17)
    label = "YTD 2026"
elif period_opt == "Q2 2026 (Apr–Jun)":
    p_start, p_end = date(2026, 4, 1), date(2026, 6, 17)
    label = "Q2 2026"
else:
    with col_p2:
        c1, c2 = st.columns(2)
        p_start = c1.date_input("Start", value=date(2026, 6, 1))
        p_end   = c2.date_input("End",   value=TODAY)
    label = f"{p_start} – {p_end}"

dept_summary = month_end_report.get_department_summary(df_deals, p_start, p_end)
trend        = month_end_report.get_monthly_trend(df_deals)
sp_summary   = month_end_report.get_salesperson_summary(df_deals, p_start, p_end)
fin_mix      = month_end_report.get_finance_company_mix(df_deals, p_start, p_end)
gl_ytd       = month_end_report.get_ytd_gl_summary(df_gl)

st.divider()

# ── KPIs ───────────────────────────────────────────────────────────────────────
if not dept_summary.empty:
    totals = dept_summary[dept_summary["department"] == "TOTAL"].iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Units",   f"{totals['units']}")
    k2.metric("Front Gross",   f"${totals['front_gross']:,.0f}")
    k3.metric("Back Gross",    f"${totals['back_gross']:,.0f}")
    k4.metric("Total Gross",   f"${totals['total_gross']:,.0f}",
              delta=f"PVR ${totals['avg_pvr']:,.0f}")

st.divider()

tab_dept, tab_trend, tab_sp, tab_fin, tab_gl = st.tabs([
    "Department Summary", "Monthly Trend", "Salesperson", "Finance Mix", "GL / YTD"
])

# ── Department Summary ─────────────────────────────────────────────────────────
with tab_dept:
    st.subheader(f"Department Summary — {label}")
    if dept_summary.empty:
        st.info("No posted deals in this period.")
    else:
        st.dataframe(dept_summary, use_container_width=True, hide_index=True)

        no_total = dept_summary[dept_summary["department"] != "TOTAL"]
        fig = px.bar(no_total, x="department", y=["front_gross","back_gross"],
                     barmode="stack", title="Gross Profit by Department",
                     color_discrete_map={"front_gross":"#1b3a6b","back_gross":"#70ad47"},
                     labels={"value":"Amount ($)","variable":"Gross Type"})
        st.plotly_chart(fig, use_container_width=True)

# ── Monthly Trend ─────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Monthly Trend — YTD 2026")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=trend["month_label"], y=trend["total_gross"],
                          name="Total Gross", marker_color="#1b3a6b"))
    fig2.add_trace(go.Scatter(x=trend["month_label"], y=trend["avg_pvr"],
                              name="Avg PVR", yaxis="y2", mode="lines+markers",
                              line=dict(color="#c00000", width=2)))
    fig2.update_layout(
        yaxis=dict(title="Total Gross ($)"),
        yaxis2=dict(title="Avg PVR ($)", overlaying="y", side="right"),
        legend=dict(orientation="h"),
        height=420,
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(trend, x="month_label", y="units", title="Units Sold by Month",
                  color_discrete_sequence=["#1b3a6b"])
    st.plotly_chart(fig3, use_container_width=True)

# ── Salesperson ────────────────────────────────────────────────────────────────
with tab_sp:
    st.subheader(f"Salesperson Performance — {label}")
    if sp_summary.empty:
        st.info("No data for this period.")
    else:
        sp_summary["avg_pvr"] = sp_summary["avg_pvr"].round(0).astype(int)
        st.dataframe(sp_summary, use_container_width=True, hide_index=True)
        fig4 = px.bar(sp_summary, x="salesperson", y="total_gross",
                      title="Gross by Salesperson", color="units",
                      color_continuous_scale="Blues",
                      labels={"total_gross":"Total Gross ($)"})
        st.plotly_chart(fig4, use_container_width=True)

# ── Finance Mix ────────────────────────────────────────────────────────────────
with tab_fin:
    st.subheader(f"Finance Company Mix — {label}")
    if fin_mix.empty:
        st.info("No data for this period.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(fin_mix, use_container_width=True, hide_index=True)
        with c2:
            fig5 = px.pie(fin_mix, names="finance_company", values="deals",
                          title="Deals by Finance Company")
            st.plotly_chart(fig5, use_container_width=True)

# ── GL / YTD ──────────────────────────────────────────────────────────────────
with tab_gl:
    st.subheader("GL — YTD vs Budget vs Prior Year")
    st.dataframe(
        gl_ytd.style.applymap(
            lambda v: "color: #c00000" if isinstance(v, float) and v < 0 else "",
            subset=["variance_to_budget"]
        ),
        use_container_width=True, hide_index=True,
    )

# ── Export ────────────────────────────────────────────────────────────────────
st.divider()
if st.button("Export Report to Excel"):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if not dept_summary.empty:
            dept_summary.to_excel(writer, sheet_name="Department Summary", index=False)
        trend.to_excel(writer, sheet_name="Monthly Trend", index=False)
        if not sp_summary.empty:
            sp_summary.to_excel(writer, sheet_name="Salesperson", index=False)
        gl_ytd.to_excel(writer, sheet_name="GL YTD", index=False)
    st.download_button("Download Month_End_Report.xlsx", buf.getvalue(),
                       file_name=f"Month_End_{label.replace(' ','_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
