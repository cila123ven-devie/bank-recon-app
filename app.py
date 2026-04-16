import pandas as pd
import streamlit as st
import re

st.title("🔍 Policy-Level Bank Reconciliation")

# -------------------------------
# POLICY EXTRACTION
# -------------------------------
def extract_policies(desc):
    desc = str(desc)

    patterns = [
        r'CTH\d+', r'CTO\d+', r'CTB\d+',
        r'ACU\d+', r'LSM\d+',
        r'AST\d+', r'GCI\d+',
        r'RSA\d+', r'Res\d+'
    ]

    found = []
    for p in patterns:
        found += re.findall(p, desc)

    return list(set(found))

# -------------------------------
# PROCESS BANK
# -------------------------------
def process_bank(files):
    df_list = []

    for f in files:
        df = pd.read_excel(f)
        df["Policies"] = df["Description"].apply(extract_policies)
        df = df.explode("Policies")
        df.rename(columns={"Policies": "Policy"}, inplace=True)

        df_list.append(df)

    bank = pd.concat(df_list, ignore_index=True)

    result = bank.groupby("Policy")["Amount"].sum().reset_index()
    return result

# -------------------------------
# PROCESS MIS
# -------------------------------
def process_mis(file):
    mis = pd.read_excel(file)

    mis["Policies"] = mis["Description"].apply(extract_policies)
    mis = mis.explode("Policies")
    mis.rename(columns={"Policies": "Policy"}, inplace=True)

    result = mis.groupby("Policy")["Amount"].sum().reset_index()
    return result

# -------------------------------
# PROCESS TIAL
# -------------------------------
def process_tial(file):
    tial = pd.read_excel(file)

    tial["Policy"] = tial["PolicyNo"]
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    result = tial.groupby("Policy")["Amount"].sum().reset_index()
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
    mis = process_mis(mis_file)
    tial = process_tial(tial_file)

    # Merge everything
    df = pd.merge(bank, mis, on="Policy", how="outer", suffixes=("_Bank", "_MIS"))
    df = pd.merge(df, tial, on="Policy", how="outer")

    df.rename(columns={"Amount": "Tial"}, inplace=True)

    df.fillna(0, inplace=True)

    # ---------------- STATUS ----------------
    def get_status(row):
        b = round(row["Amount_Bank"], 2)
        m = round(row["Amount_MIS"], 2)
        t = round(row["Tial"], 2)

        if b == m == t:
            return "Matched"
        elif b == 0:
            return "Not in Bank"
        elif m == 0:
            return "Not in MIS"
        elif t == 0:
            return "Not in Tial"
        else:
            return "Mismatch"

    df["Status"] = df.apply(get_status, axis=1)

    # Clean columns
    df = df[["Policy", "Amount_Bank", "Amount_MIS", "Tial", "Status"]]

    st.success("Recon Complete ✅")
    st.dataframe(df)

    st.download_button("Download Results", df.to_csv(index=False), "policy_recon.csv")
