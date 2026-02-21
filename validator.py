def count_rows(df):
    return df.shape[0]

def count_columns(df):
    return df.shape[1]

def count_duplicates(df):
    return df.duplicated().sum()

def count_missing_values(df):
    return df.isnull().sum().sum()

def count_empty_rows(df):
    return df.isnull().all(axis=1).sum()

def validate_dataset(df):
    summary = {
        "total_rows": count_rows(df),
        "total_columns": count_columns(df),
        "duplicate_rows": count_duplicates(df),
        "missing_values": count_missing_values(df),
        "empty_rows": count_empty_rows(df)
    }
    return summary