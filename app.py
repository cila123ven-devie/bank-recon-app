def process_bank(files):

    all_data = []

    for file in files:
        bank = load_file(file)

        # 🔍 Detect description column automatically
        possible_desc = ["Description", "Transaction Description", "Narrative", "Details"]
        desc_col = next((col for col in possible_desc if col in bank.columns), None)

        if desc_col is None:
            st.error(f"❌ Could not find description column in {file.name}")
            st.write(bank.columns)
            return pd.DataFrame()

        # 🔍 Detect amount column
        possible_amt = ["Transaction Amount", "Amount", "Debit", "Credit"]
        amt_col = next((col for col in possible_amt if col in bank.columns), None)

        if amt_col is None:
            st.error(f"❌ Could not find amount column in {file.name}")
            st.write(bank.columns)
            return pd.DataFrame()

        # 🔍 Detect account column
        possible_acc = ["Account Number", "Account", "Acc Number"]
        acc_col = next((col for col in possible_acc if col in bank.columns), None)

        if acc_col is None:
            st.error(f"❌ Could not find account column in {file.name}")
            st.write(bank.columns)
            return pd.DataFrame()

        # ✅ Apply logic
        bank["Policy"] = bank[desc_col].apply(extract_policy)
        bank["Group"] = bank["Policy"].apply(get_group)
        bank["Amount"] = bank[amt_col]
        bank["Account Number"] = bank[acc_col]

        all_data.append(bank)

    combined = pd.concat(all_data, ignore_index=True)

    result = combined.groupby(["Group", "Account Number"])["Amount"].sum().reset_index()

    return result

    
