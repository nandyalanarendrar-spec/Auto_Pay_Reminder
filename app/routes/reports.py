from fastapi import APIRouter, Depends, Query, Response, status
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
    current_user: dict = Depends(get_current_user)
):
    """
    Generates downloadable report for the signed-in user's subscriptions, EMIs, and financial safety score.
    Formats available: `csv` or `pdf`.
    All amounts formatted in Indian Rupees (₹).
    """
    clean_user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id

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
