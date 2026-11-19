import re
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
from app.services.detectors import parse_date_unambiguous
from app.models.db import log_audit, log_activity

def apply_safe_repairs(df: pd.DataFrame, dataset_id: str, records_meta: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[Dict[str, Any]], int]:
    """
    Applies safe deterministic repairs to the working dataframe.
    Records every applied change in the audit trail.
    Updates records metadata (removes resolved safe issues).
    Returns (working_df, updated_records_meta, repairs_count).
    """
    working_df = df.copy()
    repairs_count = 0

    for r_meta in records_meta:
        idx = r_meta["record_index"]
        serial = r_meta["datafix_serial"]
        remaining_issues = []

        for issue in r_meta.get("issues", []):
            col = issue["column"]
            method = issue["repair_method"]
            issue_type = issue["issue_type"]

            if method == "safe_ai_rule" and col in working_df.columns:
                old_val = working_df.at[idx, col]
                new_val = old_val
                applied = False

                # 1. Whitespace safe repair
                if issue_type == "whitespace" and isinstance(old_val, str):
                    new_val = re.sub(r"\s+", " ", old_val.strip())
                    applied = True

                # 2. Date format safe repair
                elif issue_type == "date_format":
                    is_date, std_iso, is_invalid = parse_date_unambiguous(old_val)
                    if is_date and not is_invalid and std_iso:
                        new_val = std_iso
                        applied = True

                if applied and str(old_val) != str(new_val):
                    working_df.at[idx, col] = new_val
                    repairs_count += 1
                    log_audit(
                        dataset_id=dataset_id,
                        serial=serial,
                        col=col,
                        old_val=old_val,
                        new_val=new_val,
                        actor="AI",
                        reason=f"Safe AI repair: {issue_type} standardized",
                        val_result="passed"
                    )
                    # Issue is resolved! Do not add to remaining_issues
                else:
                    remaining_issues.append(issue)
            else:
                remaining_issues.append(issue)

        r_meta["issues"] = remaining_issues
        # Re-evaluate human_required status
        r_meta["human_required"] = any(iss["repair_method"] == "human" for iss in remaining_issues)
        if not r_meta["human_required"]:
            r_meta["validation_status"] = "valid" if len(remaining_issues) == 0 else "repaired_safe"
        else:
            r_meta["validation_status"] = "needs_human_review"

    if repairs_count > 0:
        log_activity(dataset_id, "SAFE_REPAIR", f"Automated engine applied {repairs_count} safe rule repairs.")

    return working_df, records_meta, repairs_count
