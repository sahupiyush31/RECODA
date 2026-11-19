from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class IssueDetail(BaseModel):
    column: str
    issue_type: str # 'missing_value', 'whitespace', 'date_format', 'duplicate', 'invalid_range', 'invalid_format'
    description: str
    repair_method: str # 'safe_ai_rule' or 'human'
    suggested_action: Optional[str] = None

class RecordItem(BaseModel):
    record_index: int
    datafix_serial: Optional[str] = None
    human_required: bool
    validation_status: str
    issues: List[IssueDetail] = []
    data: Dict[str, Any]

class DatasetSummary(BaseModel):
    dataset_id: str
    filename: str
    file_type: str
    upload_time: str
    total_records: int
    total_columns: int
    columns: List[str]
    green_count: int
    red_count: int
    green_percentage: float
    red_percentage: float
    analysis_status: str

class DatasetRecordsResponse(BaseModel):
    dataset_id: str
    category: str # 'GREEN' or 'RED'
    total_count: int
    columns: List[str]
    records: List[Dict[str, Any]]

class AuditLogItem(BaseModel):
    id: int
    dataset_id: str
    datafix_serial: str
    column_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    actor: str
    reason: Optional[str]
    timestamp: str
    validation_result: Optional[str]

class RollbackRequest(BaseModel):
    audit_id: int

class ActivityItem(BaseModel):
    id: int
    dataset_id: str
    event_type: str
    description: str
    timestamp: str
