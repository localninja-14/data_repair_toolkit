import pandas as pd
import json
import re
from dateutil.parser import parse

class Profiler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.profile = {}

    def load_data(self):
        if self.filepath.endswith('.csv'):
            self.df = pd.read_csv(self.filepath, low_memory=False)
        elif self.filepath.endswith(('.xls', '.xlsx')):
            self.df = pd.read_excel(self.filepath)
        else:
            raise ValueError("Unsupported file type")

    def numeric_like_ratio(self, series):
        total = len(series)
        if total == 0:
            return 0.0
        numeric_count = series.dropna().apply(lambda x: bool(re.match(r'^-?\d+(\.\d+)?$', str(x).strip()))).sum()
        return float(numeric_count / total)

    def date_like_ratio(self, series):
        total = len(series)
        if total == 0:
            return 0.0
        date_count = 0
        for v in series.dropna():
            try:
                parse(str(v))
                date_count += 1
            except:
                continue
        return float(date_count / total)

    def profile_columns(self):
        for col in self.df.columns:
            series = self.df[col]
            top_vals = [
                v.item() if hasattr(v, 'item') else v
                for v in series.dropna().unique()[:5]
            ]
            self.profile[col] = {
                "dtype_original": str(series.dtype),
                "missing_pct": float(series.isna().mean()),
                "unique_count": int(series.nunique()),
                "top_values": top_vals,
                "numeric_ratio": self.numeric_like_ratio(series),
                "date_ratio": self.date_like_ratio(series)
            }

    def save_profile(self, output_path="profiles.json"):
        with open(output_path, "w") as f:
            json.dump(self.profile, f, indent=4)
        print(f"Profile saved to {output_path}")

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_data/test.csv"
    profiler = Profiler(path)
    profiler.load_data()
    profiler.profile_columns()
    profiler.save_profile()