import streamlit as st
import pandas as pd
import os

from main import load_file, validate_dataset, standardize_columns, create_output_folder
from cleaner import remove_duplicates, remove_empty_rows, fill_missing_values
from pdf_report import generate_pdf_report

st.title("Data Repair Toolkit")

st.header("1️⃣ Upload Files")
uploaded_files = st.file_uploader("Upload CSV or Excel files", accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")

    st.header("2️⃣ Data Preview")
    first_file = uploaded_files[0]
    df, file_type = load_file(first_file)
    st.dataframe(df.head(10))

    st.header("3️⃣ Cleaning Rules")
    remove_dup = st.checkbox("Remove Duplicates", value=True)
    remove_empty = st.checkbox("Remove Empty Rows", value=True)
    fill_missing = st.checkbox("Fill Missing Values", value=True)
    standardize_cols = st.checkbox("Standardize Column Names", value=True)

    if st.button("Run Cleaning Pipeline"):
        output_folder = "output"
        create_output_folder()

        results = []

        for file in uploaded_files:
            df, file_type = load_file(file)

            validation_summary = validate_dataset(df)

            if standardize_cols:
                df = standardize_columns(df)
            if remove_dup:
                df = remove_duplicates(df)
            if remove_empty:
                df = remove_empty_rows(df)
            if fill_missing:
                df = fill_missing_values(df)

            duplicates_count = validation_summary["duplicate_rows"]
            empty_rows_count = validation_summary["empty_rows"]
            missing_count = validation_summary["missing_values"]

            cleaning_summary = {
                "duplicates_removed": duplicates_count,
                "empty_rows_removed": empty_rows_count,
                "missing_values_handled": missing_count,
                "final_rows": df.shape[0]
            }

            filename = os.path.basename(file.name)
            if file_type == "csv":
                cleaned_path = os.path.join(output_folder, f"cleaned_{filename}")
                df.to_csv(cleaned_path, index=False)
            else:
                cleaned_path = os.path.join(output_folder, f"cleaned_{filename}")
                df.to_excel(cleaned_path, index=False)

            report_path = os.path.join(output_folder, f"{filename}_report.pdf")
            generate_pdf_report(validation_summary, report_path, filename, cleaning_summary)

            results.append({
                "file": filename,
                "rows_before": validation_summary["total_rows"],
                "rows_after": df.shape[0],
                "duplicates_removed": validation_summary["duplicate_rows"],
                "missing_handled": validation_summary["missing_values"]
            })

        st.header("4️⃣ Cleaning Summary")
        st.table(pd.DataFrame(results))

        st.success(f"Cleaning completed! Check the '{output_folder}' folder for cleaned files and reports.")