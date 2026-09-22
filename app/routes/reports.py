from fastapi import APIRouter, Depends, Query, Response, Header, status
from typing import Optional
from app.core.security import get_current_user
from app.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["Financial Reports & Export"])

@router.get(
    "/export",
    summary="Export downloadable financial summary report (CSV or PDF)"
)
def export_report(
    format: str = Query("csv", description="Export format: csv or pdf"),
    user_id: Optional[str] = Query(None, description="Optional user ID"),
    authorization: Optional[str] = Header(None)
):
    """
    Generates downloadable report for user's subscriptions, EMIs, and financial safety score.
    Formats available: `csv` or `pdf`.
    All amounts formatted in Indian Rupees (₹).
    """
    clean_user_id = user_id or "user_123"
    
    # Extract user ID from token if provided
    if authorization and authorization.startswith("Bearer "):
        try:
            from app.core.security import verify_jwt_token
            token = authorization.split(" ")[1]
            payload = verify_jwt_token(token)
            clean_user_id = payload.get("sub") or payload.get("id") or clean_user_id
        except Exception:
            pass

    fmt = (format or "csv").lower().strip()

    if fmt == "pdf":
        pdf_bytes, filename = ReportsService.generate_pdf_summary_report(clean_user_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    else:
        content, filename = ReportsService.generate_csv_report(clean_user_id)
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
