import pandas as pd
import streamlit as st
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


account_map = {
    "OMI": "1206521767",
    "HOLLARD": "1206592265",
    "BRYTE": "1206521759",
    "SANTAM": "1206521775",
    "GUARDRISK": "1206521783",
    "RESQ": "1137828080"
}


def group_tial(tial):

    tial["Group"] = tial["PolicyNo"].apply(get_group)
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    result = tial.groupby(["Group"])["Amount"].sum().reset_index()

    return result
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
    tial_raw = pd.read_excel(tial_file)
tial = group_tial(tial_raw)
    mis = pd.read_excel(mis_file)

    bank["Policy"] = bank["Description"].apply(extract_policy)
    mis["Policy"] = mis["Description"].apply(extract_policy)
   tial["Group"] = tial["Group"]

    bank["Amount"] = bank["Transaction Amount"]
    mis["Amount"] = mis["Transaction Amount"]
    tial["Amount"] = tial["Bank Amount"]

    all_keys = set(bank["Policy"]) | set(tial["Group"]) | set(mis["Policy"])

    results = []

    for key in all_keys:
        b = bank[bank["Policy"] == key]
        t = tial[tial["Group"] == key]
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
