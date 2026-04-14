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

        # Function to calculate Revised Needed with new rules
        def calculate_revised_needed(row):
            revised_available = row["Revised Available"]
            reorder_pt = row["Reorder Pt"]
            max_stock = row["Max Stock"]

            # Special case: both zero
            if revised_available == 0 and reorder_pt == 0:
                return 0

            # Only calculate when Revised Available <= Reorder Pt
            if revised_available <= reorder_pt:

                # Case 1: Max Stock is missing
                if pd.isna(max_stock):
                    return (reorder_pt - revised_available) + 1

                # Case 2: Max Stock exists
                return max_stock - revised_available

            # Otherwise, no reorder needed
            return 0

        # Apply the calculation
        df_items["Revised Needed"] = df_items.apply(calculate_revised_needed, axis=1)

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
