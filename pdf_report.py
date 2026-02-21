from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf_report(summary, output_path, input_file, cleaning_summary):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DATA CLEANING REPORT")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"File processed: {input_file}")
    y -= 25

    for key, value in summary.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20

    y -= 10

    if cleaning_summary:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Cleaning Summary")
        y -= 25
        c.setFont("Helvetica", 12)
        for key, value in cleaning_summary.items():
            c.drawString(50, y, f"{key}: {value}")
            y -= 20

    y -= 10
    c.drawString(50, y-10, "Processing Completed Successfully.")
    c.save()