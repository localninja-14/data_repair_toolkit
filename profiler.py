import pandas as pd
import json
import re
import os
from typing import Any, List, Dict, Tuple
from collections import Counter

class Profiler:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.profile = {}
        self.report_summary = []

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
        
        # NEW: Role inference
        role, confidence = self._infer_role(col, series, numeric_ratio, date_ratio, email_ratio, phone_ratio, unique_count)
        
        # NEW: Frequency distribution (top 10 values)
        frequencies = self._get_frequencies(non_null, top_n=10)
        
        # NEW: Pattern detection
        patterns = self._detect_patterns(non_null)
        
        # NEW: Duplicate detection
        duplicates = self._detect_duplicates(non_null)
        
        # NEW: Whitespace issues hint
        whitespace_issue = self._has_whitespace_issues(non_null)
        
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
            "inferred_role": role,
            "role_confidence": float(confidence),
            "top_values": frequencies,
            "patterns_detected": patterns,
            "duplicate_ratio": duplicates.get("exact_duplicate_ratio", 0.0),
            "whitespace_issue": whitespace_issue,
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

    def _infer_role(self, col: str, series: pd.Series, numeric_ratio: float, date_ratio: float, 
                    email_ratio: float, phone_ratio: float, unique_count: int) -> Tuple[str, float]:
        """Infer the likely role/type of a column based on statistics."""
        total = len(series)
        cardinality_ratio = unique_count / total if total > 0 else 0
        
        # Check for primary key (high cardinality, mostly numeric or strings)
        if cardinality_ratio > 0.9 and unique_count > 10:
            return "primary_key", 0.95
        
        # Check for identifier (high uniqueness but fewer than primary_key)
        if cardinality_ratio > 0.7 and unique_count > 5:
            if numeric_ratio > 0.8:
                return "identifier", 0.85
            else:
                return "identifier", 0.75
        
        # Check for event_date or temporal column
        if date_ratio > 0.8:
            return "event_date", 0.9
        
        # Check for email
        if email_ratio > 0.8:
            return "email", 0.95
        
        # Check for phone
        if phone_ratio > 0.8:
            return "phone", 0.85
        
        # Check for person_name (lower cardinality object, mixed case, contains duplicates)
        if series.dtype == 'object' and cardinality_ratio < 0.8 and cardinality_ratio > 0.3:
            return "person_name", 0.7
        
        # Check for categorical (low cardinality, few unique values)
        if unique_count < 20 and cardinality_ratio < 0.3:
            return "categorical", 0.85
        
        # Check for numeric_measure
        if numeric_ratio > 0.8:
            return "numeric_measure", 0.8
        
        # Default to free_text for object columns
        if series.dtype == 'object':
            return "free_text", 0.5
        
        return "unknown", 0.3

    def _get_frequencies(self, series: pd.Series, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top N values and their frequencies."""
        if len(series) == 0:
            return []
        
        value_counts = series.value_counts().head(top_n)
        result = []
        for value, count in value_counts.items():
            result.append({
                "value": str(value),
                "count": int(count),
                "percentage": float(count / len(series) * 100)
            })
        return result

    def _detect_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Detect distinct patterns/formats within a column."""
        if len(series) == 0:
            return {"pattern_count": 0, "patterns": []}
        
        # Sample first 100 non-null values
        sample = series.head(100)
        patterns = set()
        examples = {}
        
        for val in sample:
            val_str = str(val)
            # Create a pattern mask: replace digits with D, letters with L, keep symbols
            pattern = re.sub(r'\d', 'D', val_str)
            pattern = re.sub(r'[a-zA-Z]', 'L', pattern)
            
            if pattern not in patterns:
                patterns.add(pattern)
                examples[pattern] = val_str
        
        result = {
            "pattern_count": len(patterns),
            "patterns": [
                {
                    "pattern": p,
                    "example": examples[p]
                }
                for p in sorted(patterns)[:5]  # Return up to 5 patterns
            ]
        }
        return result

    def _detect_duplicates(self, series: pd.Series) -> Dict[str, Any]:
        """Detect exact and potential fuzzy duplicates."""
        if len(series) == 0:
            return {"exact_duplicate_ratio": 0.0}
        
        total = len(series)
        exact_duplicates = series.duplicated().sum()
        exact_duplicate_ratio = exact_duplicates / total if total > 0 else 0
        
        return {
            "exact_duplicate_ratio": float(exact_duplicate_ratio),
            "exact_duplicate_count": int(exact_duplicates),
        }

    def _has_whitespace_issues(self, series: pd.Series) -> bool:
        """Check if there are leading/trailing whitespace issues."""
        if series.dtype != 'object' or len(series) == 0:
            return False
        
        sample = series.head(100)
        for val in sample:
            val_str = str(val)
            if val_str != val_str.strip():
                return True
        return False

    def save_outputs(self, json_path: str = "output/client_data_profile.json", 
                    pdf_path: str = "output/profile_report.pdf"):
        """Save both JSON profile and PDF report."""
        os.makedirs(os.path.dirname(json_path) if os.path.dirname(json_path) else "output", exist_ok=True)
        
        # Save JSON
        with open(json_path, "w") as f:
            json.dump(self.profile, f, indent=4, default=str)
        print(f"JSON profile saved to {json_path}")
        
        # Generate and save PDF
        try:
            self._generate_pdf_report(pdf_path)
            print(f"PDF report saved to {pdf_path}")
        except ImportError:
            print("reportlab not installed; PDF report will not be generated.")
        except Exception as e:
            print(f"Warning: could not generate PDF report: {e}")

    def _generate_pdf_report(self, pdf_path: str):
        """Generate a human-readable PDF report from the profile."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
        except ImportError:
            raise ImportError("reportlab is required to generate PDF reports")
        
        os.makedirs(os.path.dirname(pdf_path) if os.path.dirname(pdf_path) else ".", exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
        )
        story.append(Paragraph("Data Quality Profile Report", title_style))
        
        # Summary
        story.append(Paragraph("<b>Dataset Overview</b>", styles['Heading2']))
        total_rows = len(self.df) if self.df is not None else 0
        total_cols = len(self.profile)
        summary_text = f"<b>Dimensions:</b> {total_rows} rows × {total_cols} columns<br/>"
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Per-column profiles
        story.append(Paragraph("<b>Column Profiles</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2 * inch))
        
        for col, metrics in self.profile.items():
            # Column heading
            col_text = (
                f"<b>{col}</b> ({metrics.get('inferred_role', 'unknown')}) "
                f"[confidence: {metrics.get('role_confidence', 0):.0%}]"
            )
            story.append(Paragraph(col_text, styles['Heading3']))
            
            # Column details
            details = []
            details.append(f"<b>Type:</b> {metrics.get('dtype', 'unknown')}")
            details.append(f"<b>Completeness:</b> {(1 - metrics.get('missing_pct', 0)):.1%}")
            details.append(f"<b>Unique values:</b> {metrics.get('unique_count', 0)} ({metrics.get('cardinality_ratio', 0):.1%})")
            
            if metrics.get('duplicate_ratio', 0) > 0.01:
                details.append(f"<b>⚠ Duplicate ratio:</b> {metrics.get('duplicate_ratio', 0):.1%}")
            
            if metrics.get('whitespace_issue', False):
                details.append(f"<b>⚠ Whitespace issues detected</b>")
            
            if metrics.get('patterns_detected', {}).get('pattern_count', 0) > 1:
                pattern_count = metrics['patterns_detected']['pattern_count']
                details.append(f"<b>⚠ Multiple formats detected:</b> {pattern_count} distinct patterns")
            
            if metrics.get('missing_pct', 0) > 0.1:
                details.append(f"<b>⚠ High missing data:</b> {metrics['missing_pct']:.1%}")
            
            # Top values
            top_vals = metrics.get('top_values', [])
            if top_vals:
                top_vals_str = ", ".join([f"{v['value']} ({v['percentage']:.0f}%)" for v in top_vals[:5]])
                details.append(f"<b>Top values:</b> {top_vals_str}")
            
            details_text = "<br/>".join(details)
            story.append(Paragraph(details_text, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        story.append(PageBreak())
        story.append(Paragraph("<b>Recommended Cleaning Actions</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2 * inch))
        
        actions = []
        for col, metrics in self.profile.items():
            col_actions = []
            
            if metrics.get('missing_pct', 0) > 0.1:
                col_actions.append(f"Handle {metrics['missing_pct']:.0%} missing values in <b>{col}</b>")
            
            if metrics.get('whitespace_issue', False):
                col_actions.append(f"Strip leading/trailing whitespace from <b>{col}</b>")
            
            if metrics.get('patterns_detected', {}).get('pattern_count', 0) > 1:
                col_actions.append(f"Standardise multiple date/format variations in <b>{col}</b>")
            
            if metrics.get('duplicate_ratio', 0) > 0.01:
                col_actions.append(f"Investigate and resolve duplicates in <b>{col}</b> ({metrics['duplicate_ratio']:.1%})")
            
            if metrics.get('non_ascii_ratio', 0) > 0.05:
                col_actions.append(f"Normalise non-ASCII characters in <b>{col}</b>")
            
            actions.extend(col_actions)
        
        if actions:
            for action in actions:
                story.append(Paragraph(f"• {action}", styles['Normal']))
        else:
            story.append(Paragraph("No major issues detected.", styles['Normal']))
        
        # Build PDF
        doc.build(story)

    def save_profile(self, path="output/data_profile.json"):
        """Legacy method for backward compatibility."""
        self.save_outputs(json_path=path)