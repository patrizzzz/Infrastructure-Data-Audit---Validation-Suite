import sys
import os
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

st.set_page_config(
    page_title="DPWH Infrastructure Data Audit Suite",
    page_icon="🌉",
    layout="wide"
)

st.title("🌉 Philippine Infrastructure Data Audit & Validation Suite")
st.markdown("### Executive Data Quality Dashboard - Department of Public Works and Highways (DPWH)")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "national_bridges_2021.csv")

@st.cache_data
def run_pipeline():
    df_raw = load_dataset(DATA_PATH)
    validator = DataValidator(df_raw)
    issues_df, val_metrics = validator.validate()
    
    cleaner = DataCleaner(df_raw, issues_df)
    clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()
    
    scorer = DataQualityScorer(clean_df, issues_df)
    overall_score, grade, dim_scores = scorer.calculate_scores()
    
    db_mgr = DatabaseManager()
    db_mgr.ingest_audit_data(clean_df, quarantine_df, issues_df, audit_log_df)
    
    return df_raw, clean_df, quarantine_df, issues_df, audit_log_df, val_metrics, overall_score, grade, dim_scores

try:
    df_raw, clean_df, quarantine_df, issues_df, audit_log_df, val_metrics, overall_score, grade, dim_scores = run_pipeline()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Overall DQ Score", f"{overall_score}%", f"Grade {grade}")
    col2.metric("Total Bridges Evaluated", f"{len(df_raw):,}")
    col3.metric("Clean Valid Records", f"{len(clean_df):,}")
    col4.metric("Quarantined Records", f"{len(quarantine_df):,}")
    col5.metric("Total Issues Flagged", f"{len(issues_df):,}")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Quality Scorecard", "🗺️ Geospatial & Inventory", "⚠️ Quarantine & Audit Log", "🔍 SQL Query Console"])
    
    with tab1:
        st.subheader("Data Quality Dimensions Breakdown")
        dim_df = pd.DataFrame(list(dim_scores.items()), columns=["Dimension", "Score (%)"])
        st.bar_chart(dim_df.set_index("Dimension"))
        
        st.markdown("#### Validation Issues by Severity")
        if not issues_df.empty:
            sev_df = issues_df["severity"].value_counts().reset_index()
            sev_df.columns = ["Severity", "Count"]
            st.dataframe(sev_df, use_container_width=True)
            
    with tab2:
        st.subheader("Geospatial & Infrastructure Inventory Distribution")
        
        region_filter = st.selectbox("Select Region", ["All Regions"] + list(clean_df["REGION"].dropna().unique()))
        
        filtered_df = clean_df if region_filter == "All Regions" else clean_df[clean_df["REGION"] == region_filter]
        
        if "LATITUDE" in filtered_df.columns and "LONGITUDE" in filtered_df.columns:
            map_data = filtered_df[["LATITUDE", "LONGITUDE"]].dropna().rename(columns={"LATITUDE": "lat", "LONGITUDE": "lon"})
            st.map(map_data)
            
        st.subheader("Bridge Physical Condition Summary")
        cond_counts = filtered_df["CONDITION"].value_counts().reset_index()
        cond_counts.columns = ["Condition Rating", "Number of Bridges"]
        st.dataframe(cond_counts, use_container_width=True)

    with tab3:
        st.subheader("Quarantined & Invalid Records Explorer")
        st.markdown("Records failing critical validation rules isolated from primary analytics pipeline:")
        st.dataframe(quarantine_df.head(50), use_container_width=True)
        
        st.subheader("Granular Data Audit Log")
        st.dataframe(audit_log_df.head(50), use_container_width=True)

    with tab4:
        st.subheader("Interactive SQL Analytics Console")
        query = st.text_area("Write SQL Query over 'clean_bridges', 'quarantined_bridges', or 'validation_issues':", 
                             "SELECT REGION, COUNT(*) as Total_Bridges, AVG(BR_LENGTH) as Avg_Length FROM clean_bridges GROUP BY REGION ORDER BY Total_Bridges DESC;")
        if st.button("Run Query"):
            db_mgr = DatabaseManager()
            result_df = db_mgr.run_query(query)
            st.dataframe(result_df, use_container_width=True)

except Exception as e:
    st.error(f"Error initializing dashboard: {e}")
