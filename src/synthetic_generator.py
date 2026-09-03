import os
import random
import pandas as pd
import numpy as np

def generate_dirty_sample(num_records: int = 200, output_path: str = None) -> pd.DataFrame:
    """
    Generates a synthetic dirty infrastructure dataset with injected anomalies:
      - Inverted / Out-of-bounds coordinates
      - Impossible construction years (e.g. 2999, 1600)
      - Negative bridge lengths and carriageway widths
      - Missing mandatory fields (BRIDGE_ID, BR_NAME)
      - Duplicate primary key IDs
      - Invalid categorical ratings ('Critical Danger', 'Destroyed')
    """
    regions = ["National Capital Region", "Cordillera Administrative Region", "Region I - Ilocos Region", "Region IV-A - CALABARZON"]
    provinces = ["Metro Manila", "Benguet", "Ilocos Norte", "Cavite"]
    deos = ["Metro Manila 1st DEO", "Benguet 1st DEO", "Ilocos Norte 1st DEO", "Cavite DEO"]
    types = ["Concrete", "Steel", "Timber", "Pre-stressed Concrete"]
    conditions = ["Good", "Fair", "Poor", "Bad"]

    records = []
    for i in range(1, num_records + 1):
        bridge_id = f"B{i:05d}LZ"
        br_name = f"Sample Bridge {i}"
        region = random.choice(regions)
        province = random.choice(provinces)
        deo = random.choice(deos)
        road_name = f"National Highway Sector {i % 10}"
        
        br_length = round(random.uniform(10.0, 300.0), 2)
        br_width = round(random.uniform(6.0, 15.0), 2)
        num_span = random.randint(1, 10)
        num_lanes = random.choice([2, 4, 6])
        load_limit = random.choice([15, 20, 25, 30])
        actual_yr = random.randint(1960, 2021)
        condition = random.choice(conditions)
        
        lat = round(random.uniform(14.0, 17.0), 6)
        long_val = round(random.uniform(120.0, 122.0), 6)

        records.append({
            "OBJECTID": i,
            "ISLAND": "Luzon",
            "REGION": region,
            "PROVINCE": province,
            "DEO": deo,
            "ROAD_NAME": road_name,
            "BRIDGE_ID": bridge_id,
            "BR_NAME": br_name,
            "BR_LENGTH": br_length,
            "BR_WIDTH": br_width,
            "BR_TYPE1": random.choice(types),
            "BR_TYPE2": "Permanent",
            "ACTUAL_YR": str(actual_yr),
            "CONDITION": condition,
            "NUM_SPAN": num_span,
            "NUM_LANES": num_lanes,
            "LOAD_LIMIT": load_limit,
            "LATITUDE": lat,
            "LONGITUDE": long_val
        })

    dirty_df = pd.DataFrame(records)

    dirty_df.loc[5, "BRIDGE_ID"] = np.nan  # Missing mandatory ID
    dirty_df.loc[12, "BR_NAME"] = ""  # Missing mandatory Name
    dirty_df.loc[20, "LATITUDE"] = 99.999  # Invalid Latitude
    dirty_df.loc[20, "LONGITUDE"] = 200.000  # Invalid Longitude
    dirty_df.loc[35, "BR_LENGTH"] = -50.0  # Negative length
    dirty_df.loc[42, "ACTUAL_YR"] = "2999"  # Future year
    dirty_df.loc[55, "BRIDGE_ID"] = "INVALID_ID_FORMAT_999"  # Bad Regex ID
    dirty_df.loc[70, "BRIDGE_ID"] = dirty_df.loc[10, "BRIDGE_ID"]  # Duplicate Primary Key
    dirty_df.loc[88, "CONDITION"] = "Destroyed Beyond Repair"  # Invalid Category

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        dirty_df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"Generated synthetic dirty dataset ({len(dirty_df)} rows) -> {output_path}")

    return dirty_df
