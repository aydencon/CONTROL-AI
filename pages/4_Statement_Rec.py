import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from io import BytesIO
from data_loader import load
from modules import statement_rec
from config import DEALERSHIP_NAME

st.set_page_config(page_title="Statement Rec | " + DEALERSHIP_NAME, layout="wide")
st.title("Bank & Statement Reconciliation")
st.caption("Match GL cash entries to bank statement. Surface unmatched items on both sides.")

@st.cache_data(ttl=60)
def get_default_data():
    return load("bank_transactions"), load("gl_cash_transactions")

tab_demo, tab_upload = st.tabs(["Use Fake Data (Demo)", "Upload Your Files"])

# ── Demo Tab ───────────────────────────────────────────────────────────────────
with tab_demo:
    st.info("Using built-in fake bank and GL data for Doyle Chrysler.")

    df_bank, df_gl_cash = get_default_data()

    matched, bank_only, gl_only = statement_rec.match_bank_to_gl(df_bank, df_gl_cash)
    summary = statement_rec.get_rec_summary(matched, bank_only, gl_only, df_bank, df_gl_cash)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Matched",         f"{summary['matched_count']}")
    c2.metric("Bank Only",       f"{summary['bank_only_count']}",
              delta_color="inverse" if summary["bank_only_count"] else "normal",
              delta="Needs attention" if summary["bank_only_count"] else "None")
    c3.metric("GL Only",         f"{summary['gl_only_count']}",
              delta_color="inverse" if summary["gl_only_count"] else "normal",
              delta="Needs attention" if summary["gl_only_count"] else "None")
    c4.metric("Net Difference",  f"${summary['difference']:,.2f}",
              delta_color="inverse" if abs(summary["difference"]) > 0.01 else "normal",
              delta="Out of balance" if abs(summary["difference"]) > 0.01 else "Balanced")

    st.divider()

    tab_m, tab_bo, tab_go = st.tabs(["Matched Items", "Bank Only (unrecorded in GL)", "GL Only (outstanding checks)"])

    with tab_m:
        st.caption(f"{len(matched)} matched transactions")
        st.dataframe(matched, use_container_width=True, hide_index=True)

    with tab_bo:
        if bank_only.empty:
            st.success("All bank items matched to GL.")
        else:
            st.warning(f"{len(bank_only)} bank transactions not found in GL")
            st.dataframe(
                bank_only[["date","description","amount","reference"]],
                use_container_width=True, hide_index=True,
            )
            st.caption(f"Total: ${bank_only['amount'].sum():,.2f} — These are likely bank charges not yet recorded.")

    with tab_go:
        if gl_only.empty:
            st.success("All GL items matched to bank.")
        else:
            st.info(f"{len(gl_only)} GL entries not yet cleared at bank")
            st.dataframe(
                gl_only[["date","description","debit","credit","reference"]],
                use_container_width=True, hide_index=True,
            )
            net = (gl_only["debit"].fillna(0) - gl_only["credit"].fillna(0)).sum()
            st.caption(f"Net outstanding: ${net:,.2f} — These are likely outstanding checks.")

    if st.button("Export Bank Rec to Excel"):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
            matched.to_excel(writer, sheet_name="Matched", index=False)
            bank_only.to_excel(writer, sheet_name="Bank Only", index=False)
            gl_only.to_excel(writer, sheet_name="GL Only", index=False)
        st.download_button("Download Bank_Rec.xlsx", buf.getvalue(),
                           file_name="Bank_Rec.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── Upload Tab ────────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("""
Upload your own GL export and bank/vendor statement.

**GL file** should have columns: `date`, `description`, `debit`, `credit`, `reference`
**Statement file** should have columns: `date`, `description`, `amount`

Accepted formats: **.csv** or **.xlsx**
""")
    col_gl, col_stmt = st.columns(2)
    gl_file   = col_gl.file_uploader("GL Export",    type=["csv","xlsx"], key="gl_up")
    stmt_file = col_stmt.file_uploader("Statement",  type=["csv","xlsx"], key="stmt_up")

    if gl_file and stmt_file:
        def read_file(f):
            if f.name.endswith(".csv"):
                return pd.read_csv(f)
            return pd.read_excel(f)

        try:
            u_gl   = read_file(gl_file)
            u_stmt = read_file(stmt_file)
            st.success(f"Loaded: GL {len(u_gl)} rows | Statement {len(u_stmt)} rows")

            if "debit" not in u_gl.columns:
                u_gl["debit"]  = u_gl.get("amount", 0).clip(lower=0)
                u_gl["credit"] = (-u_gl.get("amount", 0)).clip(lower=0)

            u_matched, u_bank_only, u_gl_only = statement_rec.match_bank_to_gl(u_stmt, u_gl)
            u_summary = statement_rec.get_rec_summary(u_matched, u_bank_only, u_gl_only, u_stmt, u_gl)

            m1, m2, m3 = st.columns(3)
            m1.metric("Matched",    f"{u_summary['matched_count']}")
            m2.metric("Stmt Only",  f"{u_summary['bank_only_count']}")
            m3.metric("GL Only",    f"{u_summary['gl_only_count']}")

            st.subheader("Unmatched Statement Items")
            st.dataframe(u_bank_only, use_container_width=True, hide_index=True)

            st.subheader("Unmatched GL Items")
            st.dataframe(u_gl_only, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error processing files: {e}")
