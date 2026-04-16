import pandas as pd
import streamlit as st
import re

st.title("🔍 Smart Bank Reconciliation Tool")

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
# EXTRACT ALL POLICIES
# -------------------------------
def extract_policies(desc):
    desc = str(desc)

    patterns = [
        r'CTH\d+',
        r'CTO\d+',
        r'CTB\d+',
        r'ACU\d+',
        r'LSM\d+',
        r'AST\d+',
        r'GCI\d+',
        r'RSA\d+',
        r'Res\d+'
    ]

    found = []

    for pattern in patterns:
        matches = re.findall(pattern, desc)
        found.extend(matches)

    return list(set(found))

# -------------------------------
# GET MAIN POLICY
# -------------------------------
def get_main_policy(policies):
    priority = ("CTH", "CTO", "CTB", "ACU", "LSM")

    for p in policies:
        if p.startswith(priority):
            return p

    return policies[0] if policies else ""

# -------------------------------
# LINK CHILD POLICIES
# -------------------------------
def assign_main_policy_column(df, policy_col):
    main_policy = None
    assigned = []

    for p in df[policy_col]:

        if isinstance(p, str) and p.startswith(("CTH", "CTO", "CTB", "ACU", "LSM")):
            main_policy = p
            assigned.append(p)

        elif isinstance(p, str) and p.startswith(("RSA", "AST", "GCI")):
            assigned.append(main_policy)

        else:
            assigned.append(p)

    df["MainPolicy"] = assigned
    return df

# -------------------------------
# PROCESS BANK (MULTIPLE FILES)
# -------------------------------
def process_bank(files):
    df_list = []

    for file in files:
        df = pd.read_excel(file)
        df_list.append(df)

    bank = pd.concat(df_list, ignore_index=True)

    bank["Policies"] = bank["Description"].apply(extract_policies)
    bank["Policy"] = bank["Policies"].apply(get_main_policy)
    bank = assign_main_policy_column(bank, "Policy")

    bank["Group"] = bank["MainPolicy"].apply(get_group)

    result = bank.groupby("Group")["Amount"].sum().reset_index()
    return result

# -------------------------------
# PROCESS MIS
# -------------------------------
def process_mis(file):
    mis = pd.read_excel(file)

    mis["Policies"] = mis["Description"].apply(extract_policies)
    mis["Policy"] = mis["Policies"].apply(get_main_policy)
    mis = assign_main_policy_column(mis, "Policy")

    mis["Group"] = mis["MainPolicy"].apply(get_group)

    result = mis.groupby("Group")["Amount"].sum().reset_index()
    return result

# -------------------------------
# PROCESS TIAL
# -------------------------------
def process_tial(file):
    tial = pd.read_excel(file)

    tial["Policy"] = tial["PolicyNo"]
    tial = assign_main_policy_column(tial, "Policy")

    tial["Group"] = tial["MainPolicy"].apply(get_group)
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    result = tial.groupby("Group")["Amount"].sum().reset_index()
    return result

# -------------------------------
# FILE UPLOAD
# -------------------------------
bank_files = st.file_uploader("Upload BANK FILES", type=["xlsx"], accept_multiple_files=True)
tial_file = st.file_uploader("Upload TIAL FILE", type=["xlsx"])
mis_file = st.file_uploader("Upload MIS FILE", type=["xlsx"])

# -------------------------------
# RUN RECON
# -------------------------------
if bank_files and tial_file and mis_file:

    bank = process_bank(bank_files)
    tial = process_tial(tial_file)
    mis = process_mis(mis_file)

    results = []

    all_groups = set(bank["Group"]) | set(tial["Group"]) | set(mis["Group"])

    for group in all_groups:

        bank_amt = bank[bank["Group"] == group]["Amount"].sum() if group in bank["Group"].values else 0
        mis_amt = mis[mis["Group"] == group]["Amount"].sum() if group in mis["Group"].values else 0
        tial_amt = tial[tial["Group"] == group]["Amount"].sum() if group in tial["Group"].values else 0

        results.append({
            "Group": group,
            "Bank Total": bank_amt,
            "MIS Total": mis_amt,
            "Tial Total": tial_amt,
            "Bank vs MIS": "Matched" if round(bank_amt,2) == round(mis_amt,2) else "Mismatch",
            "Bank vs Tial": "Matched" if round(bank_amt,2) == round(tial_amt,2) else "Mismatch"
        })

    df = pd.DataFrame(results)

    st.success("Recon Complete ✅")
    st.dataframe(df)

    st.download_button("Download Results", df.to_csv(index=False), "recon_results.csv")
