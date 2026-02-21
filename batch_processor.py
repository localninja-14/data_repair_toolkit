import os
from loader import load_file
from validator import validate_dataset
from column_standardizer import standardize_columns
from cleaner import remove_duplicates, remove_empty_rows, fill_missing_values, fix_invalid_emails, normalize_dates_text
from pdf_report import generate_pdf_report
from config import OUTPUT_FOLDER

def create_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

def process_files(file_list, rules):
    create_output_folder()
    results = []

    for file in file_list:
        filename = file.name if hasattr(file, "name") else os.path.basename(file)

        df, file_type = load_file(file)

        validation_summary = validate_dataset(df)

        if rules.get("standardize_cols", False):
            df = standardize_columns(df)

        duplicates_removed = 0
        empty_rows_removed = 0
        missing_handled = 0

        if rules.get("remove_duplicates", False):
            df, duplicates_removed = remove_duplicates(df)
        if rules.get("remove_empty", False):
            df, empty_rows_removed = remove_empty_rows(df)
        if rules.get("fill_missing", False):
            df, missing_handled = fill_missing_values(df)
        if rules.get("fix_emails", False):
            df = fix_invalid_emails(df)
        if rules.get("normalize_dates_text", False):
            df = normalize_dates_text(df)

        cleaned_path = os.path.join(OUTPUT_FOLDER, f"cleaned_{filename}")
        if file_type == "csv":
            df.to_csv(cleaned_path, index=False)
        else:
            df.to_excel(cleaned_path, index=False)

        cleaning_summary = {
            "duplicates_removed": duplicates_removed,
            "empty_rows_removed": empty_rows_removed,
            "missing_values_handled": missing_handled,
            "final_rows": df.shape[0]
        }
        report_path = os.path.join(OUTPUT_FOLDER, f"{filename}_report.pdf")
        generate_pdf_report(validation_summary, report_path, filename, cleaning_summary)

        results.append({
            "file": filename,
            "rows_before": validation_summary["total_rows"],
            "rows_after": df.shape[0],
            "duplicates_removed": duplicates_removed,
            "missing_handled": missing_handled
        })

    return results