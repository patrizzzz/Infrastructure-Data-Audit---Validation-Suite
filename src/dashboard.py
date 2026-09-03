import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
import streamlit as st
from src.data_loader import load_dataset
from src.profiler import DataProfiler
from src.validator import DataValidator
from src.cleaner import DataCleaner
from src.quality_score import DataQualityScorer
from src.db_manager import DatabaseManager
from src.synthetic_generator import generate_dirty_sample

st.set_page_config(
    page_title="DPWH Infrastructure Data Audit Suite",
    page_icon="🌉",
    layout="wide"
)

st.title("🌉 Philippine Infrastructure Data Audit & Validation Suite")
st.markdown("##### *An Enterprise Data Quality Engineering & Geospatial Analytics Platform for DPWH Infrastructure Datasets*")

st.sidebar.image("https://img.icons8.com/color/96/bridge.png", width=70)
st.sidebar.title(" Audit Controls & Portfolio")
st.sidebar.markdown("---")

data_source = st.sidebar.radio(
    "Select Dataset Source:",
    [
        "Official DPWH 2021 National Bridges (8,496 records)",
        "Synthetic Benchmark Dirty Dataset (200 records with anomalies)",
        "Upload Custom CSV Dataset"
    ]
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_RAW_PATH = os.path.join(ROOT_DIR, "data", "raw", "national_bridges_2021.csv")
DEFAULT_SYNTH_PATH = os.path.join(ROOT_DIR, "data", "test", "dirty_bridges_sample.csv")

target_file_path = None

if data_source == "Official DPWH 2021 National Bridges (8,496 records)":
    if os.path.exists(DEFAULT_RAW_PATH):
        target_file_path = DEFAULT_RAW_PATH
    else:
        st.warning("Raw DPWH file not found locally. Falling back to synthetic benchmark dataset.")
        if not os.path.exists(DEFAULT_SYNTH_PATH):
            generate_dirty_sample(200, DEFAULT_SYNTH_PATH)
        target_file_path = DEFAULT_SYNTH_PATH

elif data_source == "Synthetic Benchmark Dirty Dataset (200 records with anomalies)":
    if not os.path.exists(DEFAULT_SYNTH_PATH):
        generate_dirty_sample(200, DEFAULT_SYNTH_PATH)
    target_file_path = DEFAULT_SYNTH_PATH

elif data_source == "Upload Custom CSV Dataset":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getvalue())
            target_file_path = tmp.name
    else:
        st.info(" Please upload a CSV file in the sidebar to run the audit engine.")
        if os.path.exists(DEFAULT_RAW_PATH):
            target_file_path = DEFAULT_RAW_PATH
        else:
            if not os.path.exists(DEFAULT_SYNTH_PATH):
                generate_dirty_sample(200, DEFAULT_SYNTH_PATH)
            target_file_path = DEFAULT_SYNTH_PATH

@st.cache_data
def process_audit_pipeline(file_path: str):
    df_raw = load_dataset(file_path)
    profiler = DataProfiler(df_raw)
    prof_summary = profiler.profile()
    
    validator = DataValidator(df_raw)
    issues_df, val_metrics = validator.validate()
    
    cleaner = DataCleaner(df_raw, issues_df)
    clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()
    
    scorer = DataQualityScorer(clean_df, issues_df)
    overall_score, grade, dim_scores = scorer.calculate_scores()
    
    db_mgr = DatabaseManager()
    db_mgr.ingest_audit_data(clean_df, quarantine_df, issues_df, audit_log_df)
    
    return df_raw, prof_summary, clean_df, quarantine_df, issues_df, audit_log_df, val_metrics, overall_score, grade, dim_scores

