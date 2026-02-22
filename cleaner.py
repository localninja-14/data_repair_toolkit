import pandas as pd
from rapidfuzz import fuzz, process
import numpy as np
from dateutil import parser

def remove_duplicates(df):
    df = df.copy()
    return df.drop_duplicates().reset_index(drop=True)

def remove_empty_rows(df):
    df = df.copy()
    return df.dropna(how="all").reset_index(drop=True)

def fill_missing_values(df):
    df = df.copy()

    for col in df.columns:
        if df[col].dtype in [np.float64, np.int64]:
            df[col].fillna(df[col].median(), inplace=True)
        else:            
            df[col] = df[col].fillna("Unknown", inplace=True)
    return df

def standardize_column_names(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

def fix_invalid_emails(df, column="email"):
    df = df.copy()

    if column not in df.columns:
        return df
    df[column] = df[column].astype(str).str.strip().str.lower()
    df[column] = df[column].replace({"nan": ""})
    df[column] = df[column].apply(lambda x: x if "@" in x else "")
    return df
    
def normalize_dates_text(df, date_columns=None):
    df = df.copy()

    if date_columns is None:
        date_columns = [col for col in df.columns if "date" in col.lower()]
    for col in date_columns:
        def parse_date(val):
            try:
                return parser.parse(val, dayfirst=True).date()
            except:
                return pd.NaT
        df[col] = df[col].apply(parse_date)
    return df

def remove_fuzzy_duplicates(df, column_list=None, threshold=90):
    df = df.copy()

    if column_list is None:
        column_list = df.select_dtypes(include='object').columns.tolist()
    to_drop = set()
    for col in column_list:
        values = df[col].astype(str).tolist()
        matches = process.cdist(values, values, scorer=fuzz.ratio)
        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                if matches[i][j] >= threshold:
                    to_drop.add(j)
    df = df.drop(df.index[list(to_drop)]).reset_index(drop=True)
    return df

def fill_missing_context(df):
    df = df.copy()
    
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue
        if df[col].dtype in [np.float64, np.int64]:
            df[col].fillna(df[col].median(), inplace=True)
        else:
            df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown", inplace=True)
    return df