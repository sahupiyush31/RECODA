import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Critical columns where values must NEVER be fabricated or guessed
CRITICAL_KEYWORDS = [
    "salary", "wage", "compensation", "income", "pay",
    "id", "identifier", "ssn", "code", "serial", "national_id",
    "name", "first_name", "last_name", "employee_name", "customer_name",
    "email", "phone", "account", "tax", "dob", "birth"
]

NON_NEGATIVE_NUMERIC_KEYWORDS = [
    "salary", "age", "quantity", "price", "amount", "cost", "hours", "experience", "inventory"
]

def is_critical_column(col_name: str) -> bool:
    clean_col = col_name.lower().replace(" ", "_").replace("-", "_")
    return any(kw in clean_col for kw in CRITICAL_KEYWORDS)

def is_non_negative_column(col_name: str) -> bool:
    clean_col = col_name.lower().replace(" ", "_").replace("-", "_")
    return any(kw in clean_col for kw in NON_NEGATIVE_NUMERIC_KEYWORDS)

def is_missing(val: Any) -> bool:
    if val is None:
        return True
    try:
        result = pd.isna(val)
        # pd.isna on a list/array returns an array; only trust scalar bool results
        if isinstance(result, (bool, np.bool_)) and result:
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(val, str):
        cleaned = val.strip().lower()
        if cleaned in ["", "nan", "null", "none", "n/a", "na", "-", "--", "undefined"]:
            return True
    return False

def parse_date_unambiguous(val: Any) -> Tuple[bool, Optional[str], bool]:
    """
    Returns (is_date_candidate, standardized_iso_str, is_ambiguous_or_invalid)
    Standardizes valid dates to YYYY-MM-DD.
    If multiple formats produce conflicting interpretations (e.g. 01/02/2024
    could be Jan-02 or Feb-01), flags as ambiguous rather than silently picking one.
    """
    if val is None:
        return False, None, False
    try:
        if pd.isna(val):
            return False, None, False
    except (TypeError, ValueError):
        pass

    s = str(val).strip()
    if len(s) < 6 or len(s) > 30:
        return False, None, False

    # Check for known invalid dates like 2024-02-31 or 99/99/9999
    if re.search(r"(\b99[/-]99|\b00[/-]00|\b3[2-9]|\b[1-9]\d{3}[/-]02[/-]3[01])", s):
        return True, None, True

    # Try standard patterns; collect all successful interpretations
    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%m/%d/%Y", "%m-%d-%Y",
        "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"
    ]

    results = []
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.year < 1900 or dt.year > 2100:
                return True, None, True
            results.append(dt.strftime("%Y-%m-%d"))
        except (ValueError, TypeError):
            continue

    if results:
        unique_results = set(results)
        if len(unique_results) == 1:
            # All matching formats agree — unambiguous
            return True, results[0], False
        else:
            # Multiple conflicting interpretations (e.g. dd/mm vs mm/dd) — flag as ambiguous
            return True, None, True

    # If it strongly looks like a date string (has slashes/hyphens and digits) but failed
    if re.match(r"^\d{1,4}[/-]\d{1,2}[/-]\d{1,4}", s):
        return True, None, True

    return False, None, False

