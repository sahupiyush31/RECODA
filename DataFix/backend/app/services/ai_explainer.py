import os
import json
from typing import Dict, Any, List, Optional
import requests
from app.utils.helpers import get_api_key

def generate_ai_diagnosis(dataset_name: str, total_records: int, green_count: int, red_count: int, top_issues: List[str]) -> str:
    """
    Generates an intelligent dataset quality summary and diagnosis.
    Uses Gemini API if an API key is available in api_key.txt, otherwise returns rule-based analysis.
    """
    api_key = get_api_key()
    
    # Deterministic fallback text
    fallback_summary = (
        f"DataFix Engine diagnosed dataset '{dataset_name}' with {total_records} total records. "
        f"Automated rule checks confirmed {green_count} records are valid or safely repaired ({round(green_count/max(1,total_records)*100,1)}%). "
        f"{red_count} records require human review due to uninferable fields (e.g. missing critical business values, ambiguous dates, or statistical outliers). "
        "Strict adherence to product principle: AI never fabricates missing financial, demographic, or identification facts."
    )
    
    if not api_key:
        return fallback_summary

    try:
        # Call Gemini REST API directly
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            f"You are the DataFix Autonomous Data Quality & Repair Engine AI. "
            f"Analyze this dataset diagnosis: Filename '{dataset_name}', Total records: {total_records}, "
            f"GREEN (clean/safely repaired): {green_count}, RED (human intervention required): {red_count}. "
            f"Detected issues: {', '.join(top_issues[:5]) if top_issues else 'None'}. "
            f"Provide a concise, professional 3-sentence summary highlighting what was safely standardized vs why human intervention was guarded."
        )
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 150,
                "temperature": 0.2
            }
        }
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if text.strip():
                    return text.strip()
    except Exception:
        pass

    return fallback_summary
