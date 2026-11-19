import os
import pandas as pd
from typing import Dict, Any, Tuple
from app.utils.helpers import generate_serial
from app.services.detectors import detect_row_issues, find_dataset_duplicates, calculate_outlier_bounds
from app.services.repairs import apply_safe_repairs
from app.models.db import (
    update_dataset_stats, save_record_metadata_batch,
    log_activity, get_dataset
)

def analyze_dataset_pipeline(dataset_id: str, working_file_path: str) -> Dict[str, Any]:
    """
    Profiles the dataset, detects issues, applies safe repairs, and calculates RED/GREEN metrics.
    """
    # 1. Read working file
    if working_file_path.endswith(".csv"):
        df = pd.read_csv(working_file_path, dtype=object) # Read as object initially to preserve raw values
    else:
        df = pd.read_excel(working_file_path, dtype=object)

    total_records = len(df)
    columns = [str(c) for c in df.columns]
    total_columns = len(columns)

    if total_records == 0:
        update_dataset_stats(
            dataset_id=dataset_id,
            total_records=0,
            total_columns=total_columns,
            columns=columns,
            green_count=0,
            red_count=0,
            green_pct=0.0,
            red_pct=0.0,
            status="analyzed"
        )
        return {
            "total_records": 0,
            "green_count": 0,
            "red_count": 0,
            "green_percentage": 0.0,
            "red_percentage": 0.0
        }

    # 2. Stable DataFix Serial Numbers & Initial Metadata
    duplicate_indices = find_dataset_duplicates(df)
    outlier_bounds = calculate_outlier_bounds(df)

    initial_records_meta = []
    for idx in range(total_records):
        row = df.iloc[idx]
        serial = generate_serial(idx)
        issues = detect_row_issues(row, idx, df, duplicate_indices, outlier_bounds)
        has_human_issue = any(iss["repair_method"] == "human" for iss in issues)
        initial_records_meta.append({
            "record_index": idx,
            "datafix_serial": serial,
            "human_required": has_human_issue,
            "validation_status": "needs_human_review" if has_human_issue else "valid",
            "issues": issues
        })

    # 3. Apply Safe Repairs
    working_df, updated_meta, repairs_count = apply_safe_repairs(df, dataset_id, initial_records_meta)

    # 4. Save updated working dataset to disk
    if working_file_path.endswith(".csv"):
        working_df.to_csv(working_file_path, index=False)
    else:
        working_df.to_excel(working_file_path, index=False)

    # 5. Calculate Final RED/GREEN Metrics
    green_count = sum(1 for r in updated_meta if not r["human_required"])
    red_count = total_records - green_count

    green_pct = round((green_count / total_records) * 100, 1)
    red_pct = round((red_count / total_records) * 100, 1)

    # 6. Save records metadata to DB
    save_record_metadata_batch(dataset_id, updated_meta)

    # 7. Update dataset summary in DB
    update_dataset_stats(
        dataset_id=dataset_id,
        total_records=total_records,
        total_columns=total_columns,
        columns=columns,
        green_count=green_count,
        red_count=red_count,
        green_pct=green_pct,
        red_pct=red_pct,
        status="analyzed"
    )

    log_activity(
        dataset_id,
        "ANALYSIS_COMPLETE",
        f"Analysis complete: {green_count} GREEN records ({green_pct}%), {red_count} RED records ({red_pct}%)."
    )

    return {
        "total_records": total_records,
        "total_columns": total_columns,
        "columns": columns,
        "green_count": green_count,
        "red_count": red_count,
        "green_percentage": green_pct,
        "red_percentage": red_pct,
        "repairs_count": repairs_count
    }
