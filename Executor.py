import pandas as pd
import json
from datetime import datetime
from persistent_reputation import RuleReputation

class Executor:
    def __init__(self, data_path, rules_path="approved_rules.json"):
        self.data_path = data_path
        self.rules_path = rules_path
        self.df = None
        self.rules = None
        self.logs = []

    def load(self):
        if self.data_path.endswith(".csv"):
            self.df = pd.read_csv(self.data_path, low_memory=False)
        elif self.data_path.endswith((".xls", ".xlsx")):
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError("Unsupported file type")

        with open(self.rules_path, "r") as f:
            self.rules = json.load(f)

    def log_action(self, column, action, before_dtype, after_dtype, rows_affected, pre_nulls, post_nulls, pre_unique, post_unique):
        null_delta = post_nulls - pre_nulls
        unique_delta = post_unique - pre_unique

        confidence = 1.0

        if rows_affected == 0:
            confidence -= 0.5

        if null_delta > 0:
            confidence -= 0.4

        if unique_delta < 0:
            confidence -= 0.2

        confidence = max(0.0, round(confidence, 2))
        
        if confidence < 0.5:
            status = "needs_review"
        elif confidence < 0.8:
            status = "neutral"
        else:
            status = "safe"

        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "column": column,
            "action": action,
            "before_dtype": before_dtype,
            "after_dtype": after_dtype,
            "rows_affected": int(rows_affected),
            "pre_nulls": int(pre_nulls),
            "post_nulls": int(post_nulls),
            "pre_unique": int(pre_unique),
            "post_unique": int(post_unique),
            "null_delta": int(null_delta),
            "unique_delta": int(unique_delta),
            "confidence": confidence,
            "status": status
        })

        rep = RuleReputation()
        rep.update(self.logs)

        print("Deal Number score:", rep.get_score("Deal Number", "coerce_to_float"))

    def apply_rules(self):
        for rule in self.rules:
            column = rule["column"]
            action = rule["action"]

            if column not in self.df.columns:
                raise ValueError(f"Column {column} not found in dataset")

            before_dtype = str(self.df[column].dtype)

            if action == "coerce_to_float":
                pre_nulls = self.df[column].isna().sum()
                pre_unique = self.df[column].nunique()
                original_non_null = self.df[column].notna().sum()
                self.df[column] = (
                    self.df[column]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("$", "", regex=False)
                )
                self.df[column] = pd.to_numeric(self.df[column], errors="coerce")
                rows_affected = original_non_null - self.df[column].notna().sum()
                post_nulls = self.df[column].isna().sum()
                post_unique = self.df[column].nunique()

            elif action == "parse_date":
                pre_nulls = self.df[column].isna().sum()
                pre_unique = self.df[column].nunique()
                original_non_null = self.df[column].notna().sum()
                self.df[column] = pd.to_datetime(self.df[column], errors="coerce")
                rows_affected = original_non_null - self.df[column].notna().sum()
                post_nulls = self.df[column].isna().sum()
                post_unique = self.df[column].nunique()

            elif action == "normalize_text":
                pre_nulls = self.df[column].isna().sum()
                pre_unique = self.df[column].nunique()
                self.df[column] = (
                    self.df[column]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                original_series = self.df[column].copy()

                self.df[column] = (
                    self.df[column]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                rows_affected = (original_series != self.df[column]).sum()
                post_nulls = self.df[column].isna().sum()
                post_unique = self.df[column].nunique()

            else:
                raise ValueError(f"Unsupported action: {action}")
            
            after_dtype = str(self.df[column].dtype)

            self.log_action(
                column=column,
                action=action,
                before_dtype=before_dtype,
                after_dtype=after_dtype,
                rows_affected=rows_affected,
                pre_nulls=pre_nulls,
                post_nulls=post_nulls,
                pre_unique=pre_unique,
                post_unique=post_unique
            )

    def save_outputs(self, cleaned_path="cleaned_data.csv", log_path="execution_logs.json"):
        self.df.to_csv(cleaned_path, index=False)
        with open(log_path, "w") as f:
            json.dump(self.logs, f, indent=4)
        print("Execution complete.")
        print(f"Cleaned data saved to {cleaned_path}")
        print(f"Logs saved to {log_path}")

def evaluate_gpt_proposals(self, proposals, reputation: "RuleReputation"):
    evaluated = []

    for rule in proposals:
        column = rule["column"]
        action = rule["action"]
        gpt_conf = rule.get("confidence", 0.5)

        hist_score = reputation.get_score(column, action)
        if hist_score is None:
            hist_score = gpt_conf

        combined_conf = (gpt_conf + hist_score) / 2

        if combined_conf >= 0.6:
            status = "safe"
        elif combined_conf >= 0.5:
            status = "neutral"
        else:
            status = "needs_review"

        evaluated.append({
            "column": column,
            "action": action,
            "confidence": combined_conf,
            "status": status
        })

    return evaluated
    
if __name__ == "__main__":
    import sys
    data_path = sys.argv[1] if len(sys.argv) > 1 else "sample_data/test.csv"

    executor = Executor(data_path)
    executor.load()
    executor.apply_rules()
    executor.save_outputs()