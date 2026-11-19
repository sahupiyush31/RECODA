import os
import re
import math
from typing import Optional, Any, Dict, List
import pandas as pd
import numpy as np

def get_api_key() -> Optional[str]:
    """
    Checks api_key.txt in the workspace root, backend dir, or environment variables.
    Returns cleaned key string if present, else None.
    """
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "api_key.txt"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "api_key.txt"),
        os.path.abspath("api_key.txt"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Might be format KEY=value or bare key
                            if "=" in line:
                                parts = line.split("=", 1)
                                return parts[1].strip().strip('"').strip("'")
                            return line
            except Exception:
                pass
                
    for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]:
        if os.environ.get(env_var):
            return os.environ.get(env_var).strip()
            
    return None

def generate_serial(index: int) -> str:
    """Generates a stable DataFix serial number scoped to record index: DFX-000001, etc."""
    return f"DFX-{index + 1:06d}"

def clean_record_for_json(record: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures NaN, NaT, None, Inf are converted to None or clean strings for JSON serialization."""
    cleaned = {}
    for k, v in record.items():
        try:
            is_na = pd.isna(v)
            # pd.isna on a list/array returns an array; treat as not-NA in that case
            if isinstance(is_na, (bool, np.bool_)):
                if is_na or v is None:
                    cleaned[k] = None
                    continue
        except (TypeError, ValueError):
            pass
        if v is None:
            cleaned[k] = None
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            cleaned[k] = None
        elif isinstance(v, (pd.Timestamp, np.datetime64)):
            cleaned[k] = str(v)
        else:
            cleaned[k] = v
    return cleaned

def clean_df_for_json(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records = df.to_dict(orient="records")
    return [clean_record_for_json(r) for r in records]
