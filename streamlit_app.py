import streamlit as st
import pandas as pd
import json
import os
import tempfile
import time
from io import BytesIO
from profiler import Profiler

# ============================================================
# ANTI-ABUSE CONFIGURATION
# ============================================================
MAX_FILE_SIZE_MB = 10
MAX_ROWS = 5000
MAX_COLUMNS = 150
MAX_PROFILE_SECONDS = 60
MAX_REQUESTS_PER_HOUR = 50

# ============================================================
# SESSION STATE & RATE LIMITING
# ============================================================
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = time.time()

# Check rate limit
def check_rate_limit():
    elapsed = time.time() - st.session_state.last_request_time
    if elapsed < 3600:  # Within an hour
        if st.session_state.request_count >= MAX_REQUESTS_PER_HOUR:
            st.error(f"⛔ Rate limit exceeded. Max {MAX_REQUESTS_PER_HOUR} analyses per hour.")
            return False
    else:
        # Reset if hour has passed
        st.session_state.request_count = 0
        st.session_state.last_request_time = time.time()
    return True

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Data Profiler", page_icon="📊", layout="wide")

st.title("📊 DATA PROFILING")
st.markdown("""
Analyze your dataset instantly. See what's broken, what patterns exist, and get actionable insights.

**Free tier:** First 5,000 rows | **Full dataset analysis:** [Hire me on Fiverr](https://fiverr.com/users/ireri_data_lab)
""")

# Sidebar info
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool profiles your data and identifies:
- Data types & quality issues
- Column roles (ID, name, date, etc.)
- Multiple format variations
- Duplicate ratios
- Missing data patterns

Perfect for understanding messy datasets before cleaning.
""")

st.sidebar.markdown("### Limits (Free Tier)")
st.sidebar.markdown(f"""
- File size: {MAX_FILE_SIZE_MB}MB max
- Rows: {MAX_ROWS:,} max
- Columns: {MAX_COLUMNS} max
- Timeout: {MAX_PROFILE_SECONDS}s
- Rate: {MAX_REQUESTS_PER_HOUR}/hour

