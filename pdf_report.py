try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    A4 = None
    canvas = None


def generate_pdf_report(profile: dict,
                        proposals: dict,
                        output_path: str,
                        input_file: str,
                        cleaning_summary: dict = None,
                        impact_metrics: dict = None,
                        review: bool = False):
    if canvas is None:
        print("reportlab not installed; PDF report will not be generated.")
        return
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 50

    # === EXECUTIVE SUMMARY (Page 1) ===
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, "DATA CLEANING REPORT")
    y -= 40

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"File: {input_file}")
    y -= 20

    if review:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, y, "[Dry Run / Review Mode]")
        y -= 25
    else:
        y -= 5

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "BUSINESS IMPACT")
    y -= 25

    if impact_metrics:
        c.setFont("Helvetica", 11)
        quality_before = impact_metrics.get("data_quality_score_before", 0)
        quality_after = impact_metrics.get("data_quality_score_after", 0)
        improvement = impact_metrics.get("quality_improvement_pct", 0)
        missing_before = impact_metrics.get("missing_pct_before", 0)
        missing_after = impact_metrics.get("missing_pct_after", 0)
        rows_removed = impact_metrics.get("rows_removed", 0)
        cols_modified = impact_metrics.get("columns_modified", 0)

        # key metrics in a readable layout
        metrics_text = [
            f"• Data Quality Score: {quality_before:.1f}% → {quality_after:.1f}% ({improvement:+.1f}%)",
            f"• Missing Data: {missing_before:.1f}% → {missing_after:.1f}%",
            f"• Invalid Rows Removed: {rows_removed}",
            f"• Columns Standardized: {cols_modified}",
            f"• Data Set Size: {impact_metrics.get('total_rows', 'N/A')} rows, {impact_metrics.get('total_columns', 'N/A')} columns",
        ]

        for line in metrics_text:
            c.drawString(50, y, line)
            y -= 18

        y -= 10
        c.setFont("Helvetica-Oblique", 11)
        summary = impact_metrics.get("summary_statement", "")
        c.drawString(50, y, summary)
        y -= 25

    # === PROFILE OVERVIEW ===
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "DATA PROFILE")
    y -= 25

    if profile:
        c.setFont("Helvetica", 9)
        for col, stats in profile.items():
            if y < 80:
                c.showPage()
                y = height - 50

            c.drawString(50, y, f"Column: {col}")
            y -= 12
            c.setFont("Helvetica", 8)

            # only show key stats to keep PDF compact
            key_stats = [
                ("Type", stats.get("dtype")),
                ("Missing", f"{stats.get('missing_pct', 0)*100:.1f}%"),
                ("Unique", stats.get("unique_count")),
            ]
            for key, val in key_stats:
                c.drawString(60, y, f"  {key}: {val}")
                y -= 10

            c.setFont("Helvetica", 9)
            y -= 5

    y -= 10

    # === PROPOSALS ===
    if proposals:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "CLEANING RULES APPLIED")
        y -= 25

        if y < 80:
            c.showPage()
            y = height - 50

        c.setFont("Helvetica", 9)
        for col, func in proposals.items():
            if y < 80:
                c.showPage()
                y = height - 50

            snippet = func.replace("\n", " ")[:120]
            c.drawString(50, y, f"• {col}: {snippet}...")
            y -= 12

    y -= 10

    # === FOOTER ===
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, "Data Repair Toolkit | Premium Data Cleaning as a Service")
    c.drawString(50, 15, f"Processed on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.save()

# add pandas import for timestamp in footer
import pandas as pd
