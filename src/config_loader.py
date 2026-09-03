import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "validation_rules.yaml")

DEFAULT_CONFIG: Dict[str, Any] = {
    "spatial_bounds": {
        "latitude": {"min": 4.5, "max": 21.5},
        "longitude": {"min": 116.0, "max": 127.0}
    },
    "mandatory_columns": ["BRIDGE_ID", "BR_NAME", "REGION", "PROVINCE", "DEO", "ROAD_NAME"],
    "numerical_bounds": {
        "BR_LENGTH": {"min": 0.1, "max": 5000.0},
        "BR_WIDTH": {"min": 1.0, "max": 60.0},
        "NUM_SPAN": {"min": 1, "max": 150},
        "NUM_LANES": {"min": 1, "max": 16},
        "LOAD_LIMIT": {"min": 0, "max": 100}
    },
    "date_bounds": {
        "construction_year": {"min": 1800, "max": 2026}
    },
    "regex_patterns": {
        "BRIDGE_ID": r"^B\d{5}[A-Z]{2}$"
    },
    "allowed_categories": {
        "CONDITION": ["Good", "Fair", "Poor", "Bad"],
        "BR_TYPE1": ["Concrete", "Steel", "Timber", "Masonry", "Pre-stressed Concrete", "Other"]
    },
    "quality_score_weights": {
        "completeness": 0.25,
        "validity": 0.30,
        "uniqueness": 0.20,
        "consistency": 0.15,
        "timeliness": 0.10
    }
}

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Loads validation rules configuration from YAML file with fallback defaults.
    """
    target_path = config_path or DEFAULT_CONFIG_PATH
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config else DEFAULT_CONFIG
        except Exception as e:
            print(f"[Warning] Failed to load config from {target_path}: {e}. Using defaults.")
            return DEFAULT_CONFIG
    else:
        return DEFAULT_CONFIG
