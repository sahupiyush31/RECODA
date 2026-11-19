import os
import uuid
import json
import shutil
import numpy as np
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from app.models.db import (
    insert_dataset, get_dataset, get_records_metadata,
    get_audit_trail, get_recent_activities, log_activity,
    update_dataset_stats, save_record_metadata_batch, log_audit
)
from app.services.profiling import analyze_dataset_pipeline
from app.services.reconciliation import reconcile_fixed_dataset
from app.services.ai_explainer import generate_ai_diagnosis
from app.services.detectors import detect_row_issues, find_dataset_duplicates, calculate_outlier_bounds
from app.utils.helpers import clean_df_for_json, get_api_key, generate_serial

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

@router.get("/health")
def health_check():
    api_key_present = get_api_key() is not None
    return {
        "status": "healthy",
        "service": "RECODA Engine",
        "api_key_configured": api_key_present
    }

@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or "dataset.csv"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv, .xlsx, or .xls")

    # Normalize .xls -> .xlsx: openpyxl always writes modern xlsx binary regardless
    # of extension, so storing as .xls would produce a corrupt/unreadable file on export.
    save_ext = ".xlsx" if ext == ".xls" else ext

    dataset_id = f"ds_{uuid.uuid4().hex[:10]}"
    orig_path = os.path.join(UPLOADS_DIR, f"{dataset_id}_original{save_ext}")
    working_path = os.path.join(UPLOADS_DIR, f"{dataset_id}_working{save_ext}")

    # Save original file
    with open(orig_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # If original was .xls, re-read and re-save as proper .xlsx binary
    if ext == ".xls":
        try:
            _xls_df = pd.read_excel(orig_path, dtype=object)
            os.remove(orig_path)
            _xls_df.to_excel(orig_path, index=False)
        except Exception:
            pass  # If conversion fails, leave original in place; pandas will still read it

    # Duplicate as working file
    shutil.copyfile(orig_path, working_path)

    # Ingest with pandas to inspect
    try:
        if ext == ".csv":
            df = pd.read_csv(orig_path, dtype=object)
        else:
            df = pd.read_excel(orig_path, dtype=object)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    total_records = len(df)
    cols = [str(c) for c in df.columns]

    dataset_dict = {
        "id": dataset_id,
        "filename": filename,
        "file_type": save_ext.lstrip("."),
        "upload_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": total_records,
        "total_columns": len(cols),
        "columns": cols,
        "green_count": 0,
        "red_count": 0,
        "green_percentage": 0.0,
        "red_percentage": 0.0,
        "analysis_status": "uploaded",
        "original_file_path": orig_path,
        "working_file_path": working_path
    }
    insert_dataset(dataset_dict)
    log_activity(dataset_id, "UPLOAD", f"Dataset '{filename}' ({total_records} records, {len(cols)} columns) uploaded.")

    # Automatically analyze immediately after upload (Section 3.2: Start profiling after upload)
    analysis_result = analyze_dataset_pipeline(dataset_id, working_path)

    updated = get_dataset(dataset_id)
    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "message": "Dataset uploaded and analyzed successfully.",
        "summary": updated,
        "analysis": analysis_result
    }