Need more? Hire me for custom solutions.
""")

# ============================================================
# FILE UPLOAD & VALIDATION
# ============================================================
uploaded_file = st.file_uploader("Upload your CSV or XLSX file", type=["csv", "xlsx"])

if uploaded_file is not None:
    # FILE SIZE CHECK
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ File too large ({file_size_mb:.1f}MB). Maximum: {MAX_FILE_SIZE_MB}MB")
        st.stop()
    
    # LOAD WITH ERROR HANDLING
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(
                uploaded_file,
                engine='python',
                on_bad_lines='skip',
                nrows=MAX_ROWS
            )
        else:
            df = pd.read_excel(uploaded_file, nrows=MAX_ROWS)
    except Exception as e:
        st.error(f"❌ Could not read file: {str(e)[:100]}")
        st.stop()
    
    # COLUMN CHECK
    if df.shape[1] > MAX_COLUMNS:
        st.error(f"❌ Too many columns ({df.shape[1]}). Maximum: {MAX_COLUMNS}")
        st.stop()
    
    # ROW NOTIFICATION
    st.success(f"✓ Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    if df.shape[0] == MAX_ROWS:
        st.info(f"📌 Showing first {MAX_ROWS:,} rows (free tier limit). For full dataset analysis, hire me for custom cleaning.")
    
    # PRIVACY WARNING
    st.warning("🔒 **Privacy Notice:** Your data is temporarily processed and automatically deleted. We do not store or log your data.")
    
    # ============================================================
    # PROFILING WITH PROTECTIONS
    # ============================================================
    if st.button("🔍 Profile Dataset", type="primary"):
        # RATE LIMIT CHECK
        if not check_rate_limit():
            st.stop()
        
        # START TIMEOUT TRACKING
        profile_start_time = time.time()
        
        with st.spinner("Analyzing your data..."):
            try:
                # Create temporary directory (auto-cleanup)
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_path = os.path.join(tmpdir, "temp_data.csv")
                    
                    # Save to temp
                    try:
                        df.to_csv(temp_path, index=False)
                    except Exception as e:
                        st.error(f"❌ Could not process data: {str(e)[:100]}")
                        st.stop()
                    
                    # CHECK TIMEOUT BEFORE PROFILING
                    if time.time() - profile_start_time > MAX_PROFILE_SECONDS:
                        st.error(f"⏱️ Analysis timed out. Try with fewer rows or columns.")
                        st.stop()
                    
                    # RUN PROFILER
                    try:
                        profiler = Profiler(temp_path)
                        profiler.load()
                        profiler.analyze()
                    except Exception as e:
                        st.error(f"❌ Profiling failed: {str(e)[:100]}")
                        st.stop()
                    
                    # CHECK TIMEOUT AFTER PROFILING
                    if time.time() - profile_start_time > MAX_PROFILE_SECONDS:
                        st.error(f"⏱️ Analysis timed out during report generation.")
                        st.stop()
                    
                    # GENERATE OUTPUTS
                    try:
                        json_path = os.path.join(tmpdir, "profile.json")
                        pdf_path = os.path.join(tmpdir, "report.pdf")
                        profiler.save_outputs(json_path=json_path, pdf_path=pdf_path)
                    except Exception as e:
                        st.error(f"❌ Could not generate reports: {str(e)[:100]}")
                        st.stop()
                    
                    # READ OUTPUTS
                    try:
                        with open(json_path, 'r') as f:
                            profile_json = json.load(f)
                        
                        with open(pdf_path, 'rb') as f:
                            pdf_bytes = f.read()
                    except Exception as e:
                        st.error(f"❌ Could not read outputs: {str(e)[:100]}")
                        st.stop()
                    
                    # ============================================================
                    # DISPLAY RESULTS IN TABS
                    # ============================================================
                    tab1, tab2, tab3 = st.tabs(["📈 Summary", "🔍 Details", "📥 Download"])
                    
                    # TAB 1: SUMMARY
                    with tab1:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Rows", f"{len(df):,}")
                        with col2:
                            st.metric("Columns", len(profile_json))
                        with col3:
                            missing_pct = sum(col['missing_pct'] for col in profile_json.values()) / len(profile_json) if profile_json else 0
                            st.metric("Avg Missing %", f"{missing_pct:.1f}%")
                        with col4:
                            roles = [col.get('inferred_role', 'unknown') for col in profile_json.values()]
                            st.metric("Unique Roles", len(set(roles)))
                        
                        st.markdown("### Column Profiles")
                        for col_name, metrics in profile_json.items():
                            with st.expander(f"**{col_name}** ({metrics.get('inferred_role', 'unknown')})"):
                                col_a, col_b = st.columns(2)
                                
                                with col_a:
                                    st.write(f"**Type:** {metrics['dtype']}")
                                    st.write(f"**Completeness:** {(1 - metrics['missing_pct'])*100:.1f}%")
                                    st.write(f"**Unique:** {metrics['unique_count']}")
                                    st.write(f"**Role Confidence:** {metrics['role_confidence']:.0%}")
                                
                                with col_b:
                                    if metrics.get('duplicate_ratio', 0) > 0:
                                        st.write(f"**Duplicates:** {metrics['duplicate_ratio']:.1%}")
                                    if metrics.get('patterns_detected', {}).get('pattern_count', 0) > 1:
                                        st.write(f"**Patterns Detected:** {metrics['patterns_detected']['pattern_count']}")
                                    if metrics.get('whitespace_issue', False):
                                        st.write("⚠️ **Whitespace issues detected**")
                                
                                # Top values
                                if metrics.get('top_values'):
                                    st.write("**Top Values:**")
                                    for val in metrics['top_values'][:5]:
                                        st.write(f"  • {val['value']}: {val['count']}x ({val['percentage']:.0f}%)")
                    
                    # TAB 2: RAW JSON
                    with tab2:
                        st.json(profile_json)
                    
                    # TAB 3: DOWNLOADS
                    with tab3:
                        st.markdown("### Download Results")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            json_str = json.dumps(profile_json, indent=2, default=str)
                            st.download_button(
                                label="📄 Download JSON Profile",
                                data=json_str,
                                file_name="client_data_profile.json",
                                mime="application/json"
                            )
                        
                        with col2:
                            st.download_button(
                                label="📋 Download PDF Report",
                                data=pdf_bytes,
                                file_name="profile_report.pdf",
                                mime="application/pdf"
                            )
                        
                        st.markdown("---")
                        st.markdown("""
                        ### Next Steps
                        
                        **Free with this tool:**
                        - Dataset profiling & diagnostics
                        - Pattern & issue detection
                        - Data quality scoring
                        
                        **Custom cleaning (hire me):**
                        - Write tailored cleaning functions for your data
                        - Handle format variations, duplicates, missing values
                        - Full dataset processing (no row limits)
                        - Custom validation rules
                        
                        [View my Fiverr gig →](https://fiverr.com)
                        """)
                    
                    # UPDATE RATE LIMIT
                    st.session_state.request_count += 1
                    st.session_state.last_request_time = time.time()
            
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)[:100]}")

else:
    st.info("👆 Upload a CSV or XLSX file to get started")
    
    st.markdown("---")
    st.markdown("""
    ### Example: What You'll See
    
    The profiler analyzes each column and reveals:
    
    1. **Role Inference** – Is this a date? Name? ID? (with confidence)
    2. **Format Variations** – Found 3 different date formats? Detects it.
    3. **Duplicates & Missing** – Exact duplicate ratio, missing data %
    4. **Type Consistency** – How "clean" is the data in each column?
    5. **Frequency Distribution** – Most common values & percentages
    6. **Outliers** – Numeric anomalies detected
    
    All in JSON + PDF format, ready to guide custom cleaning.
    """)
