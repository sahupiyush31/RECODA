import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from app.models.db import (
    get_dataset, get_records_metadata, save_record_metadata_batch,
    log_audit, log_activity, update_dataset_stats
)
from app.services.detectors import detect_row_issues, find_dataset_duplicates, calculate_outlier_bounds
from app.services.repairs import apply_safe_repairs
from app.utils.helpers import generate_serial


def _safe_str(v) -> str:
    """Safely convert a cell value to string, treating NA as empty string.
    Guards against non-scalar types (lists/arrays) that make pd.isna() return an array."""
    if v is None:
        return ""
    try:
        result = pd.isna(v)
        if isinstance(result, (bool, np.bool_)) and result:
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).strip()

def reconcile_fixed_dataset(dataset_id: str, uploaded_file_path: str) -> Dict[str, Any]:
    """
    Reconciles human-corrected RED file with working dataset using DataFix Serial Numbers.
    Enforces strict reconciliation safeguards.
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset {dataset_id} not found.")

    working_file_path = dataset["working_file_path"]
    if working_file_path.endswith(".csv"):
        working_df = pd.read_csv(working_file_path, dtype=object)
    else:
        working_df = pd.read_excel(working_file_path, dtype=object)

    # Read uploaded correction file
    if uploaded_file_path.endswith(".csv"):
        uploaded_df = pd.read_csv(uploaded_file_path, dtype=object)
    else:
        uploaded_df = pd.read_excel(uploaded_file_path, dtype=object)

    # Identify serial column or fallback identifier
    serial_col = None
    for cand in ["DataFix_Serial", "datafix_serial", "DFX_Serial", "DataFix Serial Number", "Serial"]:
        if cand in uploaded_df.columns:
            serial_col = cand
            break

    current_meta = get_records_metadata(dataset_id)
    meta_by_serial = {m["datafix_serial"]: m for m in current_meta}
    meta_by_index = {m["record_index"]: m for m in current_meta}

    id_col = None
    id_to_index = {}

    if serial_col:
        # Safeguards: check for duplicate serials
        uploaded_serials = uploaded_df[serial_col].dropna().astype(str).str.strip().tolist()
        if len(uploaded_serials) != len(set(uploaded_serials)):
            raise ValueError("Reconciliation rejected: Duplicate DataFix serial numbers found in uploaded file.")
    else:
        # Fallback 1: check for primary key column present in both datasets
        for cand_id in ["Employee_ID", "employee_id", "emp_id", "ID", "id", "Record_ID", "record_id"]:
            if cand_id in uploaded_df.columns and cand_id in working_df.columns:
                id_col = cand_id
                id_to_index = {
                    str(working_df.at[i, id_col]).strip(): i
                    for i in range(len(working_df))
                    if not pd.isna(working_df.at[i, id_col]) and str(working_df.at[i, id_col]).strip() != ""
                }
                break

        # Fallback 2: full dataset match if row counts and columns align
        full_match = (len(uploaded_df) == len(working_df)) and set(working_df.columns).issubset(set(uploaded_df.columns))

        if not id_col and not full_match:
            raise ValueError(
                "Correction file must include a 'DataFix_Serial' column (obtained via 'Download Correction Template') "
                "or match the original dataset's primary key (e.g. 'Employee_ID')."
            )

    accepted_changes = 0
    rejected_changes = 0
    reconciled_serials = []

    # Map rows to working dataset
    for row_idx, up_row in uploaded_df.iterrows():
        target_idx = None
        serial = None

        if serial_col:
            raw_s = up_row[serial_col]
            serial = str(raw_s).strip() if not pd.isna(raw_s) else None
            if not serial or serial not in meta_by_serial:
                continue
            target_meta = meta_by_serial[serial]
            target_idx = target_meta["record_index"]
        elif id_col:
            raw_id = up_row[id_col]
            id_val = str(raw_id).strip() if not pd.isna(raw_id) else None
            if not id_val or id_val not in id_to_index:
                continue
            target_idx = id_to_index[id_val]
            serial = meta_by_index[target_idx]["datafix_serial"]
        else:
            # Full dataset aligned by row index
            if row_idx in meta_by_index:
                target_idx = row_idx
                serial = meta_by_index[target_idx]["datafix_serial"]

        if target_idx is None or serial is None:
            continue

        idx = target_idx

        # Compare column changes (excluding serial column)
        for col in working_df.columns:
            if col in uploaded_df.columns:
                old_val = working_df.at[idx, col]
                new_val = up_row[col]

                # Normalize string representations for comparison
                old_str = _safe_str(old_val)
                new_str = _safe_str(new_val)

                if old_str != new_str:
                    # Validate correction: does not accept introducing blank to required field
                    if new_str == "":
                        log_audit(
                            dataset_id=dataset_id,
                            serial=serial,
                            col=col,
                            old_val=old_str,
                            new_val=new_str,
                            actor="Human",
                            reason="Rejected: Cannot replace value with empty/blank",
                            val_result="rejected"
                        )
                        rejected_changes += 1
                    else:
                        working_df.at[idx, col] = new_str
                        accepted_changes += 1
                        reconciled_serials.append(serial)
                        log_audit(
                            dataset_id=dataset_id,
                            serial=serial,
                            col=col,
                            old_val=old_str,
                            new_val=new_str,
                            actor="Human",
                            reason="Human correction applied via Add Fixed Dataset",
                            val_result="passed"
                        )

    # Save updated working dataset
    if working_file_path.endswith(".csv"):
        working_df.to_csv(working_file_path, index=False)
    else:
        working_df.to_excel(working_file_path, index=False)

    # Re-run issue detection and revalidation across working_df
    total_records = len(working_df)
    duplicate_indices = find_dataset_duplicates(working_df)
    outlier_bounds = calculate_outlier_bounds(working_df)

    # Build lookup by record_index to avoid positional-index desync
    meta_by_index = {m["record_index"]: m["datafix_serial"] for m in current_meta}

    updated_meta = []
    for idx in range(total_records):
        row = working_df.iloc[idx]
        serial = meta_by_index.get(idx, generate_serial(idx))
        issues = detect_row_issues(row, idx, working_df, duplicate_indices, outlier_bounds)
        has_human_issue = any(iss["repair_method"] == "human" for iss in issues)

        updated_meta.append({
            "record_index": idx,
            "datafix_serial": serial,
            "human_required": has_human_issue,
            "validation_status": "needs_human_review" if has_human_issue else "valid",
            "issues": issues
        })

    # Save to DB
    save_record_metadata_batch(dataset_id, updated_meta)

    # Recalculate stats
    green_count = sum(1 for r in updated_meta if not r["human_required"])
    red_count = total_records - green_count
    green_pct = round((green_count / total_records) * 100, 1) if total_records > 0 else 0.0
    red_pct = round((red_count / total_records) * 100, 1) if total_records > 0 else 0.0

    update_dataset_stats(
        dataset_id=dataset_id,
        total_records=total_records,
        total_columns=len(working_df.columns),
        columns=[str(c) for c in working_df.columns],
        green_count=green_count,
        red_count=red_count,
        green_pct=green_pct,
        red_pct=red_pct,
        status="reconciled"
    )

    log_activity(
        dataset_id,
        "HUMAN_CORRECTION",
        f"Add Fixed Dataset reconciled: {accepted_changes} accepted corrections, {rejected_changes} rejected. {green_count} now GREEN ({green_pct}%)."
    )

    return {
        "accepted_changes": accepted_changes,
        "rejected_changes": rejected_changes,
        "reconciled_records": len(set(reconciled_serials)),
        "green_count": green_count,
        "red_count": red_count,
        "green_percentage": green_pct,
        "red_percentage": red_pct
    }
