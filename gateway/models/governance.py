from pydantic import BaseModel, ConfigDict
from typing import Optional


class BudgetRequestCreate(BaseModel):
    requested_limit: float
    reason: str


class BudgetApprovalDecision(BaseModel):
    decision_reason: Optional[str] = None


class BudgetRequestItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    request_id: str
    team_id: str
    requester_id: str
    current_limit: float
    requested_limit: float
    reason: str
    status: str  # "pending", "approved", "denied"
    created_at: str
    approver_id: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_at: Optional[str] = None
