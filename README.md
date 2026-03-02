# Data Repair Toolkit – Profiler

A sophisticated data diagnostic tool that analyzes datasets and reveals exactly what needs cleaning—without the generic automation trap.

---

## 🚀 Try It Now (Free)

### [Click Here to Profile Your Dataset](https://datarepairtoolkit-profile-5000-rows.streamlit.app)

Upload your CSV or XLSX file (first 5,000 rows), get instant diagnostics:
- Detailed column analysis
- Data quality scoring
- Format variation detection
- Missing data patterns
- Pattern-based role inference

**Download results as JSON + PDF** – use them for your own cleaning or hire me to do it custom.

---

## Why This Tool?

Most data cleaning is generic: strip whitespace, fill NAs, standardize formats. **Boring. Ineffective.**

My approach is *data-aware*:

1. **I profile your data** using this tool
2. **I look for YOUR specific problems** – not cookie-cutter issues
3. **I write custom cleaning functions** based on what I find
4. **You get tailored solutions** that actually fit your business

This repo is my diagnostic engine. The profiler reads your data and tells me:
- Are there 3 different date formats in that column? (Yes → custom parser)
- Is the "Email" column actually 73% garbage? (Yes → validation rules)
- Are names duplicated with typos? (Yes → fuzzy matching)

**That intelligence drives the custom work.**

---

## What Gets Analyzed

For each column, the profiler detects:

| Metric | Detects |
|--------|---------|
| **Type Detection** | numeric, date, email, phone, URL ratios |
| **Role Inference** | primary_key, identifier, event_date, categorical, numeric_measure, free_text (with confidence) |
| **Quality** | missing %, uniqueness, cardinality |
| **Patterns** | multiple formats (e.g., 3 different date formats) |
| **Duplicates** | exact duplicate ratio per column |
| **Frequencies** | top values and percentages |
| **Issues** | whitespace problems, type inconsistencies, outliers |

---

## Example: What You'll See

```json
{
  "Join_Date": {
    "inferred_role": "event_date",
    "role_confidence": 0.9,
    "missing_pct": 0.0,
    "patterns_detected": {
      "pattern_count": 3,
      "patterns": [
        {"pattern": "LL/LL/LLLL", "example": "01/02/2024"},
        {"pattern": "LLLL-LL-LL", "example": "2024-02-01"},
        {"pattern": "LL-LL-LL", "example": "03-12-2023"}
      ]
    },
    "duplicate_ratio": 0.18,
    "top_values": [
      {"value": "2024-02-01", "count": 2, "percentage": 18.2}
    ]
  }
}
```

This single column profile tells me **everything I need to know** to write effective cleaning logic.

---

## Use Cases

- **Data audit** – What's actually wrong with my dataset?
- **DIY cleaning** – Download the profile, clean it yourself
- **Proof of analysis** – Show stakeholders you understand the data
- **Hiring me** – Use the profile to specify custom cleaning needs

---

## Local Installation

Want to run it locally?

```bash
pip install -r requirements.txt
python main.py path/to/your/data.csv
```

**Output:**
- `output/client_data_profile.json` – Structured diagnostics
- `output/profile_report.pdf` – Human-readable analysis

---

## For Businesses: Custom Data Cleaning

If you want **production-grade data cleaning** tailored to your dataset:

### [Hire Me on Fiverr →](https://fiverr.com/ireri_data_lab)

**I offer:**
- ✅ Full dataset profiling (no row limits)
- ✅ Custom cleaning function development
- ✅ Format standardization & normalization
- ✅ Duplicate detection & resolution
- ✅ Data quality validation
- ✅ Before/after metrics & impact report

**Process:**
1. You upload your dataset
2. I profile it using this tool
3. I identify specific cleaning needs
4. I write & apply custom solutions
5. You receive cleaned data + documentation

---

## Technical Details

- **Python:** 3.8+
- **Dependencies:** pandas, openpyxl, reportlab, streamlit
- **Processing:** First 5,000 rows (free tier)

---

## About

Built as a data diagnostic and positioning tool for professional data cleaning services. 

**The philosophy:** *Analyze first, understand the problem, then solve it custom. Not the other way around.*

---

## License

MIT

