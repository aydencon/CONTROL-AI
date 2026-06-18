import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
from data_loader import load
from modules import cash_forecast
from config import DEALERSHIP_NAME, CASH_LOW_THRESHOLD

st.set_page_config(page_title="Cash Forecast | " + DEALERSHIP_NAME, layout="wide")
st.title("Cash Forecast & Floorplan Tracker")
st.caption("Daily cash position for next 30 days. Floorplan balances and curtailments.")

@st.cache_data(ttl=60)
def get_data():
    return load("gl_balances"), load("floorplan"), load("ap_invoices"), load("deals")

df_gl, df_fp, df_ap, df_deals = get_data()

position   = cash_forecast.get_current_position(df_gl)
fp_summary = cash_forecast.get_floorplan_summary(df_fp)
forecast   = cash_forecast.forecast_30_days(position["cash_operating"], df_ap, df_deals, df_fp)
curtailments = cash_forecast.get_curtailments_due(df_fp)
due_soon   = cash_forecast.get_ap_due_soon(df_ap, days=7)

# ── Current Position ──────────────────────────────────────────────────────────
st.subheader("Current Position")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Operating Cash",       f"${position['cash_operating']:,.0f}")
c2.metric("Payroll Cash",         f"${position['cash_payroll']:,.0f}")
c3.metric("Total Cash",           f"${position['total_cash']:,.0f}")
c4.metric("Floorplan Payable",    f"${position['floorplan_payable']:,.0f}")
c5.metric("Net Equity Position",  f"${position['net_position']:,.0f}",
          delta_color="normal" if position["net_position"] > 0 else "inverse",
          delta="Positive" if position["net_position"] > 0 else "Negative")

st.divider()

# ── 30-Day Forecast Chart ──────────────────────────────────────────────────────
st.subheader("30-Day Cash Forecast")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=forecast["date"], y=forecast["running_balance"],
    name="Running Balance", line=dict(color="#1b3a6b", width=2), mode="lines+markers",
))
fig.add_trace(go.Bar(
    x=forecast["date"], y=forecast["receipts"],
    name="Expected Receipts", marker_color="#70ad47", opacity=0.6,
))
fig.add_trace(go.Bar(
    x=forecast["date"], y=[-d for d in forecast["disbursements"]],
    name="Disbursements", marker_color="#c00000", opacity=0.6,
))
fig.add_hline(y=CASH_LOW_THRESHOLD, line_dash="dot", line_color="orange",
              annotation_text=f"Min Cash ${CASH_LOW_THRESHOLD:,.0f}")
fig.update_layout(
    barmode="relative", height=420,
    xaxis_title="Date", yaxis_title="Amount ($)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Floorplan ──────────────────────────────────────────────────────────────────
st.subheader("Floorplan Summary")
f1, f2, f3, f4 = st.columns(4)
f1.metric("Total Units",         f"{fp_summary['total_units']}")
f2.metric("Floor Amount",        f"${fp_summary['total_floor_amount']:,.0f}")
f3.metric("Interest Accrued",    f"${fp_summary['total_interest']:,.0f}")
f4.metric("Curtailments Due",    f"{fp_summary['curtailment_count']}",
          delta=f"${fp_summary['curtailment_amount']:,.0f}" if fp_summary["curtailment_count"] else None,
          delta_color="inverse" if fp_summary["curtailment_count"] else "normal")

tab_all, tab_curt, tab_aged = st.tabs(["All Vehicles", "Curtailments Due", "Aging Analysis"])

with tab_all:
    fp_display = df_fp[["stock_number","year","make","model","color","department",
                         "floored_date","days_floored","floor_amount","interest_accrued",
                         "total_outstanding","status"]].copy()
    fp_display["floor_amount"]     = fp_display["floor_amount"].map("${:,.0f}".format)
    fp_display["interest_accrued"] = fp_display["interest_accrued"].map("${:,.2f}".format)
    fp_display["total_outstanding"]= fp_display["total_outstanding"].map("${:,.2f}".format)

    search = st.text_input("Filter by make, model, or stock #:", key="fp_search")
    if search:
        mask = fp_display.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        fp_display = fp_display[mask]
    st.dataframe(fp_display, use_container_width=True, hide_index=True)

with tab_curt:
    if curtailments.empty:
        st.success("No curtailments due.")
    else:
        st.error(f"{len(curtailments)} vehicle(s) require curtailment payment")
        st.dataframe(
            curtailments[["stock_number","year","make","model","department",
                          "floored_date","days_floored","days_over_curtailment",
                          "floor_amount","total_outstanding"]],
            use_container_width=True, hide_index=True,
        )
        st.metric("Total Curtailment Exposure", f"${curtailments['floor_amount'].sum():,.0f}")

with tab_aged:
    import plotly.express as px
    age_bins  = [0, 30, 60, 90, 120, 150, 180, 999]
    age_labels = ["0-30","31-60","61-90","91-120","121-150","151-180","180+"]
    df_fp_copy = df_fp.copy()
    df_fp_copy["age_bucket"] = pd.cut(df_fp_copy["days_floored"], bins=age_bins, labels=age_labels, right=True)
    age_summary = df_fp_copy.groupby("age_bucket", observed=True).agg(
        units=("stock_number","count"),
        total=("floor_amount","sum")
    ).reset_index()
    fig2 = px.bar(age_summary, x="age_bucket", y="units", color="total",
                  labels={"age_bucket":"Days Floored","units":"Units"},
                  title="Floorplan Units by Age",
                  color_continuous_scale=["#70ad47","#ffc000","#c00000"])
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── AP Due Soon ───────────────────────────────────────────────────────────────
st.subheader("AP Due This Week")
if due_soon.empty:
    st.info("No AP due in the next 7 days.")
else:
    st.dataframe(
        due_soon[["vendor","invoice_number","due_date","amount","days_until_due"]],
        use_container_width=True, hide_index=True,
    )
    st.metric("Total Due This Week", f"${due_soon['amount'].sum():,.2f}")

# ── Export ────────────────────────────────────────────────────────────────────
st.divider()
if st.button("Export Forecast to Excel"):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        forecast.to_excel(writer, sheet_name="30-Day Forecast", index=False)
        df_fp.to_excel(writer, sheet_name="Floorplan", index=False)
        curtailments.to_excel(writer, sheet_name="Curtailments Due", index=False)
    st.download_button("Download Cash_Forecast.xlsx", buf.getvalue(),
                       file_name="Cash_Forecast.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
