import pandas as pd
import json
import re
import os
from typing import Any, List, Dict

class Profiler:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.profile = {}

    def load(self):
        if self.data_path.endswith(".csv"):
            # use python engine and skip malformed lines to handle messy CSVs
            self.df = pd.read_csv(
                self.data_path,
                engine="python",
                on_bad_lines="skip",
            )
        elif self.data_path.endswith((".xls", ".xlsx")):
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError("Unsupported file type")

    def analyze(self):
        for col in self.df.columns:
            series = self.df[col]
            self.profile[col] = self._profile_column(col, series)

    def _profile_column(self, col: str, series: pd.Series) -> Dict[str, Any]:
        missing_pct = series.isna().mean()
        unique_count = series.nunique()
        
        non_null = series.dropna()
        samples = non_null.head(3).tolist() if len(non_null) > 0 else []
        
        numeric_ratio = self._numeric_ratio(non_null)
        date_ratio = self._date_ratio(non_null)
        
        email_ratio = self._pattern_ratio(non_null, r"^[^@]+@[^@]+\.[^@]+$")
        phone_ratio = self._pattern_ratio(non_null, r"^\+?[\d\-\(\)\s]{7,}$")
        url_ratio = self._pattern_ratio(non_null, r"^https?://")
        
        if non_null.dtype == 'object':
            str_lengths = non_null.astype(str).str.len()
            string_stats = {
                "min_length": int(str_lengths.min()),
                "max_length": int(str_lengths.max()),
                "mean_length": float(str_lengths.mean()),
            }
        else:
            string_stats = {}
        
        non_ascii_ratio = self._non_ascii_ratio(non_null)
        
        outliers = None
        if numeric_ratio > 0.7:
            outliers = self._detect_outliers(non_null)
        
        type_consistency = self._type_consistency(non_null)
        
        return {
            "dtype": str(series.dtype),
            "missing_pct": float(missing_pct),
            "unique_count": int(unique_count),
            "cardinality_ratio": float(unique_count / len(series)) if len(series) > 0 else 0,
            "numeric_ratio": float(numeric_ratio),
            "date_ratio": float(date_ratio),
            "email_ratio": float(email_ratio),
            "phone_ratio": float(phone_ratio),
            "url_ratio": float(url_ratio),
            "non_ascii_ratio": float(non_ascii_ratio),
            "type_consistency_score": float(type_consistency),
            "samples": samples,
            "string_stats": string_stats,
            "outliers": outliers,
        }

    def _numeric_ratio(self, series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        numeric_mask = series.astype(str).str.replace(",", "").str.replace("$", "").str.replace(".", "").str.replace("-", "").str.isdigit()
        return numeric_mask.mean()

    def _date_ratio(self, series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        date_mask = series.astype(str).apply(lambda x: pd.to_datetime(x, errors='coerce')).notna()
        return date_mask.mean()

    def _pattern_ratio(self, series: pd.Series, pattern: str) -> float:
        if len(series) == 0:
            return 0.0
        matches = series.astype(str).apply(lambda x: bool(re.match(pattern, str(x))))
        return matches.mean()

    def _non_ascii_ratio(self, series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        non_ascii_mask = series.astype(str).apply(lambda x: not all(ord(c) < 128 for c in str(x)))
        return non_ascii_mask.mean()

    def _type_consistency(self, series: pd.Series) -> float:
        if len(series) == 0:
            return 1.0
        str_series = series.astype(str)
        total = len(series)
        
        consistent = 0
        if pd.to_numeric(str_series, errors='coerce').notna().sum() >= total * 0.7:
            consistent = pd.to_numeric(str_series, errors='coerce').notna().sum()
        elif pd.to_datetime(str_series, errors='coerce').notna().sum() >= total * 0.7:
            consistent = pd.to_datetime(str_series, errors='coerce').notna().sum()
        else:
            consistent = total
        
        return consistent / total

    def _detect_outliers(self, series: pd.Series) -> List[Any]:
        numeric_series = pd.to_numeric(series, errors='coerce').dropna()
        if len(numeric_series) < 4:
            return None
        
        Q1 = numeric_series.quantile(0.25)
        Q3 = numeric_series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_values = numeric_series[(numeric_series < lower_bound) | (numeric_series > upper_bound)]
        return outlier_values.head(5).tolist() if len(outlier_values) > 0 else None

    def save_profile(self, path="output/data_profile.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.profile, f, indent=4, default=str)
        