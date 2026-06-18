import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import date, timedelta
from data_loader import load
from modules import ap_manager
from config import DEALERSHIP_NAME, VENDORS

st.set_page_config(page_title="AP Manager | " + DEALERSHIP_NAME, layout="wide")
st.title("Accounts Payable Manager")
st.caption("AP aging, invoice log, duplicate detection, and due-date tracking.")

TODAY = date(2026, 6, 17)

@st.cache_data(ttl=60)
def get_data():
    return load("ap_invoices")

df_ap = get_data()

aging    = ap_manager.get_aging_summary(df_ap)
dupes    = ap_manager.detect_duplicates(df_ap)
due_soon = ap_manager.get_due_soon(df_ap, days=7)
overdue  = ap_manager.get_overdue(df_ap)

# ── KPIs ───────────────────────────────────────────────────────────────────────
unpaid = df_ap[df_ap["status"] == "Unpaid"]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Unpaid",    f"${unpaid['amount'].sum():,.2f}",
          delta=f"{len(unpaid)} invoices")
c2.metric("Overdue",         f"${overdue['amount'].sum():,.2f}",
          delta=f"{len(overdue)} invoices", delta_color="inverse")
c3.metric("Due This Week",   f"${due_soon['amount'].sum():,.2f}",
          delta=f"{len(due_soon)} invoices", delta_color="inverse" if len(due_soon) else "normal")
c4.metric("Paid This Month", f"${df_ap[df_ap['status']=='Paid']['amount'].sum():,.2f}")
c5.metric("Duplicate Flags", f"{len(dupes)}",
          delta_color="inverse" if len(dupes) else "normal",
          delta="Review" if len(dupes) else "None found")

st.divider()

tab_aging, tab_invoices, tab_overdue, tab_dupes, tab_add = st.tabs([
    "Aging Summary", "All Invoices", "Overdue", "Duplicate Check", "Add Invoice"
])

# ── Aging ──────────────────────────────────────────────────────────────────────
with tab_aging:
    st.subheader("AP Aging")
    col_tbl, col_chart = st.columns([2, 3])
    with col_tbl:
        aging_display = aging.copy()
        aging_display["total"] = aging_display["total"].map("${:,.2f}".format)
        st.dataframe(aging_display, use_container_width=True, hide_index=True)
        st.metric("Grand Total", f"${unpaid['amount'].sum():,.2f}")
    with col_chart:
        fig = px.bar(aging, x="aging_bucket", y="total",
                     color="aging_bucket",
                     color_discrete_map={
                         "Current":    "#70ad47",
                         "1-30 Days":  "#ffc000",
                         "31-60 Days": "#ed7d31",
                         "60+ Days":   "#c00000",
                     },
                     title="AP Aging by Bucket",
                     labels={"total":"Amount ($)","aging_bucket":"Bucket"})
        st.plotly_chart(fig, use_container_width=True)

# ── All Invoices ───────────────────────────────────────────────────────────────
with tab_invoices:
    st.subheader("Invoice Log")

    col_f1, col_f2, col_f3 = st.columns(3)
    status_filter = col_f1.selectbox("Status", ["All","Unpaid","Paid"])
    vendor_filter = col_f2.selectbox("Vendor", ["All"] + sorted(df_ap["vendor"].unique().tolist()))
    search_filter = col_f3.text_input("Search description / invoice #")

    filtered = df_ap.copy()
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]
    if vendor_filter != "All":
        filtered = filtered[filtered["vendor"] == vendor_filter]
    if search_filter:
        mask = filtered.apply(lambda r: search_filter.lower() in str(r).lower(), axis=1)
        filtered = filtered[mask]

    st.caption(f"{len(filtered)} invoices | ${filtered['amount'].sum():,.2f} total")
    st.dataframe(
        filtered[["invoice_id","vendor","invoice_number","invoice_date","due_date",
                  "amount","gl_account","department","status","days_outstanding","days_overdue"]],
        use_container_width=True, hide_index=True,
    )

# ── Overdue ────────────────────────────────────────────────────────────────────
with tab_overdue:
    if overdue.empty:
        st.success("No overdue invoices.")
    else:
        st.error(f"{len(overdue)} overdue invoice(s) — ${overdue['amount'].sum():,.2f} total")
        st.dataframe(
            overdue[["invoice_id","vendor","invoice_number","invoice_date","due_date",
                     "amount","days_overdue","approved_by"]],
            use_container_width=True, hide_index=True,
        )

# ── Duplicates ─────────────────────────────────────────────────────────────────
with tab_dupes:
    if dupes.empty:
        st.success("No potential duplicates detected.")
    else:
        st.warning(f"{len(dupes)} potential duplicate pair(s) found")
        st.dataframe(dupes, use_container_width=True, hide_index=True)
        st.caption("Review these before paying to avoid double payment.")

# ── Add Invoice ────────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Log New Invoice")
    with st.form("add_invoice_form"):
        col1, col2 = st.columns(2)
        vendor      = col1.selectbox("Vendor", sorted(VENDORS.keys()))
        inv_number  = col2.text_input("Invoice Number")
        amount      = col1.number_input("Amount ($)", min_value=0.01, step=0.01)
        inv_date    = col2.date_input("Invoice Date", value=TODAY)
        due_date    = col1.date_input("Due Date",     value=TODAY + timedelta(days=30))
        description = col2.text_input("Description")
        approved_by = st.selectbox("Approved By", ["Controller","Service Manager","Parts Manager","GM","CFO"])
        submitted   = st.form_submit_button("Log Invoice")

    if submitted:
        if not inv_number:
            st.error("Invoice number is required.")
        else:
            new_row = {
                "invoice_id":      f"INV-{len(df_ap)+1:04d}",
                "vendor":          vendor,
                "invoice_number":  inv_number,
                "invoice_date":    inv_date,
                "due_date":        due_date,
                "amount":          amount,
                "gl_account":      VENDORS.get(vendor, "6090"),
                "department":      "Admin",
                "description":     description or f"{vendor} — invoice",
                "approved_by":     approved_by,
                "status":          "Unpaid",
                "paid_date":       None,
                "days_outstanding":0,
                "days_overdue":    0,
            }
            new_df = pd.concat([df_ap, pd.DataFrame([new_row])], ignore_index=True)
            new_df.to_csv(Path(__file__).parent.parent / "data" / "fake" / "ap_invoices.csv", index=False)
            st.success(f"Invoice {inv_number} from {vendor} logged — ${amount:,.2f}")
            st.cache_data.clear()

st.divider()
if st.button("Export AP to Excel"):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        aging.to_excel(writer, sheet_name="Aging Summary", index=False)
        df_ap.to_excel(writer, sheet_name="All Invoices", index=False)
        overdue.to_excel(writer, sheet_name="Overdue", index=False)
        if not dupes.empty:
            dupes.to_excel(writer, sheet_name="Duplicates", index=False)
    st.download_button("Download AP_Report.xlsx", buf.getvalue(),
                       file_name="AP_Report.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
