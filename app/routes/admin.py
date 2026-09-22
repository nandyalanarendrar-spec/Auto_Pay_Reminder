from fastapi import APIRouter, Depends, status
from app.core.security import require_admin
from app.schemas.admin import AdminStatsResponse, SystemHealthResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Dashboard & System Health"])

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system-level aggregate stats (Admin Protected)"
)
def get_admin_stats(
    current_user: dict = Depends(require_admin)
):
    """
    Returns aggregate system-level counts (total users, active subscriptions, EMIs, trials, high-risk flags).
    Protected by `require_admin` dependency (HTTP 403 for non-admins).
    Exposes NO individual user financial data.
    """
    res = AdminService.get_aggregate_stats()
    return res

@router.get(
    "/system-health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system health, uptime, and background job statuses (Admin Protected)"
)
def get_system_health(
    current_user: dict = Depends(require_admin)
):
    """
    Returns API health status, error rates, system uptime, and background job runner statuses.
    Protected by `require_admin` dependency.
    """
    res = AdminService.get_system_health()
    return res