try:
    with st.spinner("Executing Data Profiling, Multi-Dimensional Validation & Cleaning Engine..."):
        df_raw, prof_summary, clean_df, quarantine_df, issues_df, audit_log_df, val_metrics, overall_score, grade, dim_scores = process_audit_pipeline(target_file_path)

    st.markdown("---")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    
    grade_color = "#10b981" if grade in ["A", "B"] else ("#f59e0b" if grade == "C" else "#ef4444")
    m1.metric("Overall Data Quality Score", f"{overall_score}%", f"Grade {grade}")
    m2.metric("Total Records Evaluated", f"{len(df_raw):,}")
    m3.metric("Clean Valid Records", f"{len(clean_df):,}")
    m4.metric("Quarantined Records", f"{len(quarantine_df):,}")
    m5.metric("Total Issues Detected", f"{len(issues_df):,}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Export Portfolio Artifacts")
    
    st.sidebar.download_button(
        "Download Clean Dataset (CSV)",
        data=clean_df.to_csv(index=False).encode('utf-8'),
        file_name="clean_infrastructure.csv",
        mime="text/csv"
    )
    
    st.sidebar.download_button(
        "Download Quarantined Records (CSV)",
        data=quarantine_df.to_csv(index=False).encode('utf-8'),
        file_name="quarantined_records.csv",
        mime="text/csv"
    )

    st.sidebar.download_button(
        "Download Audit Trail Log (CSV)",
        data=audit_log_df.to_csv(index=False).encode('utf-8'),
        file_name="data_audit_log.csv",
        mime="text/csv"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data Quality Scorecard",
        "🗺️ Geospatial & Structural Analytics",
        "⚠️ Quarantine & Audit Trail",
        "🔍 SQL Analytics Console",
        "ℹ️ Portfolio & Methodology"
    ])

    with tab1:
        st.subheader("Data Quality Dimensions Breakdown")
        col_chart, col_stats = st.columns([3, 2])
        
        with col_chart:
            dim_df = pd.DataFrame(list(dim_scores.items()), columns=["Dimension", "Score (%)"])
            st.bar_chart(dim_df.set_index("Dimension"))
            
        with col_stats:
            st.markdown("#### Profiling Summary")
            st.write(f"- **Total Rows:** {prof_summary['dataset_shape']['rows']:,}")
            st.write(f"- **Total Columns:** {prof_summary['dataset_shape']['columns']}")
            st.write(f"- **Overall Missing Cells:** {prof_summary['overall_missing_cells']:,} ({prof_summary['overall_missing_pct']}%)")
            st.write(f"- **Duplicate Primary Keys:** {prof_summary['bridge_id_duplicates']}")

        st.markdown("---")
        st.subheader("Validation Issues Breakdown by Severity")
        if not issues_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                sev_counts = issues_df["severity"].value_counts().reset_index()
                sev_counts.columns = ["Severity Level", "Issue Count"]
                st.dataframe(sev_counts, use_container_width=True)
            with c2:
                code_counts = issues_df["issue_code"].value_counts().reset_index()
                code_counts.columns = ["Issue Code", "Count"]
                st.dataframe(code_counts, use_container_width=True)

    with tab2:
        st.subheader("Philippine National Bridge Spatial Map & Regional Analytics")
        
        if "REGION" in clean_df.columns:
            all_regions = ["All Regions"] + sorted(list(clean_df["REGION"].dropna().unique()))
            selected_region = st.selectbox("Filter Analytics by Region:", all_regions)
            
            filtered_df = clean_df if selected_region == "All Regions" else clean_df[clean_df["REGION"] == selected_region]
        else:
            filtered_df = clean_df

        if "LATITUDE" in filtered_df.columns and "LONGITUDE" in filtered_df.columns:
            map_data = filtered_df[["LATITUDE", "LONGITUDE"]].dropna().rename(columns={"LATITUDE": "lat", "LONGITUDE": "lon"})
            st.markdown(f"Displaying **{len(map_data):,}** geotagged bridges on spatial map:")
            st.map(map_data)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Bridge Physical Condition Ratings")
            if "CONDITION" in filtered_df.columns:
                st.dataframe(filtered_df["CONDITION"].value_counts().reset_index(), use_container_width=True)
        with col_b:
            st.markdown("#### Primary Structural Types")
            if "BR_TYPE1" in filtered_df.columns:
                st.dataframe(filtered_df["BR_TYPE1"].value_counts().reset_index(), use_container_width=True)

    with tab3:
        st.subheader("Quarantine Pattern & Audit Trail Explorer")
        st.markdown("Records with critical defects (e.g. missing primary keys, invalid coordinates, impossible measurements) are isolated into quarantine:")
        
        st.markdown(f"#### Quarantined Records ({len(quarantine_df):,} rows)")
        st.dataframe(quarantine_df.head(100), use_container_width=True)

        st.markdown("---")
        st.markdown(f"#### Granular Data Audit Trail Log ({len(audit_log_df):,} actions)")
        st.dataframe(audit_log_df.head(100), use_container_width=True)

    with tab4:
        st.subheader("Interactive SQLite Query Console")
        st.markdown("Run relational SQL queries directly over `clean_bridges`, `quarantined_bridges`, and `validation_issues`:")
        
        default_query = "SELECT REGION, COUNT(BRIDGE_ID) as Total_Bridges, ROUND(AVG(BR_LENGTH), 2) as Avg_Length_Meters FROM clean_bridges GROUP BY REGION ORDER BY Total_Bridges DESC;"
        sql_input = st.text_area("SQL Query Editor:", default_query, height=120)
        
        if st.button("Execute SQL Query"):
            db_mgr = DatabaseManager()
            res_df = db_mgr.run_query(sql_input)
            st.dataframe(res_df, use_container_width=True)

    with tab5:
        st.subheader("Project Overview & Engineering Methodology")
        st.markdown("""
        ### Executive Overview
        Public infrastructure organizations depend heavily on high-integrity inventory data for capital project planning, safety maintenance, disaster resilience, and budget allocations.
        
        This **Data Audit & Validation Suite** provides a production-grade data quality pipeline designed specifically for Philippine infrastructure datasets.
        
        ### Architecture & Data Quality Dimensions
        1. **Completeness (25%)**: Measures missingness across mandatory fields (Bridge ID, Name, Region, Coordinates).
        2. **Validity (30%)**: Evaluates physical constraints, regex patterns, and Philippine spatial bounding box (Lat 4.5°–21.5°N, Long 116°–127°E).
        3. **Uniqueness (20%)**: Checks for duplicate primary keys and duplicate tuples.
        4. **Consistency (15%)**: Asserts relational co-dependencies (e.g. Length > 0, Span count >= 1).
        5. **Timeliness (10%)**: Validates construction year bounds (1800–2026).
        
        ---
        **Developed with:** Python | Pandas | NumPy | Streamlit | SQLite | Matplotlib | Seaborn | Pytest
        """)

except Exception as e:
    st.error(f"Error executing dashboard pipeline: {e}")
