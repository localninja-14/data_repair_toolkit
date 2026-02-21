import pandas as pd
import re
def remove_duplicates(df):
    return df.drop_duplicates()

def remove_empty_rows(df):
    return df.dropna(how="all")

def fill_missing_values(df):
    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("unknown")
        else:
            df[col] = df[col].fillna(0)

def fix_invalid_emails(df):
    for col in df.columns:
        if "email" in col.lower():
            df[col] = df[col].apply(lambda x: x if pd.notnull(x) and re.match(r"[^@]+@[^@]+\.[^@]+", str(x)) else "")
    return df

def normalize_dates_texts(df):
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_datetime(df[col], errors="ignore")
            except:
                pass
            df[col] = df[col].apply(lambda x: str(x).strip().lower() if pd.notnull(x) else x)
        elif "datetime" in str(df[col].dtype):
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")