def detect_row_issues(row: pd.Series, row_index: int, df: pd.DataFrame, duplicate_indices: Dict[int, List[int]], outlier_cols: Dict[str, Tuple[float, float]]) -> List[Dict[str, Any]]:
    """
    Evaluates a single row against all modular detectors.
    Returns list of issue dictionaries.
    """
    issues = []

    # 1. Duplicate detection
    if row_index in duplicate_indices:
        other_idx = duplicate_indices[row_index][0]
        issues.append({
            "column": "Record",
            "issue_type": "duplicate",
            "description": f"Potential duplicate record matching internal record #{other_idx + 1}. Detect and explain; cannot merge/delete automatically.",
            "repair_method": "human",
            "suggested_action": "Verify if this is an intentional repeat or duplicate."
        })

    # Column-level detectors
    for col in df.columns:
        val = row[col]
        col_str = str(col)
        
        # 2. Missing Value Detector
        if is_missing(val):
            critical = is_critical_column(col_str)
            if critical:
                desc = f"'{col_str}' is blank/missing. Critical field; system cannot fabricate real-world facts."
            else:
                desc = f"Missing value in '{col_str}'. Human intervention required."
                
            issues.append({
                "column": col_str,
                "issue_type": "missing_value",
                "description": desc,
                "repair_method": "human",
                "suggested_action": f"Provide valid value for {col_str}."
            })
            continue # If missing, skip other checks for this cell

        # 3. Extra Whitespace Detector (Safe AI Rule)
        if isinstance(val, str):
            has_leading_trailing = val != val.strip()
            has_double_spaces = "  " in val
            if has_leading_trailing or has_double_spaces:
                issues.append({
                    "column": col_str,
                    "issue_type": "whitespace",
                    "description": f"Extra/irregular whitespace detected in '{col_str}'.",
                    "repair_method": "safe_ai_rule",
                    "suggested_action": "Trim leading/trailing/multiple spaces."
                })

        # 4. Date Format Inconsistency & Invalid Date Detector
        is_candidate_date = "date" in col_str.lower() or "time" in col_str.lower() or "dob" in col_str.lower()
        if is_candidate_date or isinstance(val, str):
            is_date, std_iso, is_invalid = parse_date_unambiguous(val)
            if is_date:
                if is_invalid:
                    issues.append({
                        "column": col_str,
                        "issue_type": "date_format",
                        "description": f"Invalid or ambiguous date representation '{val}' in '{col_str}'.",
                        "repair_method": "human",
                        "suggested_action": "Correct to valid calendar date (YYYY-MM-DD)."
                    })
                elif str(val).strip() != std_iso:
                    # Unambiguous date that is not standard ISO YYYY-MM-DD
                    issues.append({
                        "column": col_str,
                        "issue_type": "date_format",
                        "description": f"Date '{val}' in '{col_str}' can be safely standardized to '{std_iso}'.",
                        "repair_method": "safe_ai_rule",
                        "suggested_action": f"Convert format to {std_iso}."
                    })

        # 5. Suspicious Numeric Value & Outlier Detector
        numeric_val = None
        if isinstance(val, (int, float, np.integer, np.floating)) and not pd.isna(val):
            numeric_val = float(val)
        elif isinstance(val, str) and re.match(r"^-?\d+(\.\d+)?$", val.strip()):
            try:
                numeric_val = float(val.strip())
            except ValueError:
                pass

        if numeric_val is not None:
            col_lower = col_str.lower()
            # Check unreasonable age first (before generic non-negative check,
            # since "age" is in NON_NEGATIVE_NUMERIC_KEYWORDS and would be caught
            # by the non-negative branch before we could check > 120)
            if "age" in col_lower and (numeric_val < 0 or numeric_val > 120):
                issues.append({
                    "column": col_str,
                    "issue_type": "suspicious_numeric",
                    "description": f"Unrealistic age value ({numeric_val}) in '{col_str}'.",
                    "repair_method": "human",
                    "suggested_action": "Check age records."
                })
            # Check negative where impossible (non-age columns)
            elif is_non_negative_column(col_str) and numeric_val < 0:
                issues.append({
                    "column": col_str,
                    "issue_type": "suspicious_numeric",
                    "description": f"Suspicious negative value ({numeric_val}) in '{col_str}'. Flagged for review; cannot silently overwrite.",
                    "repair_method": "human",
                    "suggested_action": "Verify and provide non-negative figure."
                })
            # Check statistical anomaly
            elif col_str in outlier_cols:
                low_b, high_b = outlier_cols[col_str]
                if numeric_val < low_b or numeric_val > high_b:
                    issues.append({
                        "column": col_str,
                        "issue_type": "anomaly",
                        "description": f"Statistical outlier ({numeric_val}) in '{col_str}' outside normal range [{low_b:.1f}, {high_b:.1f}]. Flagged for human review.",
                        "repair_method": "human",
                        "suggested_action": "Review whether outlier is genuine."
                    })

        # 6. Format check for email
        if "email" in col_str.lower() and isinstance(val, str) and not is_missing(val):
            clean_email = val.strip()
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
                issues.append({
                    "column": col_str,
                    "issue_type": "invalid_format",
                    "description": f"Malformed email address '{val}' in '{col_str}'.",
                    "repair_method": "human",
                    "suggested_action": "Provide valid email syntax user@domain.com."
                })

    return issues

def find_dataset_duplicates(df: pd.DataFrame) -> Dict[int, List[int]]:
    """Finds exact duplicate rows or candidate duplicates across all records in the group."""
    duplicate_map = {}
    try:
        dups = df.duplicated(keep=False)
        if dups.any():
            grouped = df.groupby(list(df.columns), dropna=False).indices
            for key, indices in grouped.items():
                if len(indices) > 1:
                    for idx in indices:
                        other_ids = [int(i) for i in indices if i != idx]
                        duplicate_map[int(idx)] = other_ids
    except Exception:
        pass
    return duplicate_map

def calculate_outlier_bounds(df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """Calculates IQR outlier boundaries for numeric columns."""
    outlier_bounds = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()
            if len(series) >= 10:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    low = q1 - 3.0 * iqr
                    high = q3 + 3.0 * iqr
                    outlier_bounds[str(col)] = (float(low), float(high))
    return outlier_bounds
