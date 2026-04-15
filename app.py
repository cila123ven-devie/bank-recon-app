import pandas as pd
import streamlit as st
import re

st.title("🔍 Smart Bank Reconciliation Tool")

# -------------------------------
# LOAD FILE (handles CSV + Excel)
# -------------------------------
def load_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

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
# EXTRACT POLICY FROM TEXT
# -------------------------------
def extract_policy(desc):
    match = re.search(r'(CTH\d+|CTO\d+|CTB\d+|ACU\d+|LSM\d+|AST\d+|GCI\d+|Res\d+)', str(desc))
    return match.group(0) if match else ""

# -------------------------------
# PROCESS TIAL
# -------------------------------
def process_tial(file):
    tial = load_file(file)

    tial["Group"] = tial["PolicyNo"].apply(get_group)
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    result = tial.groupby("Group")["Amount"].sum().reset_index()
    result["Account Number"] = result["Group"].map(account_map)

    return result

# -------------------------------
# PROCESS BANK
# -------------------------------
def process_bank(file):
    bank = load_file(file)

    bank["Policy"] = bank["Description"].apply(extract_policy)
    bank["Group"] = bank["Policy"].apply(get_group)
    bank["Amount"] = bank["Transaction Amount"]

    result = bank.groupby(["Group", "Account Number"])["Amount"].sum().reset_index()

    return result

# -------------------------------
# PROCESS MIS
# -------------------------------
def process_mis(file):
    mis = load_file(file)

    mis["Policy"] = mis["Description"].apply(extract_policy)
    mis["Group"] = mis["Policy"].apply(get_group)
    mis["Amount"] = mis["Transaction Amount"]

    result = mis.groupby(["Group", "Account Number"])["Amount"].sum().reset_index()

    return result

# -------------------------------
# FILE UPLOAD
# -------------------------------
bank_file = st.file_uploader("Upload Bank Statement", type=["xlsx", "xls", "csv"])
tial_file = st.file_uploader("Upload Tial Report", type=["xlsx", "xls", "csv"])
mis_file = st.file_uploader("Upload MIS Report", type=["xlsx", "xls", "csv"])

# -------------------------------
# RUN RECON
# -------------------------------
if bank_file and tial_file and mis_file:

    bank = process_bank(bank_file)
    tial = process_tial(tial_file)
    mis = process_mis(mis_file)

    results = []

    all_groups = set(bank["Group"]) | set(tial["Group"]) | set(mis["Group"])

    for group in all_groups:

        b = bank[bank["Group"] == group]
        t = tial[tial["Group"] == group]
        m = mis[mis["Group"] == group]

        bank_amt = b["Amount"].sum() if not b.empty else 0
        tial_amt = t["Amount"].sum() if not t.empty else 0
        mis_amt = m["Amount"].sum() if not m.empty else 0

        if round(bank_amt, 2) == round(tial_amt, 2) == round(mis_amt, 2):
            status = "Matched"
        else:
            status = "Mismatch"

        results.append({
            "Group": group,
            "Bank Amount": bank_amt,
            "Tial Amount": tial_amt,
            "MIS Amount": mis_amt,
            "Status": status
        })

    df = pd.DataFrame(results)

    st.success("Recon Complete ✅")
    st.dataframe(df)

    st.download_button("Download Results", df.to_csv(index=False), "recon_results.csv")
