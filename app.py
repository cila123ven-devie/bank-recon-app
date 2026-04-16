import pandas as pd
import streamlit as st
import re

st.title("🔍 Smart Bank Reconciliation Tool")

# -------------------------------
# DATE CLEANING
# -------------------------------
def clean_date(df, column):
    df[column] = pd.to_datetime(df[column], errors='coerce')
    df[column] = df[column].dt.strftime('%Y-%m-%d')
    return df

# -------------------------------
# GROUP MAPPING
# -------------------------------
def get_group(policy):
    policy = str(policy)

    if policy.startswith("CTO"):
        return "OMI"
    elif policy.startswith(("CTH", "HD", "CTHB")):
        return "HOLLARD"
    elif policy.startswith("CTB"):
        return "BRYTE"
    elif policy.startswith(("ACU", "LSM")):
        return "SANTAM"
    elif policy.startswith(("AST", "GCI")):
        return "GUARDRISK"
    elif policy.startswith("Res"):
        return "RESQ"
    else:
        return "UNKNOWN"

# -------------------------------
# ACCOUNT MAP
# -------------------------------
account_map = {
    "OMI": "1206521767",
    "HOLLARD": "1206592265",
    "BRYTE": "1206521759",
    "SANTAM": "1206521775",
    "GUARDRISK": "1206521783",
    "RESQ": "1137828080"
}

# -------------------------------
# EXTRACT POLICY
# -------------------------------
def extract_policy(desc):
    match = re.search(r'(CTH\d+|CTO\d+|CTB\d+|ACU\d+|LSM\d+|AST\d+|GCI\d+|Res\d+)', str(desc))
    return match.group(0) if match else ""

# -------------------------------
# FILE UPLOAD
# -------------------------------
bank_file = st.file_uploader("Upload BANK TEMPLATE", type=["xlsx"])
tial_file = st.file_uploader("Upload TIAL TEMPLATE", type=["xlsx"])
mis_file = st.file_uploader("Upload MIS TEMPLATE", type=["xlsx"])

# -------------------------------
# RUN RECON
# -------------------------------
if bank_file and tial_file and mis_file:

    bank = pd.read_excel(bank_file)
    tial = pd.read_excel(tial_file)
    mis = pd.read_excel(mis_file)

    # Clean Dates
    bank = clean_date(bank, "Date")
    tial = clean_date(tial, "Date")
    mis = clean_date(mis, "Date")

    # ---------------- BANK ----------------
    bank["Policy"] = bank["Description"].apply(extract_policy)
    bank["Group"] = bank["Policy"].apply(get_group)

    bank_grouped = bank.groupby(["Date", "Group", "Account Number"])["Amount"].sum().reset_index()

    # ---------------- TIAL ----------------
    tial["Group"] = tial["PolicyNo"].apply(get_group)
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    tial_grouped = tial.groupby(["Date", "Group"])["Amount"].sum().reset_index()
    tial_grouped["Account Number"] = tial_grouped["Group"].map(account_map)

    # ---------------- MIS ----------------
    mis["Policy"] = mis["Description"].apply(extract_policy)
    mis["Group"] = mis["Policy"].apply(get_group)

    mis_grouped = mis.groupby(["Date", "Group", "Account Number"])["Amount"].sum().reset_index()

    # ---------------- MATCHING ----------------
    results = []

    all_keys = set(
        tuple(x) for x in bank_grouped[["Date", "Group"]].values
    ) | set(
        tuple(x) for x in tial_grouped[["Date", "Group"]].values
    ) | set(
        tuple(x) for x in mis_grouped[["Date", "Group"]].values
    )

    for date, group in all_keys:

        b = bank_grouped[(bank_grouped["Date"] == date) & (bank_grouped["Group"] == group)]
        t = tial_grouped[(tial_grouped["Date"] == date) & (tial_grouped["Group"] == group)]
        m = mis_grouped[(mis_grouped["Date"] == date) & (mis_grouped["Group"] == group)]

        bank_amt = b["Amount"].sum() if not b.empty else 0
        tial_amt = t["Amount"].sum() if not t.empty else 0
        mis_amt = m["Amount"].sum() if not m.empty else 0

        if round(bank_amt, 2) == round(tial_amt, 2) == round(mis_amt, 2):
            status = "Matched"
        else:
            status = "Mismatch"

        results.append({
            "Date": date,
            "Group": group,
            "Bank": bank_amt,
            "Tial": tial_amt,
            "MIS": mis_amt,
            "Status": status
        })

    df = pd.DataFrame(results)

    st.success("Recon Complete ✅")
    st.dataframe(df)

    st.download_button("Download Results", df.to_csv(index=False), "recon_results.csv")
