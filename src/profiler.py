import pandas as pd
import numpy as np
from typing import Dict, Any

class DataProfiler:
    """
    Data Profiling Engine for Infrastructure Datasets.
    Computes structural metrics, missingness patterns, statistical summaries, and uniqueness.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def profile(self) -> Dict[str, Any]:
        """
        Executes a complete profiling sweep over the dataset.
        Returns a dictionary of profiling results.
        """
        total_rows, total_cols = self.df.shape
        total_cells = total_rows * total_cols
        
        missing_counts = self.df.isnull().sum()
        missing_pcts = (missing_counts / total_rows * 100).round(2)
        
        column_profile = {}
        for col in self.df.columns:
            dtype_str = str(self.df[col].dtype)
            num_missing = int(missing_counts[col])
            pct_missing = float(missing_pcts[col])
            num_unique = int(self.df[col].nunique(dropna=True))
            
            col_info = {
                "dtype": dtype_str,
                "missing_count": num_missing,
                "missing_pct": pct_missing,
                "unique_count": num_unique
            }
            
            if pd.api.types.is_numeric_dtype(self.df[col]):
                valid_series = self.df[col].dropna()
                if not valid_series.empty:
                    col_info["stats"] = {
                        "min": float(valid_series.min()),
                        "max": float(valid_series.max()),
                        "mean": float(valid_series.mean().round(2)),
                        "median": float(valid_series.median().round(2)),
                        "std": float(valid_series.std().round(2)) if len(valid_series) > 1 else 0.0,
                        "skewness": float(valid_series.skew().round(2)) if len(valid_series) > 2 else 0.0
                    }
            else:
                top_values = self.df[col].value_counts().head(5).to_dict()
                col_info["top_categories"] = {str(k): int(v) for k, v in top_values.items()}
                
            column_profile[col] = col_info

        duplicate_rows = int(self.df.duplicated().sum())
        pk_duplicates = int(self.df.duplicated(subset=["BRIDGE_ID"]).sum()) if "BRIDGE_ID" in self.df.columns else 0

        summary = {
            "dataset_shape": {"rows": total_rows, "columns": total_cols, "total_cells": total_cells},
            "total_duplicates": duplicate_rows,
            "bridge_id_duplicates": pk_duplicates,
            "overall_missing_cells": int(missing_counts.sum()),
            "overall_missing_pct": float((missing_counts.sum() / total_cells * 100).round(2)),
            "columns": column_profile
        }

        return summary
