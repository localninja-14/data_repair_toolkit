import sys
import os
from loader import load_file
from validator import validate_dataset
from column_standardizer import standardize_columns
from pdf_report import generate_pdf_report
from cleaner import remove_duplicates, remove_empty_rows, fill_missing_values

def create_output_folder():
    if not os.path.exists("output"):
        os.makedirs("output")

def main():
    if len(sys.argv) < 2:
        print("USAGE: python main.py input_file")
        return
    
    input_file = sys.argv[1]

    print("Loading dataset...")
    df, file_type = load_file(input_file)

    print("Dataset Loaded Successfully")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print(f"Detected file type: {file_type}")

    validation_summary = validate_dataset(df)

    print("\n--- Data Validation Summary ---")
    for key, value in validation_summary.items():
        print(f"{key}: {value}")

    initial_rows = df.shape[0]
    initial_duplicates = validation_summary["duplicate_rows"]
    initial_missing = validation_summary["missing_values"]
    initial_empty_rows = validation_summary["empty_rows"]

    df = standardize_columns(df)

    df = remove_duplicates(df)

    df = remove_empty_rows(df)

    df = fill_missing_values(df)

    final_rows = df.shape[0]
    
    cleaning_summary = {
        "duplicates_removed": initial_duplicates,
        "empty_rows_removed": initial_empty_rows,
        "missing_values_handled": initial_missing,
        "final_rows": final_rows
    }

    create_output_folder()

    if file_type == "csv":
        output_file = "output/cleaned_output.csv"
        df.to_csv(output_file, index=False)
    else:
        output_file = "output/cleaned_output.xlsx"
        df.to_excel(output_file, index=False)

    report_path = "output/data_cleaning_report.pdf"
    generate_pdf_report(validation_summary, report_path, input_file, cleaning_summary)

    print("Report Saved:", report_path)

if __name__ == "__main__":
    main()