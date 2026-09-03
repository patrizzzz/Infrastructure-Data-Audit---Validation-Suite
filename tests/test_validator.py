import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
from src.validator import DataValidator

def test_validator_mandatory_missing():
    data = {
        "BRIDGE_ID": ["B00001LZ", None],
        "BR_NAME": ["Bridge A", "Bridge B"],
        "REGION": ["NCR", "CAR"],
        "PROVINCE": ["Metro Manila", "Benguet"],
        "DEO": ["NCR 1st DEO", "Benguet DEO"],
        "ROAD_NAME": ["EDSA", "Kennon Rd"]
    }
    df = pd.DataFrame(data)
    validator = DataValidator(df)
    issues_df, metrics = validator.validate()
    
    assert len(issues_df) >= 1
    assert "ERR_MANDATORY_MISSING" in issues_df["issue_code"].values

def test_validator_spatial_bounds():
    data = {
        "BRIDGE_ID": ["B00001LZ", "B00002LZ"],
        "BR_NAME": ["Bridge A", "Bridge B"],
        "REGION": ["NCR", "CAR"],
        "PROVINCE": ["Metro Manila", "Benguet"],
        "DEO": ["NCR 1st DEO", "Benguet DEO"],
        "ROAD_NAME": ["EDSA", "Kennon Rd"],
        "LATITUDE": [14.5, 88.888],  # Second one out of bounds
        "LONGITUDE": [121.0, 120.0]
    }
    df = pd.DataFrame(data)
    validator = DataValidator(df)
    issues_df, metrics = validator.validate()
    
    assert "ERR_INVALID_SPATIAL_BOUNDS" in issues_df["issue_code"].values

def test_validator_duplicate_primary_key():
    data = {
        "BRIDGE_ID": ["B00001LZ", "B00001LZ"], # Duplicate ID
        "BR_NAME": ["Bridge A", "Bridge A Dup"],
        "REGION": ["NCR", "NCR"],
        "PROVINCE": ["Metro Manila", "Metro Manila"],
        "DEO": ["NCR 1st DEO", "NCR 1st DEO"],
        "ROAD_NAME": ["EDSA", "EDSA"]
    }
    df = pd.DataFrame(data)
    validator = DataValidator(df)
    issues_df, metrics = validator.validate()
    
    assert "ERR_DUPLICATE_PRIMARY_KEY" in issues_df["issue_code"].values
