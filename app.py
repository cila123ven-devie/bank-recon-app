def extract_policy_bank(desc):
    import re
    match = re.search(r'(CTH\d+|CTO\d+|CTB\d+|ACU\d+|LSM\d+|AST\d+|GCI\d+|Res\d+)', str(desc))
    return match.group(0) if match else ""
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

  def group_tial(tial):

    tial["Group"] = tial["PolicyNo"].apply(get_group)
    tial["Amount"] = tial["Gross Premium"] + tial["Risk Premium"]

    result = tial.groupby(["Group"])["Amount"].sum().reset_index()

    result["Account Number"] = result["Group"].map(account_map)

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

bank["Policy"] = bank["Description"].apply(extract_policy_bank)
bank["Group"] = bank["Policy"].apply(get_group)
bank["Amount"] = bank["Transaction Amount"]

bank_grouped = bank.groupby(["Group", "Account Number"])["Amount"].sum().reset_index()
    tial_raw = pd.read_excel(tial_file)
tial = group_tial(tial_raw)
    mis = pd.read_excel(mis_file)

mis["Policy"] = mis["Description"].apply(extract_policy_bank)
mis["Group"] = mis["Policy"].apply(get_group)
mis["Amount"] = mis["Transaction Amount"]

mis_grouped = mis.groupby(["Group", "Account Number"])["Amount"].sum().reset_index()

    bank["Policy"] = bank["Description"].apply(extract_policy)
    mis["Policy"] = mis["Description"].apply(extract_policy)
   tial["Group"] = tial["Group"]

    bank["Amount"] = bank["Transaction Amount"]
    mis["Amount"] = mis["Transaction Amount"]
    tial["Amount"] = tial["Bank Amount"]

    all_keys = set(bank["Policy"]) | set(tial["Group"]) | set(mis["Policy"])

    results = []

  results = []

all_groups = set(bank_grouped["Group"]) | set(tial["Group"]) | set(mis_grouped["Group"])

for group in all_groups:

    b = bank_grouped[bank_grouped["Group"] == group]
    t = tial[tial["Group"] == group]
    m = mis_grouped[mis_grouped["Group"] == group]

    bank_amt = b["Amount"].sum() if not b.empty else 0
    tial_amt = t["Amount"].sum() if not t.empty else 0
    mis_amt = m["Amount"].sum() if not m.empty else 0

    if bank_amt == tial_amt == mis_amt:
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
