"""Stateless banking pilot. Uses existing session/API-key authentication."""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends

from preflight.banking import DisbursementAnalysis, DisbursementCase, analyze_disbursement
from preflight.security.rbac import Role, require_role


router = APIRouter(prefix="/api/v1/banking", tags=["Banking preflight pilot"])


@router.post("/analyze", response_model=DisbursementAnalysis,
             dependencies=[Depends(require_role(Role.VIEWER))])
def analyze_case(payload: DisbursementCase) -> DisbursementAnalysis:
    """Check manually supplied VND data; does not persist, approve or disburse."""
    return analyze_disbursement(payload, as_of=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date())
