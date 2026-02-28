import pandas as pd
import json
from datetime import datetime
import ast
import builtins
from utils import sanitize_column_name

class Executor:
    def __init__(self, data_path, rules_path="output/proposed_rules.json"):
        self.data_path = data_path
        self.rules_path = rules_path
        self.df = None
        self.rules = None
        self.column_name_map = {}  # maps original -> sanitized
        self.logs = []
        self._function_namespace = {}

    def load(self):
        if self.data_path.endswith(".csv"):
            self.df = pd.read_csv(
                self.data_path,
                engine="python",
                on_bad_lines="skip",
            )
        elif self.data_path.endswith((".xls", ".xlsx")):
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError("Unsupported file type")

        with open(self.rules_path, "r") as f:
            rules_data = json.load(f)
        
        # extract column_name_map and proposals from the new format
        if isinstance(rules_data, dict) and "column_name_map" in rules_data:
            self.column_name_map = rules_data["column_name_map"]
            self.rules = rules_data["proposals"]
        else:
            # fallback to legacy format (direct dict or list of rules)
            self.rules = rules_data
            # if it's a dict, build map from column names
            if isinstance(self.rules, dict):
                self.column_name_map = {col: sanitize_column_name(col) for col in self.rules.keys()}

    def _validate_code(self, code: str):
        """Quick AST check to forbid unsafe operations."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in code: {e}")

        forbidden_nodes = (ast.Import, ast.ImportFrom)
        forbidden_names = {"open", "exec", "eval", "compile", "__import__", "os", "sys", "subprocess", "socket"}

        for node in ast.walk(tree):
            if isinstance(node, forbidden_nodes):
                raise ValueError(f"Forbidden statement {type(node).__name__} in user code")
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name and name in forbidden_names:
                    raise ValueError(f"Forbidden function call '{name}' in user code")

    def _restricted_builtins(self):
        # allow a small set of safe builtins
        allow = [
            "abs", "len", "min", "max", "sum", "any", "all", "sorted",
            "str", "int", "float", "bool", "list", "dict", "set", "tuple",
            "range", "enumerate", "zip", "map", "filter",
        ]
        return {k: getattr(builtins, k) for k in allow}

    def _run_in_sandbox(self, func_source: str, func_name: str, series):
        """Execute function code in restricted namespace (in-process)."""
        try:
            safe_globals = {"pd": pd, "__builtins__": self._restricted_builtins()}
            local_ns = {}
            exec(func_source, safe_globals, local_ns)
            f = local_ns.get(func_name)
            if f is None:
                raise RuntimeError(f"Function {func_name} not defined")
            result = f(series)
            return result
        except Exception as e:
            raise RuntimeError(f"Error executing {func_name}: {e}")

    def log_action(self, column, action, before_dtype, after_dtype, rows_affected, pre_nulls, post_nulls, pre_unique, post_unique):
        null_delta = post_nulls - pre_nulls
        unique_delta = post_unique - pre_unique

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
            "unique_delta": int(unique_delta)
        })

    def apply_rules(self, dry_run: bool = False):
        """Apply the loaded rules to the dataframe.

        If dry_run is True the original dataframe is not modified; the
        transformations are computed on a temporary copy and results are
        reported in logs. Supports two types of rule formats:
        1. list of dicts with 'column' and 'action' (legacy behavior)
        2. dict mapping column -> python function source code (from GPT advisor)
        """
        target_df = self.df.copy() if dry_run else self.df

        if isinstance(self.rules, dict):
            # GPT-produced mapping: column -> function source string
            for col, func_code in self.rules.items():
                column = col
                if column not in target_df.columns:
                    raise ValueError(f"Column {column} not found in dataset")
                
                # get sanitized column name for function lookup
                sanitized_col = self.column_name_map.get(column, sanitize_column_name(column))
                func_name = f"clean_{sanitized_col}"

                # validate the code before attempting to run it
                try:
                    self._validate_code(func_code)
                except Exception as exc:
                    raise RuntimeError(f"Code validation failed for {column}: {exc}")

                before_dtype = str(target_df[column].dtype)
                pre_nulls = target_df[column].isna().sum()
                pre_unique = target_df[column].nunique()
                original_series = target_df[column].copy()

                # apply cleaning function in restricted namespace
                try:
                    cleaned = self._run_in_sandbox(func_code, func_name, original_series)
                except Exception as exc:
                    raise RuntimeError(f"Error running sandboxed function for {column}: {exc}")

                target_df[column] = cleaned
                rows_affected = (original_series != cleaned).sum()
                post_nulls = cleaned.isna().sum()
                post_unique = cleaned.nunique()
                after_dtype = str(cleaned.dtype)

                self.log_action(
                    column=column,
                    action="gpt_function",
                    before_dtype=before_dtype,
                    after_dtype=after_dtype,
                    rows_affected=rows_affected,
                    pre_nulls=pre_nulls,
                    post_nulls=post_nulls,
                    pre_unique=pre_unique,
                    post_unique=post_unique,
                )
        else:
            # legacy list of rules
            for rule in self.rules:
                column = rule["column"]
                action = rule["action"]

                if column not in target_df.columns:
                    raise ValueError(f"Column {column} not found in dataset")

                before_dtype = str(target_df[column].dtype)

                if action == "coerce_to_float":
                    pre_nulls = target_df[column].isna().sum()
                    pre_unique = target_df[column].nunique()
                    original_non_null = target_df[column].notna().sum()
                    target_df[column] = (
                        target_df[column]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.replace("$", "", regex=False)
                    )
                    target_df[column] = pd.to_numeric(target_df[column], errors="coerce")
                    rows_affected = original_non_null - target_df[column].notna().sum()
                    post_nulls = target_df[column].isna().sum()
                    post_unique = target_df[column].nunique()

                elif action == "parse_date":
                    pre_nulls = target_df[column].isna().sum()
                    pre_unique = target_df[column].nunique()
                    original_non_null = target_df[column].notna().sum()
                    target_df[column] = pd.to_datetime(target_df[column], errors="coerce")
                    rows_affected = original_non_null - target_df[column].notna().sum()
                    post_nulls = target_df[column].isna().sum()
                    post_unique = target_df[column].nunique()

                elif action == "normalize_text":
                    pre_nulls = target_df[column].isna().sum()
                    pre_unique = target_df[column].nunique()
                    target_df[column] = (
                        target_df[column]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )
                    original_series = target_df[column].copy()

                    target_df[column] = (
                        target_df[column]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )
                    rows_affected = (original_series != target_df[column]).sum()
                    post_nulls = target_df[column].isna().sum()
                    post_unique = target_df[column].nunique()

                else:
                    raise ValueError(f"Unsupported action: {action}")
                
                after_dtype = str(target_df[column].dtype)

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

        if dry_run:
            print("Dry run complete; no changes were written to the original dataframe.")
        else:
            self.df = target_df

    def save_outputs(self, cleaned_path="cleaned_data.csv", log_path="execution_logs.json"):
        self.df.to_csv(cleaned_path, index=False)
        with open(log_path, "w") as f:
            json.dump(self.logs, f, indent=4)
        print("Execution complete.")
        print(f"Cleaned data saved to {cleaned_path}")
        print(f"Logs saved to {log_path}")

if __name__ == "__main__":
    import sys
    data_path = sys.argv[1] if len(sys.argv) > 1 else "sample_data/test.csv"

    executor = Executor(data_path)
    executor.load()
    executor.apply_rules()
    executor.save_outputs()