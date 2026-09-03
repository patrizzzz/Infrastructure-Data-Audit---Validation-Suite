import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
from src.quality_score import DataQualityScorer

def test_quality_scorer_perfect_score():
    data = {
        "BRIDGE_ID": ["B00001LZ", "B00002LZ"],
        "BR_NAME": ["Bridge A", "Bridge B"],
        "REGION": ["NCR", "CAR"],
        "PROVINCE": ["Metro Manila", "Benguet"],
        "DEO": ["NCR DEO", "Benguet DEO"],
        "BR_LENGTH": [50.0, 100.0],
        "BR_WIDTH": [10.0, 12.0],
        "NUM_SPAN": [2, 4],
        "ACTUAL_YR": [2010, 2015]
    }
    df = pd.DataFrame(data)
    issues_df = pd.DataFrame()
    
    scorer = DataQualityScorer(df, issues_df)
    score, grade, dim_scores = scorer.calculate_scores()
    
    assert score >= 90.0
    assert grade == "A"
    assert dim_scores["Completeness"] == 100.0
    assert dim_scores["Validity"] == 100.0
