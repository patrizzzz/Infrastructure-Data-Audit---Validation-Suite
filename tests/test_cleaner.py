import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
from src.validator import DataValidator
from src.cleaner import DataCleaner

def test_cleaner_quarantine_isolation():
    data = {
        "BRIDGE_ID": ["B00001LZ", None],  # Second row critical missing ID
        "BR_NAME": ["Valid Bridge", "Missing ID Bridge"],
        "REGION": ["NCR", "NCR"],
        "PROVINCE": ["Metro Manila", "Metro Manila"],
        "DEO": ["NCR 1st DEO", "NCR 1st DEO"],
        "ROAD_NAME": ["EDSA", "EDSA"],
        "BR_WIDTH": [10.0, 0.0]
    }
    df = pd.DataFrame(data)
    validator = DataValidator(df)
    issues_df, _ = validator.validate()
    
    cleaner = DataCleaner(df, issues_df)
    clean_df, quarantine_df, audit_log_df = cleaner.clean_and_quarantine()
    
    assert len(clean_df) == 1
    assert len(quarantine_df) == 1
    assert clean_df.iloc[0]["BRIDGE_ID"] == "B00001LZ"
    assert not audit_log_df.empty
