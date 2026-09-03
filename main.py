import os
import sys
import argparse
import subprocess
import pandas as pd

from src.data_loader import load_dataset
from src.profiler import DataProfiler
from src.validator import DataValidator
from src.cleaner import DataCleaner
from src.quality_score import DataQualityScorer
from src.db_manager import DatabaseManager
from src.report_generator import ReportGenerator
from src.synthetic_generator import generate_dirty_sample

def main():
    parser = argparse.ArgumentParser(description="Philippine Infrastructure Data Audit & Validation Suite")
    parser.add_argument("--dataset", type=str, default="data/raw/national_bridges_2021.csv", help="Path to CSV or GeoJSON dataset")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic dirty dataset for testing")
    parser.add_argument("--all", action="store_true", help="Run complete end-to-end data audit pipeline")
    parser.add_argument("--profile", action="store_true", help="Run data profiling")
    parser.add_argument("--validate", action="store_true", help="Run validation engine")
    parser.add_argument("--clean", action="store_true", help="Run data cleaner & quarantine handler")
    parser.add_argument("--score", action="store_true", help="Run quality score calculator")
    parser.add_argument("--report", action="store_true", help="Generate visual charts & executive HTML report")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive Streamlit dashboard")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        args.all = True

    if args.synthetic:
        synth_path = "data/test/dirty_bridges_sample.csv"
        print(f"[1/7] Generating synthetic dirty benchmark dataset -> {synth_path}")
        generate_dirty_sample(num_records=200, output_path=synth_path)
        args.dataset = synth_path

    if not os.path.exists(args.dataset):
        print(f"Error: Dataset not found at {args.dataset}. Run with --synthetic to generate sample data.")
        sys.exit(1)

    print(f"========================================================================")
    print(f"    PHILIPPINE INFRASTRUCTURE DATA AUDIT & VALIDATION SUITE")
    print(f"========================================================================")
    print(f"Loading Dataset: {args.dataset}")
    df_raw = load_dataset(args.dataset)
    print(f"Dataset Loaded: {len(df_raw):,} records, {len(df_raw.columns)} columns.\n")

    if args.all or args.profile:
        print("--- [Step 1] Data Profiling ---")
        profiler = DataProfiler(df_raw)
        prof_summary = profiler.profile()
        print(f"Shape: {prof_summary['dataset_shape']['rows']} rows x {prof_summary['dataset_shape']['columns']} cols")
        print(f"Overall Missing Cells: {prof_summary['overall_missing_cells']} ({prof_summary['overall_missing_pct']}%)")
        print(f"Duplicate Primary Keys (BRIDGE_ID): {prof_summary['bridge_id_duplicates']}\n")

    if args.all or args.validate:
        print("--- [Step 2] Validation Engine Execution ---")
        validator = DataValidator(df_raw)
        issues_df, val_metrics = validator.validate()
        print(f"Records Evaluated: {val_metrics['total_records_evaluated']:,}")
        print(f"Issues Detected: {val_metrics['total_issues_detected']:,}")
        print(f"Flagged Records: {val_metrics['flagged_records']:,}")
        print(f"Clean Records: {val_metrics['clean_records']:,}\n")

        os.makedirs("reports", exist_ok=True)
        issues_path = "reports/audit_report.csv"
        issues_df.to_csv(issues_path, index=False, encoding="utf-8")
        print(f"Saved detailed audit findings -> {issues_path}\n")

    if args.all or args.clean:
        print("--- [Step 3] Data Cleaning & Quarantine Isolation ---")
        if 'issues_df' not in locals():
            validator = DataValidator(df_raw)
            issues_df, val_metrics = validator.validate()

        cleaner = DataCleaner(df_raw, issues_df)
        clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()

        os.makedirs("data/processed", exist_ok=True)
        clean_path = "data/processed/clean_infrastructure.csv"
        quarantine_path = "data/processed/quarantined_records.csv"
        audit_log_path = "reports/data_audit_log.csv"

        clean_df.to_csv(clean_path, index=False, encoding="utf-8")
        quarantine_df.to_csv(quarantine_path, index=False, encoding="utf-8")
        audit_log_df.to_csv(audit_log_path, index=False, encoding="utf-8")

        print(f"Clean Records Saved -> {clean_path} ({len(clean_df):,} rows)")
        print(f"Quarantined Records Saved -> {quarantine_path} ({len(quarantine_df):,} rows)")
        print(f"Audit Trail Saved -> {audit_log_path} ({len(audit_log_df):,} actions)\n")

    if args.all or args.score:
        print("--- [Step 4] Composite Data Quality Scoring ---")
        if 'clean_df' not in locals():
            validator = DataValidator(df_raw)
            issues_df, val_metrics = validator.validate()
            cleaner = DataCleaner(df_raw, issues_df)
            clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()

        scorer = DataQualityScorer(clean_df, issues_df)
        overall_score, grade, dim_scores = scorer.calculate_scores()

        print(f"OVERALL DATA QUALITY SCORE: {overall_score}%")
        print(f"OVERALL DATA QUALITY GRADE: {grade}")
        print("Dimension Breakdown:")
        for dim, score in dim_scores.items():
            print(f"  - {dim:15s}: {score}%")
        print("")

        summary_df = pd.DataFrame([{
            "Overall_Score": overall_score,
            "Letter_Grade": grade,
            **dim_scores,
            "Total_Records": len(df_raw),
            "Clean_Records": len(clean_df),
            "Quarantined_Records": len(quarantine_df)
        }])
        summary_df.to_csv("reports/data_quality_summary.csv", index=False, encoding="utf-8")

    if args.all or args.report:
        print("--- [Step 5] SQLite DB Ingestion & Visual Reporting ---")
        if 'clean_df' not in locals():
            validator = DataValidator(df_raw)
            issues_df, val_metrics = validator.validate()
            cleaner = DataCleaner(df_raw, issues_df)
            clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()
            scorer = DataQualityScorer(clean_df, issues_df)
            overall_score, grade, dim_scores = scorer.calculate_scores()

        db_mgr = DatabaseManager()
        db_mgr.ingest_audit_data(clean_df, quarantine_df, issues_df, audit_log_df)
        print("Populated SQLite Database -> data/processed/infrastructure_audit.db")

        reporter = ReportGenerator()
        figures = reporter.generate_visualizations(clean_df, issues_df, dim_scores)
        print(f"Generated Visual Figures in -> reports/figures/")
        
        html_report = reporter.generate_html_report(overall_score, grade, dim_scores, val_metrics, issues_df)
        print(f"Generated Executive Audit Report -> {html_report}\n")

    if args.dashboard:
        print("--- Launching Streamlit Interactive Dashboard ---")
        subprocess.run(["streamlit", "run", "src/dashboard.py"])

    print("========================================================================")
    print("      DATA AUDIT & VALIDATION SUITE EXECUTION COMPLETED")
    print("========================================================================")

if __name__ == "__main__":
    main()
