import streamlit as st
import pandas as pd
import io

st.title("Reorder Report – Revised Availability Calculator")

uploaded = st.file_uploader("Upload SOS Reorder Report (Excel)", type=["xlsx"])

if uploaded:
    # Read the FULL binary buffer to avoid partial reads on Streamlit Cloud
    data = uploaded.read()
    df = pd.read_excel(io.BytesIO(data), engine="openpyxl")

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Identify the total row (SOS labels it "Total" in column A)
    total_mask = df.iloc[:, 0].astype(str).str.strip().str.lower() == "total"

    # Separate item rows and total row
    df_items = df[~total_mask].copy()
    df_total = df[total_mask].copy()

    required = ["Available", "On SO", "On PO", "Reorder Pt", "Max Stock"]

    missing = [c for c in required if c not in df_items.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
    else:
        # Calculate Revised Available
        df_items["Revised Available"] = (
            df_items["Available"].fillna(0)
            + df_items["On SO"].fillna(0)
            + df_items["On PO"].fillna(0)
        )

        # Calculate Revised Needed
        df_items["Revised Needed"] = df_items.apply(
            lambda row: row["Max Stock"] - row["Revised Available"]
            if row["Revised Available"] <= row["Reorder Pt"]
            else 0,
            axis=1
        )

        # Reassemble final output (items first, then total row)
        df_final = pd.concat([df_items, df_total], ignore_index=True)

        st.subheader("Processed Report")
        st.dataframe(df_final)

        # Download button
        output = "Revised_Reorder_Report.xlsx"
        df_final.to_excel(output, index=False)

        with open(output, "rb") as f:
            st.download_button(
                "Download Revised Excel",
                f,
                file_name=output,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
