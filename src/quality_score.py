import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.config_loader import load_config

class DataQualityScorer:
    """
    Composite Data Quality Scoring Engine.
    Evaluates dataset across 5 core Data Quality dimensions:
      1. Completeness (25%)
      2. Validity (30%)
      3. Uniqueness (20%)
      4. Consistency (15%)
      5. Timeliness (10%)
    Computes overall score (0 - 100%) and Letter Grade (A-F).
    """
    def __init__(self, df: pd.DataFrame, issues_df: pd.DataFrame, config: Dict[str, Any] = None):
        self.df = df.copy()
        self.issues_df = issues_df.copy()
        self.config = config or load_config()

    def calculate_scores(self) -> Tuple[float, str, Dict[str, float]]:
        """
        Calculates individual dimension scores and overall composite quality score.
        Returns:
            overall_score: Float between 0.0 and 100.0.
            letter_grade: String ('A', 'B', 'C', 'D', 'F').
            dimension_scores: Dictionary of dimension scores.
        """
        total_rows = len(self.df)
        if total_rows == 0:
            return 0.0, "F", {}

        mandatory_cols = self.config.get("mandatory_columns", ["BRIDGE_ID", "BR_NAME", "REGION", "PROVINCE", "DEO"])
        existing_mandatory = [c for c in mandatory_cols if c in self.df.columns]
        if existing_mandatory:
            non_null_pcts = [self.df[c].notnull().mean() for c in existing_mandatory]
            completeness = float(np.mean(non_null_pcts) * 100)
        else:
            completeness = float((1 - self.df.isnull().mean().mean()) * 100)

        flagged_rows = len(self.issues_df["row_index"].unique()) if not self.issues_df.empty else 0
        validity = float(max(0.0, (total_rows - flagged_rows) / total_rows * 100))

        if "BRIDGE_ID" in self.df.columns:
            unique_ids = self.df["BRIDGE_ID"].nunique(dropna=True)
            non_null_ids = self.df["BRIDGE_ID"].notnull().sum()
            uniqueness = float((unique_ids / non_null_ids * 100)) if non_null_ids > 0 else 0.0
        else:
            duplicate_rows = self.df.duplicated().sum()
            uniqueness = float((total_rows - duplicate_rows) / total_rows * 100)

        consistency_checks = []
        if "BR_LENGTH" in self.df.columns and "BR_WIDTH" in self.df.columns:
            consistency_checks.append((self.df["BR_LENGTH"] > 0) & (self.df["BR_WIDTH"] > 0))
        if "NUM_SPAN" in self.df.columns and "BR_LENGTH" in self.df.columns:
            consistency_checks.append((self.df["NUM_SPAN"] >= 1) | (self.df["BR_LENGTH"].isnull()))
        if "NUM_ABUTT" in self.df.columns and "NUM_PIER" in self.df.columns:
            consistency_checks.append((self.df["NUM_ABUTT"] >= 0) & (self.df["NUM_PIER"] >= 0))
            
        if consistency_checks:
            combined_consistency = np.logical_and.reduce(consistency_checks)
            consistency = float(combined_consistency.mean() * 100)
        else:
            consistency = 90.0

        year_col = "ACTUAL_YR_CLEAN" if "ACTUAL_YR_CLEAN" in self.df.columns else "ACTUAL_YR"
        if year_col in self.df.columns:
            valid_yrs = pd.to_numeric(self.df[year_col], errors="coerce")
            timeliness = float((valid_yrs.notnull() & (valid_yrs >= 1950) & (valid_yrs <= 2026)).mean() * 100)
        else:
            timeliness = 85.0

        weights = self.config.get("quality_score_weights", {
            "completeness": 0.25,
            "validity": 0.30,
            "uniqueness": 0.20,
            "consistency": 0.15,
            "timeliness": 0.10
        })

        overall_score = (
            completeness * weights.get("completeness", 0.25) +
            validity * weights.get("validity", 0.30) +
            uniqueness * weights.get("uniqueness", 0.20) +
            consistency * weights.get("consistency", 0.15) +
            timeliness * weights.get("timeliness", 0.10)
        )

        overall_score = round(float(overall_score), 2)

        if overall_score >= 90.0:
            letter_grade = "A"
        elif overall_score >= 80.0:
            letter_grade = "B"
        elif overall_score >= 70.0:
            letter_grade = "C"
        elif overall_score >= 60.0:
            letter_grade = "D"
        else:
            letter_grade = "F"

        dimension_scores = {
            "Completeness": round(completeness, 2),
            "Validity": round(validity, 2),
            "Uniqueness": round(uniqueness, 2),
            "Consistency": round(consistency, 2),
            "Timeliness": round(timeliness, 2)
        }

        return overall_score, letter_grade, dimension_scores
