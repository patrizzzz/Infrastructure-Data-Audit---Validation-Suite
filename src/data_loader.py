import os
import json
import pandas as pd
import numpy as np
from typing import Union, Tuple, Dict, Any

def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Loads infrastructure dataset from CSV or GeoJSON file.
    Performs initial data parsing and column standardization.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_path, low_memory=False, encoding="utf-8-sig")
    elif ext in [".json", ".geojson"]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "features" in data:
            records = []
            for feat in data["features"]:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                if geom and geom.get("type") == "Point":
                    coords = geom.get("coordinates", [np.nan, np.nan])
                    props["LONGITUDE"] = coords[0]
                    props["LATITUDE"] = coords[1]
                records.append(props)
            df = pd.DataFrame(records)
        else:
            df = pd.DataFrame(data)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    df.columns = df.columns.str.strip()

    num_cols = ["BR_LENGTH", "BR_WIDTH", "NUM_ABUTT", "NUM_PIER", "NUM_SPAN", 
                "BR_LIFE", "LOAD_LIMIT", "HT_OVER", "HT_UNDER", "L_SDWALK", 
                "R_SDWALK", "NUM_LANES", "SEC_LENGTH", "MaxBRHT", "MaxPierHT"]
    
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "ACTUAL_YR" in df.columns:
        df["ACTUAL_YR_CLEAN"] = pd.to_numeric(df["ACTUAL_YR"], errors="coerce")

    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan, " ": np.nan})

    return df
