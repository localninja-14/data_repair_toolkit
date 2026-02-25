import pandas as pd

def detect_file_type(file):
    if hasattr(file, "name"):
        filename = file.name
    else:
        filename = str(file)

    filename = filename.lower()
    if filename.endswith(".csv"):
        return "csv"
    elif filename.endswith(".xlsx"):
        return "excel"
    else:
        raise ValueError(f"Unsupported File Format: {filename}")
    
def load_file(file):
    file_type = detect_file_type(file)

    if hasattr(file, "seek"):
        file.seek(0)

    bad_rows =0
    if file_type == "csv":
            try:
                df = pd.read_csv(file)
            except pd.errors.ParserError:
                df = pd.read_csv(file, on_bad_lines='skip')
                bad_rows = "unknown - malformed rows skipped"
    else:
        try:
            df = pd.read_excel(file)
        except Exception as e:
            raise ValueError(f"Excel file reading error: {e}")
            
    return df, file_type, bad_rows
    