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

    if file_type == "csv":
        if hasattr(file, "read"):
            df = pd.read_csv(file)
        else:
            df = pd.read_csv(file)
    else:
        if hasattr(file, "read"):
            df = pd.read_excel(file)
        else:
            df = pd.read_excel(file)

    return df, file_type
