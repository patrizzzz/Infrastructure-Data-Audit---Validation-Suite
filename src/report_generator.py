import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Tuple

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

class ReportGenerator:
    """
    Reporting & Visualization Generator.
    Produces high-res analytical charts, CSV summaries, and executive HTML audit reports.
    """
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "..", "reports")
        self.figures_dir = os.path.join(self.output_dir, "figures")
        os.makedirs(self.figures_dir, exist_ok=True)

    def generate_visualizations(self, clean_df: pd.DataFrame, issues_df: pd.DataFrame, 
                                 dimension_scores: Dict[str, float]) -> Dict[str, str]:
        """
        Generates and saves publication-quality audit figures.
        Returns a dictionary of figure image paths.
        """
        image_paths = {}

        fig, ax = plt.subplots(figsize=(8, 5))
        dims = list(dimension_scores.keys())
        scores = list(dimension_scores.values())
        colors = ["#2b5c8f", "#d9534f", "#f0ad4e", "#5cb85c", "#0275d8"]
        
        bars = ax.bar(dims, scores, color=colors, width=0.55, edgecolor="black", alpha=0.85)
        ax.set_ylim(0, 110)
        ax.set_ylabel("Score (%)", fontsize=12, fontweight="bold")
        ax.set_title("Data Quality Dimensions Audit Scorecard", fontsize=14, fontweight="bold", pad=15)
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=11, fontweight="bold")
            
        fig_path1 = os.path.join(self.figures_dir, "dq_dimension_scores.png")
        plt.tight_layout()
        plt.savefig(fig_path1, dpi=300)
        plt.close()
        image_paths["dq_scores"] = fig_path1

        if not issues_df.empty and "severity" in issues_df.columns:
            fig, ax = plt.subplots(figsize=(6, 6))
            sev_counts = issues_df["severity"].value_counts()
            colors_sev = {"CRITICAL": "#d9534f", "HIGH": "#f0ad4e", "MEDIUM": "#5bc0de", "LOW": "#5cb85c"}
            pie_colors = [colors_sev.get(s, "#999999") for s in sev_counts.index]
            
            ax.pie(sev_counts.values, labels=sev_counts.index, autopct="%1.1f%%",
                   startangle=140, colors=pie_colors, wedgeprops={"edgecolor": "white", "linewidth": 2})
            ax.set_title("Validation Issue Breakdown by Severity", fontsize=13, fontweight="bold")
            
            fig_path2 = os.path.join(self.figures_dir, "issue_severity_distribution.png")
            plt.tight_layout()
            plt.savefig(fig_path2, dpi=300)
            plt.close()
            image_paths["severity_pie"] = fig_path2

        if "REGION" in clean_df.columns and "CONDITION" in clean_df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            ct = pd.crosstab(clean_df["REGION"], clean_df["CONDITION"])
            cond_order = [c for c in ["Good", "Fair", "Poor", "Bad"] if c in ct.columns]
            ct = ct[cond_order]
            
            ct.plot(kind="barh", stacked=True, ax=ax, colormap="viridis", edgecolor="black", alpha=0.85)
            ax.set_title("Bridge Physical Condition Rating by Region", fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel("Number of Bridges", fontsize=11, fontweight="bold")
            ax.set_ylabel("Region", fontsize=11, fontweight="bold")
            ax.legend(title="Condition Rating", bbox_to_anchor=(1.02, 1), loc="upper left")
            
            fig_path3 = os.path.join(self.figures_dir, "regional_condition_heatmap.png")
            plt.tight_layout()
            plt.savefig(fig_path3, dpi=300)
            plt.close()
            image_paths["regional_condition"] = fig_path3

        return image_paths

    def generate_html_report(self, overall_score: float, grade: str, dimension_scores: Dict[str, float],
                             val_metrics: Dict[str, Any], issues_df: pd.DataFrame) -> str:
        """
        Compiles an executive HTML audit report detailing scores, metrics, and top issue tables.
        """
        html_path = os.path.join(self.output_dir, "executive_audit_report.html")
        
        grade_colors = {"A": "#28a745", "B": "#17a2b8", "C": "#ffc107", "D": "#fd7e14", "F": "#dc3545"}
        badge_color = grade_colors.get(grade, "#6c757d")

        issues_html = ""
        if not issues_df.empty:
            top_issues = issues_df.head(15)
            issues_rows = ""
            for _, r in top_issues.iterrows():
                issues_rows += f"""
                <tr>
                    <td>{r.get('row_index', '')}</td>
                    <td><b>{r.get('bridge_id', '')}</b></td>
                    <td>{r.get('column', '')}</td>
                    <td><span class="badge badge-danger">{r.get('issue_code', '')}</span></td>
                    <td>{r.get('severity', '')}</td>
                    <td>{r.get('description', '')}</td>
                </tr>
                """
            issues_html = f"""
            <h3>Top Flagged Validation Issues</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Row #</th>
                        <th>Bridge ID</th>
                        <th>Column</th>
                        <th>Issue Code</th>
                        <th>Severity</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {issues_rows}
                </tbody>
            </table>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DPWH Infrastructure Data Quality Audit Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 25px; }}
        .container {{ max-width: 1100px; margin: 0 auto; background: #ffffff; padding: 35px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .header {{ border-bottom: 3px solid #2b5c8f; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ margin: 0; color: #2b5c8f; font-size: 26px; }}
        .grade-box {{ text-align: center; background: {badge_color}; color: white; padding: 15px 30px; border-radius: 10px; font-weight: bold; }}
        .grade-box .score {{ font-size: 32px; display: block; }}
        .grade-box .grade {{ font-size: 20px; }}
        .card-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #f1f5f9; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #2b5c8f; }}
        .card h4 {{ margin: 0 0 10px 0; color: #64748b; font-size: 13px; text-transform: uppercase; }}
        .card .val {{ font-size: 22px; font-weight: bold; color: #1e293b; }}
        .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        .table th, .table td {{ padding: 10px 12px; border: 1px solid #e2e8f0; text-align: left; }}
        .table th {{ background-color: #f8fafc; color: #475569; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white; background: #ef4444; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #94a3b8; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Infrastructure Data Quality Audit Report</h1>
                <p style="margin: 5px 0 0 0; color: #64748b;">Philippine Department of Public Works and Highways (DPWH) National Bridge Inventory</p>
            </div>
            <div class="grade-box">
                <span class="score">{overall_score}%</span>
                <span class="grade">GRADE {grade}</span>
            </div>
        </div>

        <div class="card-grid">
            <div class="card">
                <h4>Total Records</h4>
                <div class="val">{val_metrics.get('total_records_evaluated', 0):,}</div>
            </div>
            <div class="card">
                <h4>Clean Valid Records</h4>
                <div class="val" style="color: #10b981;">{val_metrics.get('clean_records', 0):,}</div>
            </div>
            <div class="card">
                <h4>Quarantined / Flagged</h4>
                <div class="val" style="color: #ef4444;">{val_metrics.get('flagged_records', 0):,}</div>
            </div>
            <div class="card">
                <h4>Total Issue Count</h4>
                <div class="val" style="color: #f59e0b;">{val_metrics.get('total_issues_detected', 0):,}</div>
            </div>
        </div>

        <h3>Data Quality Dimension Breakdown</h3>
        <table class="table">
            <thead>
                <tr>
                    <th>DQ Dimension</th>
                    <th>Dimension Score</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td><b>{k}</b></td><td>{v}%</td><td>{'<span style=\"color:#10b981;font-weight:bold;\">PASS</span>' if v >= 80 else '<span style=\"color:#ef4444;font-weight:bold;\">ATTENTION REQUIRED</span>'}</td></tr>" for k, v in dimension_scores.items()])}
            </tbody>
        </table>

        {issues_html}

        <div class="footer">
            Generated by Infrastructure Data Audit & Validation Suite | DPWH Geospatial Data Engineering Platform
        </div>
    </div>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Executive HTML Audit Report generated -> {html_path}")
        return html_path
