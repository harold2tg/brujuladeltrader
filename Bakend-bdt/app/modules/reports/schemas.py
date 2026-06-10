"""Pydantic schemas for reports responses."""

from pydantic import BaseModel


class UploadInfo(BaseModel):
    """Basic upload information for reports."""
    id: str
    original_name: str
    status: str
    total_trades: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    period_label: str | None = None


class PeriodInfo(BaseModel):
    """Period information for the report."""
    year: int
    month: int | None = None
    label: str


class Insight(BaseModel):
    """Single insight entry."""
    type: str  # info, warning, critical, success
    title: str
    text: str
    severity: str  # low, medium, high


class MonthlyReportData(BaseModel):
    """Monthly report data."""
    upload_info: UploadInfo
    period: PeriodInfo
    metrics: dict
    insights: list[Insight]
    summary: str


class AnnualReportData(BaseModel):
    """Annual report data."""
    upload_info: UploadInfo
    period: PeriodInfo
    monthly_breakdown: list[dict]
    annual_summary: dict
    insights: list[Insight]


class ExportRequest(BaseModel):
    """Export request body."""
    year: int
    month: int | None = None
    language: str = "es"


class JobStatusData(BaseModel):
    """PDF generation job status."""
    status: str  # processing, completed, failed
    download_url: str | None = None
    error: str | None = None
