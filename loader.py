import pandas as pd

def detect_file_type(file_path):
    if file_path.endswith(".csv"):
        return "csv"
    elif file_path.endswith(".xlsx"):
        return "excel"
    else:
        raise ValueError("Unsupported File Format!")
    
def load_file(file_path):
    file_type = detect_file_type(file_path)

    if file_type == "csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    return df, file_type
