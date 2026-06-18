import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from datetime import date
from config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, DEALERSHIP_NAME

TODAY = date(2026, 6, 17)


def build_ap_reminder(df_overdue: pd.DataFrame, vendor_email: str) -> dict:
    vendor = df_overdue["vendor"].iloc[0] if len(df_overdue) else "Vendor"
    total  = df_overdue["amount"].sum()
    lines  = "\n".join(
        f"  • {row['invoice_number']}  |  Due {row['due_date'].date() if hasattr(row['due_date'], 'date') else row['due_date']}  |  ${row['amount']:,.2f}  ({row['days_overdue']} days overdue)"
        for _, row in df_overdue.iterrows()
    )
    subject = f"Past Due Invoice Reminder – {DEALERSHIP_NAME}"
    body = f"""Dear {vendor} Accounts Receivable Team,

This is a courtesy reminder that the following invoice(s) from {DEALERSHIP_NAME} are past due:

{lines}

Total Outstanding: ${total:,.2f}

Please confirm receipt of payment or contact us to discuss if there is a discrepancy.

Thank you,
{DEALERSHIP_NAME} — Accounting Department
"""
    return {"to": vendor_email, "subject": subject, "body": body}


def build_ar_aging_email(df_ar_customer: pd.DataFrame, contact_email: str) -> dict:
    customer = df_ar_customer["customer"].iloc[0] if len(df_ar_customer) else "Customer"
    total    = df_ar_customer["balance"].sum()
    lines    = "\n".join(
        f"  • Invoice {row['invoice_number']}  |  {row['days_outstanding']} days outstanding  |  Balance: ${row['balance']:,.2f}"
        for _, row in df_ar_customer.iterrows()
    )
    subject = f"Account Balance Reminder – {DEALERSHIP_NAME}"
    body = f"""Dear {customer},

Our records indicate the following balance(s) are outstanding on your account:

{lines}

Total Balance Due: ${total:,.2f}

Please remit payment at your earliest convenience or contact us to discuss payment arrangements.

Thank you for your business,
{DEALERSHIP_NAME} — Accounting Department
"""
    return {"to": contact_email, "subject": subject, "body": body}


def build_month_end_summary(dept_summary: pd.DataFrame, period_label: str, recipients: list[str]) -> dict:
    lines = "\n".join(
        f"  {row['department']:<20} {row['units']:>4} units   ${row['total_gross']:>10,.0f} gross   PVR ${row['avg_pvr']:>6,.0f}"
        for _, row in dept_summary.iterrows()
    )
    subject = f"{DEALERSHIP_NAME} – {period_label} Sales Summary"
    body = f"""{DEALERSHIP_NAME}
{period_label} Sales Summary
{'='*60}

Department Summary:
{lines}

This report was generated automatically by the Controller Tool.
"""
    return {"to": ", ".join(recipients), "subject": subject, "body": body}


def send_email(to: str, subject: str, body: str) -> tuple[bool, str]:
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email credentials not configured. Add EMAIL_SENDER and EMAIL_PASSWORD to .env"
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, f"Email sent to {to}"
    except Exception as e:
        return False, str(e)