@router.post("/datasets/{dataset_id}/analyze")
def trigger_analysis(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    res = analyze_dataset_pipeline(dataset_id, dataset["working_file_path"])
    return res

@router.get("/datasets/{dataset_id}/summary")
def get_dataset_summary(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    # Recent activities
    activities = get_recent_activities(dataset_id, limit=8)

    # Top issues for AI diagnosis
    meta = get_records_metadata(dataset_id)
    issues_samples = []
    for m in meta:
        for iss in m.get("issues", []):
            issues_samples.append(f"{iss['column']}: {iss['description']}")
            if len(issues_samples) >= 5:
                break
        if len(issues_samples) >= 5:
            break

    ai_diagnosis = generate_ai_diagnosis(
        dataset_name=dataset["filename"],
        total_records=dataset["total_records"],
        green_count=dataset["green_count"],
        red_count=dataset["red_count"],
        top_issues=issues_samples
    )

    return {
        **dataset,
        "activities": activities,
        "ai_diagnosis": ai_diagnosis
    }

@router.get("/datasets/{dataset_id}/records/green")
def get_green_records(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    meta = get_records_metadata(dataset_id)
    green_indices = [m["record_index"] for m in meta if not m["human_required"]]

    working_path = dataset["working_file_path"]
    df = pd.read_csv(working_path, dtype=object) if working_path.endswith(".csv") else pd.read_excel(working_path, dtype=object)

    green_df = df.iloc[green_indices] if len(green_indices) > 0 else pd.DataFrame(columns=df.columns)
    records = clean_df_for_json(green_df)

    return {
        "dataset_id": dataset_id,
        "category": "GREEN",
        "total_count": len(records),
        "columns": dataset["columns"], # Original user columns only
        "records": records
    }

@router.get("/datasets/{dataset_id}/records/red")
def get_red_records(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    meta = get_records_metadata(dataset_id)
    red_meta = [m for m in meta if m["human_required"]]
    red_indices = [m["record_index"] for m in red_meta]

    working_path = dataset["working_file_path"]
    df = pd.read_csv(working_path, dtype=object) if working_path.endswith(".csv") else pd.read_excel(working_path, dtype=object)

    red_records = []
    for m in red_meta:
        idx = m["record_index"]
        row_dict = df.iloc[idx].to_dict()
        # Safely clean values — guard against non-scalar (list/array) types that
        # would cause pd.isna() to return an array and raise ValueError
        for k, v in row_dict.items():
            is_na = False
            if v is None:
                is_na = True
            else:
                try:
                    result = pd.isna(v)
                    if isinstance(result, (bool, np.bool_)) and result:
                        is_na = True
                except (TypeError, ValueError):
                    pass
            row_dict[k] = "" if is_na else str(v)

        red_records.append({
            "record_index": idx,
            "datafix_serial": m["datafix_serial"],
            "issues": m["issues"],
            "validation_status": m["validation_status"],
            "data": row_dict
        })

    return {
        "dataset_id": dataset_id,
        "category": "RED",
        "total_count": len(red_records),
        "columns": dataset["columns"],
        "records": red_records
    }

@router.get("/datasets/{dataset_id}/export/fixed")
def export_fixed_data(dataset_id: str):
    """
    Downloads ONLY records that are currently GREEN and have passed validation.
    Preserves original columns only, omitting all DataFix internal metadata.
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    meta = get_records_metadata(dataset_id)
    green_indices = [m["record_index"] for m in meta if not m["human_required"]]

    if len(green_indices) == 0:
        raise HTTPException(status_code=400, detail="No validated GREEN records available for export.")

    working_path = dataset["working_file_path"]
    df = pd.read_csv(working_path, dtype=object) if working_path.endswith(".csv") else pd.read_excel(working_path, dtype=object)
    
    # Original user columns only
    user_cols = dataset["columns"]
    green_df = df.iloc[green_indices][user_cols]

    ext = dataset["file_type"]
    export_filename = f"fixed_{dataset['filename']}"
    export_path = os.path.join(EXPORTS_DIR, f"{dataset_id}_fixed.{ext}")

    if ext == "csv":
        green_df.to_csv(export_path, index=False)
        media_type = "text/csv"
    else:
        green_df.to_excel(export_path, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(export_path, filename=export_filename, media_type=media_type)

@router.get("/datasets/{dataset_id}/export/green")
def export_green_dataset(dataset_id: str):
    """Downloads GREEN records with original columns only."""
    return export_fixed_data(dataset_id)

@router.get("/datasets/{dataset_id}/export/red")
def export_red_dataset(dataset_id: str, for_correction: bool = Query(True, description="Include DataFix serial numbers for reconciliation template")):
    """
    Downloads RED records.
    If for_correction=True, includes DataFix_Serial column for Add Fixed Dataset reconciliation.
    If for_correction=False, preserves original columns only.
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    meta = get_records_metadata(dataset_id)
    red_meta = [m for m in meta if m["human_required"]]
    if len(red_meta) == 0:
        raise HTTPException(status_code=400, detail="No RED records requiring human intervention.")

    red_indices = [m["record_index"] for m in red_meta]
    working_path = dataset["working_file_path"]
    df = pd.read_csv(working_path, dtype=object) if working_path.endswith(".csv") else pd.read_excel(working_path, dtype=object)
    
    user_cols = dataset["columns"]
    red_df = df.iloc[red_indices][user_cols].copy()

    ext = dataset["file_type"]
    if for_correction:
        # Insert DataFix_Serial as the first column for reconciliation matching
        serials = [m["datafix_serial"] for m in red_meta]
        red_df.insert(0, "DataFix_Serial", serials)
        export_filename = f"red_correction_template_{dataset['filename']}"
    else:
        export_filename = f"red_records_{dataset['filename']}"

    export_path = os.path.join(EXPORTS_DIR, f"{dataset_id}_red_{'template' if for_correction else 'clean'}.{ext}")

    if ext == "csv":
        red_df.to_csv(export_path, index=False)
        media_type = "text/csv"
    else:
        red_df.to_excel(export_path, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(export_path, filename=export_filename, media_type=media_type)

@router.post("/datasets/{dataset_id}/add-fix")
async def add_fix_dataset(dataset_id: str, file: UploadFile = File(...)):
    """
    Reconciles uploaded corrected file using DataFix serial numbers.
    Safeguards: serial validation, partial resolution revalidation, audit tracking.
    """
    filename = file.filename or "fixed_correction.csv"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv or .xlsx")

    upload_temp = os.path.join(UPLOADS_DIR, f"reconcile_{dataset_id}_{uuid.uuid4().hex[:6]}{ext}")
    with open(upload_temp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = reconcile_fixed_dataset(dataset_id, upload_temp)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation error: {str(e)}")
    finally:
        if os.path.exists(upload_temp):
            try:
                os.remove(upload_temp)
            except Exception:
                pass

    return {
        "message": "Reconciliation completed successfully.",
        **result
    }

@router.get("/datasets/{dataset_id}/audit")
def get_audit(dataset_id: str):
    trail = get_audit_trail(dataset_id)
    return {
        "dataset_id": dataset_id,
        "total_events": len(trail),
        "audit_logs": trail
    }

@router.post("/datasets/{dataset_id}/rollback")
def rollback_change(dataset_id: str, audit_id: int = Form(...)):
    """
    Rolls back an accepted modification to its previous working value.
    Re-runs validation and logs rollback event.
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    trail = get_audit_trail(dataset_id)
    target_event = next((e for e in trail if e["id"] == audit_id), None)
    if not target_event:
        raise HTTPException(status_code=404, detail="Audit event not found.")

    serial = target_event["datafix_serial"]
    col = target_event["column_name"]
    old_val = target_event["old_value"]
    current_val = target_event["new_value"]

    # Locate record in working dataset
    meta = get_records_metadata(dataset_id)
    rec_meta = next((m for m in meta if m["datafix_serial"] == serial), None)
    if not rec_meta:
        raise HTTPException(status_code=404, detail="Target record not found.")

    idx = rec_meta["record_index"]
    working_path = dataset["working_file_path"]
    df = pd.read_csv(working_path, dtype=object) if working_path.endswith(".csv") else pd.read_excel(working_path, dtype=object)

    # Revert value
    df.at[idx, col] = old_val if old_val != "" else None
    if working_path.endswith(".csv"):
        df.to_csv(working_path, index=False)
    else:
        df.to_excel(working_path, index=False)

    # Log rollback
    log_audit(
        dataset_id=dataset_id,
        serial=serial,
        col=col,
        old_val=current_val,
        new_val=old_val,
        actor="Human",
        reason=f"Rollback of event #{audit_id}",
        val_result="reverted"
    )
    log_activity(dataset_id, "ROLLBACK", f"Reverted change for record {serial} on column '{col}'.")

    # Re-run issue detection and revalidation
    duplicate_indices = find_dataset_duplicates(df)
    outlier_bounds = calculate_outlier_bounds(df)

    # Build a lookup by record_index to avoid positional-index desync bugs
    meta_by_index = {m["record_index"]: m["datafix_serial"] for m in meta}

    updated_meta = []
    total_records = len(df)
    for i in range(total_records):
        r_row = df.iloc[i]
        r_serial = meta_by_index.get(i, generate_serial(i))
        r_issues = detect_row_issues(r_row, i, df, duplicate_indices, outlier_bounds)
        has_human = any(iss["repair_method"] == "human" for iss in r_issues)
        updated_meta.append({
            "record_index": i,
            "datafix_serial": r_serial,
            "human_required": has_human,
            "validation_status": "needs_human_review" if has_human else "valid",
            "issues": r_issues
        })
    save_record_metadata_batch(dataset_id, updated_meta)

    green_count = sum(1 for r in updated_meta if not r["human_required"])
    red_count = total_records - green_count
    green_pct = round((green_count / total_records) * 100, 1) if total_records > 0 else 0.0
    red_pct = round((red_count / total_records) * 100, 1) if total_records > 0 else 0.0

    update_dataset_stats(
        dataset_id=dataset_id,
        total_records=total_records,
        total_columns=len(df.columns),
        columns=[str(c) for c in df.columns],
        green_count=green_count,
        red_count=red_count,
        green_pct=green_pct,
        red_pct=red_pct,
        status="analyzed"
    )

    return {
        "message": f"Successfully rolled back {serial} on {col}.",
        "green_count": green_count,
        "red_count": red_count,
        "green_percentage": green_pct,
        "red_percentage": red_pct
    }
