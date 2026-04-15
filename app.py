import pandas as pd
import streamlit as st

st.title("🔍 Smart Bank Reconciliation Tool")

bank_file = st.file_uploader("Upload Bank Statement", type=["xlsx"])
tial_file = st.file_uploader("Upload Tial Report", type=["xlsx"])
mis_file = st.file_uploader("Upload MIS Report", type=["xlsx"])

def extract_policy(desc):
    if pd.isna(desc):
        return ""
    import re
    match = re.search(r'\d{6,}', str(desc))
    return match.group(0) if match else ""

if bank_file and tial_file and mis_file:

    bank = pd.read_excel(bank_file)
    tial = pd.read_excel(tial_file)
    mis = pd.read_excel(mis_file)

    bank["Policy"] = bank["Description"].apply(extract_policy)
    mis["Policy"] = mis["Description"].apply(extract_policy)
    tial["Policy"] = tial["Policy No"]

    bank["Amount"] = bank["Transaction Amount"]
    mis["Amount"] = mis["Transaction Amount"]
    tial["Amount"] = tial["Bank Amount"]

    all_keys = set(bank["Policy"]) | set(tial["Policy"]) | set(mis["Policy"])

    results = []

    for key in all_keys:
        b = bank[bank["Policy"] == key]
        t = tial[tial["Policy"] == key]
        m = mis[mis["Policy"] == key]

        if not b.empty and not t.empty and not m.empty:
            if round(b["Amount"].sum(),2) == round(t["Amount"].sum(),2) == round(m["Amount"].sum(),2):
                status = "Matched"
            else:
                status = "Amount Mismatch"
        elif b.empty:
            status = "Missing in Bank"
        elif t.empty:
            status = "Missing in Tial"
        elif m.empty:
            status = "Missing in MIS"

        results.append({
            "Policy": key,
            "Status": status
        })

    df = pd.DataFrame(results)

    st.success("Recon Complete ✅")
    st.dataframe(df)

    st.download_button("Download Results", df.to_csv(index=False), "recon_results.csv")
