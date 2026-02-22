import streamlit as st
import pandas as pd
import os

from main import load_file, validate_dataset, create_output_folder
from cleaner import (
    standardize_column_names,
    remove_duplicates,
    remove_empty_rows,
    fill_missing_values,
    fix_invalid_emails,
    normalize_dates_text,
    remove_fuzzy_duplicates,
    fill_missing_context
)
from pdf_report import generate_pdf_report

st.set_page_config(page_title="Data Cleaning Toolkit V2", layout="wide")

st.title("💎 Data Cleaning Toolkit V2")

st.header("1️⃣ Upload Files")
uploaded_files = st.file_uploader(
    "Upload datasets", type=["csv", "xlsx"], accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")

    st.header("2️⃣ Preview First File")
    first_file = uploaded_files[0]
    df_preview, file_type = load_file(first_file)
    st.dataframe(df_preview.head(10))

    st.header("3️⃣ Cleaning Rules")
    rules = {
        "standardize_cols": st.checkbox("Standardize Column Names", value=True),
        "remove_duplicates": st.checkbox("Remove Duplicates", value=True),
        "remove_empty": st.checkbox("Remove Empty Rows", value=True),
        "fill_missing": st.checkbox("Fill Missing Values", value=True),
        "fix_emails": st.checkbox("Fix Invalid Emails", value=False),
        "normalize_dates_text": st.checkbox("Normalize Dates & Text", value=False),
        "fuzzy_duplicates": st.checkbox("Remove Fuzzy Duplicates", value=False),
        "fill_missing_context": st.checkbox("Fill Missing Values with Context", value=False)
    }

    fuzzy_cols = None
    if rules["fuzzy_duplicates"]:
        fuzzy_cols_input = st.text_input("Columns for fuzzy duplicate detection (comma-separated, leave empty for all text columns)",)
        if fuzzy_cols_input.strip():
            fuzzy_cols = [c.strip() for c in fuzzy_cols_input.split(",")]

    if st.button("Run Cleaning Pipeline"):
        output_folder = "output"
        create_output_folder()
        results = []

        progress = st.progress(0)
        total_files = len(uploaded_files)

        for idx, file in enumerate(uploaded_files):
            df, file_type = load_file(file)
            validation_summary = validate_dataset(df)

            if rules["standardize_cols"]:
                df = standardize_column_names(df)
            if rules["remove_duplicates"]:
                df = remove_duplicates(df)
            if rules["remove_empty"]:
                df = remove_empty_rows(df)
            if rules["fill_missing"]:
                df = fill_missing_values(df)
            if rules["fix_emails"]:
                df = fix_invalid_emails(df)
            if rules["normalize_dates_text"]:
                df = normalize_dates_text(df)
            if rules["fuzzy_duplicates"]:
                df = remove_fuzzy_duplicates(df, column_list=fuzzy_cols)
            if rules["fill_missing_context"]:
                df = fill_missing_context(df)

            duplicates_removed = validation_summary["duplicate_rows"]
            empty_rows_removed = validation_summary["empty_rows"]
            missing_values_handled = validation_summary["missing_values"]

            cleaning_summary = {
                "duplicates_removed": duplicates_removed,
                "empty_rows_removed": empty_rows_removed,
                "missing_values_handled": missing_values_handled,
                "final_rows": df.shape[0]
            }

            filename = os.path.basename(file.name)
            cleaned_path = os.path.join(output_folder, f"cleaned_{filename}")
            if file_type == "csv":
                df.to_csv(cleaned_path, index=False)
            else:
                df.to_excel(cleaned_path, index=False)

            report_path = os.path.join(output_folder, f"{filename}_report.pdf")
            generate_pdf_report(validation_summary, report_path, filename, cleaning_summary)

            results.append({
                "file": filename,
                "rows_before": validation_summary["total_rows"],
                "rows_after": df.shape[0],
                "duplicates_removed": duplicates_removed,
                "empty_rows_removed": empty_rows_removed,
                "missing_handled": missing_values_handled,
                "cleaned_file_path": cleaned_path,
                "report_path": report_path
            })

            progress.progress((idx + 1) / total_files)

        st.header("4️⃣ Cleaning Summary")
        summary_df = pd.DataFrame(results).drop(columns=["cleaned_file_path", "report_path"])
        st.table(summary_df)

        st.header("5️⃣ Download Cleaned Files & Reports")
        for r in results:
            col1, col2 = st.columns(2)
            with col1:
                with open(r["cleaned_file_path"], "rb") as f:
                    st.download_button(
                        label=f"Download Cleaned File: {r['file']}",
                        data=f,
                        file_name=os.path.basename(r["cleaned_file_path"]),
                        mime="text/csv" if r["cleaned_file_path"].endswith(".csv") else "application/vnd.ms-excel"
                    )
            with col2:
                with open(r["report_path"], "rb") as f:
                    st.download_button(
                        label=f"Download Report: {r['file']}",
                        data=f,
                        file_name=os.path.basename(r["report_path"]),
                        mime="application/pdf"
                    )

        st.success(f"Cleaning completed! All cleaned files and reports are in '{output_folder}' folder.")