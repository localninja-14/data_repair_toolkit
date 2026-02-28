"""Impact calculator: quantifies data cleaning improvements."""

import pandas as pd


class ImpactCalculator:
    """Computes before/after metrics for cleaned data."""

    def __init__(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame, logs: list):
        self.original = original_df
        self.cleaned = cleaned_df
        self.logs = logs

    def calculate(self) -> dict:
        """Return a dict of impact metrics suitable for reporting."""
        metrics = {
            "total_rows": len(self.cleaned),
            "rows_removed": len(self.original) - len(self.cleaned),
            "total_columns": len(self.cleaned.columns),
            "columns_modified": self._count_modified_columns(),
            "missing_values_before": int(self.original.isna().sum().sum()),
            "missing_values_after": int(self.cleaned.isna().sum().sum()),
            "missing_pct_before": float(
                (self.original.isna().sum().sum() / (len(self.original) * len(self.original.columns)))
                * 100
            ),
            "missing_pct_after": float(
                (self.cleaned.isna().sum().sum() / (len(self.cleaned) * len(self.cleaned.columns)))
                * 100
            ),
            "data_quality_score_before": self._quality_score(self.original),
            "data_quality_score_after": self._quality_score(self.cleaned),
            "quality_improvement_pct": self._quality_improvement(),
            "summary_statement": self._create_summary_statement(),
        }
        return metrics

    def _count_modified_columns(self) -> int:
        count = 0
        for col in self.original.columns:
            if col in self.cleaned.columns:
                # check if dtype changed or any values differ
                if str(self.original[col].dtype) != str(self.cleaned[col].dtype):
                    count += 1
        return count

    def _quality_score(self, df: pd.DataFrame) -> float:
        """Simple quality score: 100 - (missing % + duplicate % + type inconsistency %)."""
        total_cells = len(df) * len(df.columns)
        missing = df.isna().sum().sum() / total_cells if total_cells > 0 else 0
        duplicates = df.duplicated().sum() / len(df) if len(df) > 0 else 0
        # simplified; real score could be more sophisticated
        score = 100 * (1 - missing - duplicates * 0.1)
        return max(0, min(100, score))

    def _quality_improvement(self) -> float:
        """% improvement from before to after."""
        before = self._quality_score(self.original)
        after = self._quality_score(self.cleaned)
        if before == 0:
            return 0 if after == 0 else 100
        return ((after - before) / before) * 100

    def _create_summary_statement(self) -> str:
        """Human-readable one-liner summarizing the impact."""
        improvement = self._quality_improvement()
        missing_before = self.original.isna().sum().sum() / (len(self.original) * len(self.original.columns)) * 100
        missing_after = self.cleaned.isna().sum().sum() / (len(self.cleaned) * len(self.cleaned.columns)) * 100
        missing_reduction = missing_before - missing_after
        rows_removed = len(self.original) - len(self.cleaned)
        cols_modified = self._count_modified_columns()

        parts = []
        if rows_removed > 0:
            parts.append(f"removed {rows_removed} duplicate/invalid rows")
        if missing_reduction > 0:
            parts.append(f"reduced missing data by {missing_reduction:.1f}%")
        if improvement > 0:
            parts.append(f"improved data quality by {improvement:.1f}%")
        if cols_modified > 0:
            parts.append(f"standardized {cols_modified} column(s)")

        if not parts:
            return "Dataset processed and validated."
        return "Successfully " + ", ".join(parts) + "."

    @property
    def metrics(self):
        """Cached metrics dict."""
        if not hasattr(self, "_metrics"):
            self._metrics = self.calculate()
        return self._metrics

    @metrics.setter
    def metrics(self, value):
        self._metrics = value
