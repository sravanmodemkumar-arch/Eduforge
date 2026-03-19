"""Pydantic schemas for invoice endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.invoice import InvoiceStatus


# ── Request schemas ──────────────────────────────────────────────────────


class InvoiceCreate(BaseModel):
    """Request body for creating an invoice."""

    institution_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    subtotal: float = Field(..., gt=0)
    buyer_gstin: str | None = Field(None, max_length=15)
    buyer_state_code: str | None = Field(
        None,
        max_length=2,
        description="Two-digit state code; determines intra- vs inter-state GST.",
    )


class InvoiceUpdate(BaseModel):
    """Request body for updating an invoice."""

    status: InvoiceStatus | None = None
    buyer_gstin: str | None = Field(None, max_length=15)
    r2_pdf_key: str | None = None


# ── Response schemas ─────────────────────────────────────────────────────


class InvoiceResponse(BaseModel):
    """Standard invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    invoice_number: str
    payment_id: uuid.UUID | None = None
    subtotal: float
    cgst: float
    sgst: float
    igst: float
    total: float
    sac_code: str
    hsn_code: str | None = None
    buyer_gstin: str | None = None
    seller_gstin: str | None = None
    r2_pdf_key: str | None = None
    status: InvoiceStatus
    issued_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    items: list[InvoiceResponse]
    total: int
    page: int
    size: int
