import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from src.config_loader import load_config

class DataValidator:
    """
    Validation Engine for Infrastructure Data Quality.
    Evaluates dataset against mandatory fields, numerical ranges, geographic bounds,
    pattern regexes, duplicate primary keys, and categorical enums.
    """
    def __init__(self, df: pd.DataFrame, config: Dict[str, Any] = None):
        self.df = df.copy()
        self.config = config or load_config()

    def validate(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes validation checks and logs detailed issues.
        Returns:
            issues_df: DataFrame of flagged data issues.
            metrics: Dictionary of summary validation statistics.
        """
        issues: List[Dict[str, Any]] = []

        mandatory_cols = self.config.get("mandatory_columns", [])
        for col in mandatory_cols:
            if col in self.df.columns:
                missing_mask = self.df[col].isnull() | (self.df[col] == "")
                for idx in self.df[missing_mask].index:
                    bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                    issues.append({
                        "row_index": idx,
                        "bridge_id": bridge_id,
                        "column": col,
                        "issue_code": "ERR_MANDATORY_MISSING",
                        "severity": "CRITICAL",
                        "description": f"Mandatory column '{col}' is missing or empty.",
                        "invalid_value": None
                    })

        num_bounds = self.config.get("numerical_bounds", {})
        for col, bounds in num_bounds.items():
            if col in self.df.columns:
                min_val = bounds.get("min")
                max_val = bounds.get("max")
                
                series = pd.to_numeric(self.df[col], errors="coerce")
                
                if min_val is not None:
                    out_min = series < min_val
                    for idx in self.df[out_min].index:
                        val = self.df.loc[idx, col]
                        bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                        issues.append({
                            "row_index": idx,
                            "bridge_id": bridge_id,
                            "column": col,
                            "issue_code": "ERR_NUMERICAL_UNDERFLOW",
                            "severity": "HIGH",
                            "description": f"Value {val} is below minimum bound ({min_val}).",
                            "invalid_value": val
                        })
                        
                if max_val is not None:
                    out_max = series > max_val
                    for idx in self.df[out_max].index:
                        val = self.df.loc[idx, col]
                        bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                        issues.append({
                            "row_index": idx,
                            "bridge_id": bridge_id,
                            "column": col,
                            "issue_code": "ERR_NUMERICAL_OVERFLOW",
                            "severity": "HIGH",
                            "description": f"Value {val} exceeds maximum bound ({max_val}).",
                            "invalid_value": val
                        })

        if "LATITUDE" in self.df.columns and "LONGITUDE" in self.df.columns:
            lat_bounds = self.config.get("spatial_bounds", {}).get("latitude", {})
            long_bounds = self.config.get("spatial_bounds", {}).get("longitude", {})
            
            lats = pd.to_numeric(self.df["LATITUDE"], errors="coerce")
            longs = pd.to_numeric(self.df["LONGITUDE"], errors="coerce")
            
            invalid_geo = (lats < lat_bounds.get("min", 4.5)) | (lats > lat_bounds.get("max", 21.5)) | \
                          (longs < long_bounds.get("min", 116.0)) | (longs > long_bounds.get("max", 127.0))
            
            for idx in self.df[invalid_geo].index:
                lat_val = self.df.loc[idx, "LATITUDE"]
                long_val = self.df.loc[idx, "LONGITUDE"]
                bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                issues.append({
                    "row_index": idx,
                    "bridge_id": bridge_id,
                    "column": "COORDINATES",
                    "issue_code": "ERR_INVALID_SPATIAL_BOUNDS",
                    "severity": "HIGH",
                    "description": f"Coordinates ({lat_val}, {long_val}) are outside Philippine spatial bounding box.",
                    "invalid_value": f"Lat: {lat_val}, Long: {long_val}"
                })

        year_col = "ACTUAL_YR_CLEAN" if "ACTUAL_YR_CLEAN" in self.df.columns else "ACTUAL_YR"
        if year_col in self.df.columns:
            date_cfg = self.config.get("date_bounds", {}).get("construction_year", {})
            min_yr = date_cfg.get("min", 1800)
            max_yr = date_cfg.get("max", 2026)
            
            yrs = pd.to_numeric(self.df[year_col], errors="coerce")
            invalid_yr = (yrs.notnull()) & ((yrs < min_yr) | (yrs > max_yr))
            for idx in self.df[invalid_yr].index:
                val = self.df.loc[idx, year_col]
                bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                issues.append({
                    "row_index": idx,
                    "bridge_id": bridge_id,
                    "column": "ACTUAL_YR",
                    "issue_code": "ERR_INVALID_CONSTRUCTION_YEAR",
                    "severity": "MEDIUM",
                    "description": f"Year {val} is outside realistic bounds ({min_yr}-{max_yr}).",
                    "invalid_value": val
                })

        regex_cfg = self.config.get("regex_patterns", {})
        if "BRIDGE_ID" in self.df.columns and "BRIDGE_ID" in regex_cfg:
            pattern = regex_cfg["BRIDGE_ID"]
            compiled_re = re.compile(pattern)
            
            for idx, val in self.df["BRIDGE_ID"].items():
                if pd.notnull(val) and str(val) != "":
                    if not compiled_re.match(str(val)):
                        issues.append({
                            "row_index": idx,
                            "bridge_id": val,
                            "column": "BRIDGE_ID",
                            "issue_code": "ERR_INVALID_ID_FORMAT",
                            "severity": "HIGH",
                            "description": f"Bridge ID '{val}' does not match standard pattern '{pattern}'.",
                            "invalid_value": val
                        })

        if "BRIDGE_ID" in self.df.columns:
            dup_mask = self.df.duplicated(subset=["BRIDGE_ID"], keep=False) & self.df["BRIDGE_ID"].notnull()
            for idx in self.df[dup_mask].index:
                val = self.df.loc[idx, "BRIDGE_ID"]
                issues.append({
                    "row_index": idx,
                    "bridge_id": val,
                    "column": "BRIDGE_ID",
                    "issue_code": "ERR_DUPLICATE_PRIMARY_KEY",
                    "severity": "CRITICAL",
                    "description": f"Duplicate Bridge ID '{val}' detected.",
                    "invalid_value": val
                })

        categories_cfg = self.config.get("allowed_categories", {})
        for col, allowed_list in categories_cfg.items():
            if col in self.df.columns:
                invalid_cat = self.df[col].notnull() & (~self.df[col].isin(allowed_list))
                for idx in self.df[invalid_cat].index:
                    val = self.df.loc[idx, col]
                    bridge_id = self.df.loc[idx, "BRIDGE_ID"] if "BRIDGE_ID" in self.df.columns else "UNKNOWN"
                    issues.append({
                        "row_index": idx,
                        "bridge_id": bridge_id,
                        "column": col,
                        "issue_code": "ERR_INVALID_CATEGORY",
                        "severity": "MEDIUM",
                        "description": f"Value '{val}' not in allowed categories {allowed_list}.",
                        "invalid_value": val
                    })

        issues_df = pd.DataFrame(issues)
        
        total_rows = len(self.df)
        flagged_rows = len(issues_df["row_index"].unique()) if not issues_df.empty else 0
        valid_rows = total_rows - flagged_rows
        
        metrics = {
            "total_records_evaluated": total_rows,
            "total_issues_detected": len(issues_df),
            "flagged_records": flagged_rows,
            "clean_records": valid_rows,
            "issue_breakdown_by_code": issues_df["issue_code"].value_counts().to_dict() if not issues_df.empty else {},
            "issue_breakdown_by_severity": issues_df["severity"].value_counts().to_dict() if not issues_df.empty else {}
        }

        return issues_df, metrics
