import sys
import os
from loader import load_file
from validator import validate_dataset
from column_standardizer import standardize_columns

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

    df = standardize_columns(df)

    create_output_folder()

    if file_type == "csv":
        output_file = "output/cleaned_output.csv"
        df.to_csv(output_file, index=False)
    else:
        output_file = "output/cleaned_output.xlsx"
        df.to_excel(output_file, index=False)

if __name__ == "__main__":
    main()