import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

class DataCleaner:
    """
    Data Cleaning & Quarantine Manager.
    Separates valid records from quarantined records based on issue severity,
    applies standardized text formatting, and imputes minor missing values.
    """
    def __init__(self, df: pd.DataFrame, issues_df: pd.DataFrame):
        self.df = df.copy()
        self.issues_df = issues_df.copy()

    def clean_and_quarantine(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes cleaning pipeline.
        Returns:
            clean_df: Cleaned and validated dataset.
            quarantine_df: Isolated invalid records.
            audit_log_df: Detailed log of all cleaning actions & imputations.
        """
        audit_records = []

        if not self.issues_df.empty:
            critical_mask = self.issues_df["severity"].isin(["CRITICAL", "HIGH"])
            quarantine_row_indices = self.issues_df[critical_mask]["row_index"].unique()
        else:
            quarantine_row_indices = np.array([])

        quarantine_df = self.df.loc[self.df.index.isin(quarantine_row_indices)].copy()
        clean_df = self.df.loc[~self.df.index.isin(quarantine_row_indices)].copy()

        text_columns = clean_df.select_dtypes(include=["object"]).columns
        for col in text_columns:
            clean_df[col] = clean_df[col].astype(str).str.strip()
            clean_df[col] = clean_df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})

        if "CONDITION" in clean_df.columns:
            clean_df["CONDITION"] = clean_df["CONDITION"].str.title()
            valid_conds = ["Good", "Fair", "Poor", "Bad"]
            invalid_cond_mask = ~clean_df["CONDITION"].isin(valid_conds) & clean_df["CONDITION"].notnull()
            clean_df.loc[invalid_cond_mask, "CONDITION"] = "Fair"

        impute_num_cols = ["BR_WIDTH", "NUM_LANES", "LOAD_LIMIT", "NUM_SPAN"]
        for col in impute_num_cols:
            if col in clean_df.columns:
                missing_mask = clean_df[col].isnull() | (clean_df[col] == 0)
                if missing_mask.any():
                    regional_median = clean_df.groupby("REGION")[col].transform("median")
                    overall_median = clean_df[col].median()
                    fill_series = regional_median.fillna(overall_median).fillna(1.0)
                    
                    imputed_indices = clean_df[missing_mask].index
                    clean_df.loc[missing_mask, col] = fill_series[missing_mask]
                    clean_df[f"{col}_IMPUTED"] = False
                    clean_df.loc[missing_mask, f"{col}_IMPUTED"] = True

                    for idx in imputed_indices:
                        bridge_id = clean_df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in clean_df.columns else "UNKNOWN"
                        audit_records.append({
                            "row_index": idx,
                            "bridge_id": bridge_id,
                            "column": col,
                            "action_taken": "IMPUTED_MEDIAN",
                            "new_value": clean_df.loc[idx, col],
                            "notes": "Imputed missing/zero numerical value using regional median."
                        })

        if not self.issues_df.empty:
            for idx, row in self.issues_df.iterrows():
                is_quarantined = row["row_index"] in quarantine_row_indices
                audit_records.append({
                    "row_index": row["row_index"],
                    "bridge_id": row["bridge_id"],
                    "column": row["column"],
                    "action_taken": "QUARANTINED" if is_quarantined else "FLAGGED_WARNING",
                    "new_value": None,
                    "notes": f"Issue [{row['issue_code']}] Severity: {row['severity']} - {row['description']}"
                })

        audit_log_df = pd.DataFrame(audit_records)

        return clean_df, quarantine_df, audit_log_df
