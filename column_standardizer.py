import re

def standardize_column_name(col_name):
    col_name = col_name.strip().lower()
    col_name = col_name.replace("", "_")
    col_name = re.sub(r"[^\w_]", "", col_name)
    return col_name

def standardize_columns(df):
    df = df.copy()
    df.columns = [standardize_column_name(col) for col in df.columns]
    return df