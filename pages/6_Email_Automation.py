import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from data_loader import load
from modules import email_automation, ap_manager
from config import DEALERSHIP_NAME, EMAIL_SENDER

st.set_page_config(page_title="Email Automation | " + DEALERSHIP_NAME, layout="wide")
st.title("Email Automation")
st.caption("Generate and send AP reminders, AR aging notices, and month-end summaries.")

if not EMAIL_SENDER:
    st.warning(
        "Email credentials not configured. Add `EMAIL_SENDER` and `EMAIL_PASSWORD` to your `.env` file to enable sending. "
        "You can still preview and copy emails below."
    )

@st.cache_data(ttl=60)
def get_data():
    return load("ap_invoices"), load("ar_aging")

df_ap, df_ar = get_data()
overdue_ap   = ap_manager.get_overdue(df_ap)

tab_ap, tab_ar, tab_summary = st.tabs(["AP Vendor Reminders", "AR Customer Notices", "Month-End Summary"])

# ── AP Reminders ───────────────────────────────────────────────────────────────
with tab_ap:
    st.subheader("Send Overdue Invoice Reminders to Vendors")

    if overdue_ap.empty:
        st.success("No overdue AP invoices to send reminders for.")
    else:
        overdue_vendors = sorted(overdue_ap["vendor"].unique().tolist())
        selected_vendor = st.selectbox("Select vendor to remind:", overdue_vendors)

        vendor_invoices = overdue_ap[overdue_ap["vendor"] == selected_vendor].copy()
        vendor_invoices["due_date"] = pd.to_datetime(vendor_invoices["due_date"])

        st.caption(f"{len(vendor_invoices)} overdue invoice(s) — ${vendor_invoices['amount'].sum():,.2f} total")

        vendor_email = st.text_input("Vendor email address:", placeholder="ap@vendor.com")

        if vendor_email:
            email_data = email_automation.build_ap_reminder(vendor_invoices, vendor_email)

            st.subheader("Email Preview")
            st.text(f"To:      {email_data['to']}")
            st.text(f"Subject: {email_data['subject']}")
            st.text_area("Body", email_data["body"], height=280)

            if st.button("Send AP Reminder", type="primary"):
                ok, msg = email_automation.send_email(
                    email_data["to"], email_data["subject"], email_data["body"]
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(f"Failed: {msg}")
        else:
            st.info("Enter the vendor's email address to preview and send the reminder.")

# ── AR Notices ────────────────────────────────────────────────────────────────
with tab_ar:
    st.subheader("Send AR Aging Notices to Customers")

    aged_ar = df_ar[df_ar["days_outstanding"] >= 30].copy()

    if aged_ar.empty:
        st.success("No AR items over 30 days.")
    else:
        ar_customers = sorted(aged_ar["customer"].unique().tolist())
        selected_cust = st.selectbox("Select customer:", ar_customers)

        cust_invoices = aged_ar[aged_ar["customer"] == selected_cust]
        contact_email = cust_invoices["contact_email"].iloc[0]

        st.caption(f"{len(cust_invoices)} invoice(s) outstanding — ${cust_invoices['balance'].sum():,.2f}")
        st.dataframe(
            cust_invoices[["invoice_number","invoice_date","amount","days_outstanding","aging_bucket"]],
            use_container_width=True, hide_index=True,
        )

        override_email = st.text_input("Email address (auto-filled):", value=contact_email)

        email_data = email_automation.build_ar_aging_email(cust_invoices, override_email)

        st.subheader("Email Preview")
        st.text(f"To:      {email_data['to']}")
        st.text(f"Subject: {email_data['subject']}")
        st.text_area("Body", email_data["body"], height=250, key="ar_body")

        if st.button("Send AR Notice", type="primary"):
            ok, msg = email_automation.send_email(
                email_data["to"], email_data["subject"], email_data["body"]
            )
            if ok:
                st.success(msg)
            else:
                st.error(f"Failed: {msg}")

    st.divider()
    st.subheader("Full AR Aging Summary")
    bucket_totals = df_ar.groupby("aging_bucket").agg(
        customers=("customer","nunique"), total=("balance","sum")
    ).reset_index()
    st.dataframe(bucket_totals, use_container_width=True, hide_index=True)
    st.metric("Total AR Outstanding", f"${df_ar['balance'].sum():,.2f}")

# ── Month-End Summary Email ───────────────────────────────────────────────────
with tab_summary:
    st.subheader("Send Month-End Summary Email")

    from data_loader import load as dload
    from modules import month_end_report
    from datetime import date

    df_deals = dload("deals")
    dept_sum = month_end_report.get_department_summary(
        df_deals, date(2026, 6, 1), date(2026, 6, 17)
    )

    recipients_raw = st.text_area(
        "Recipient emails (one per line or comma-separated):",
        placeholder="gm@doylechrysler.com\npresident@doylechrysler.com"
    )
    period_label = st.text_input("Period label:", value="June 2026 MTD")

    if not dept_sum.empty:
        recipients = [r.strip() for r in recipients_raw.replace(",","\n").split("\n") if r.strip()]
        email_data = email_automation.build_month_end_summary(dept_sum, period_label, recipients or ["(no recipients)"])

        st.subheader("Email Preview")
        st.text(f"To:      {email_data['to']}")
        st.text(f"Subject: {email_data['subject']}")
        st.text_area("Body", email_data["body"], height=220, key="summ_body")

        if st.button("Send Summary Email", type="primary"):
            if not recipients:
                st.error("Add at least one recipient email.")
            else:
                for r in recipients:
                    ok, msg = email_automation.send_email(r, email_data["subject"], email_data["body"])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(f"{r}: {msg}")
