"""Invoice API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invoice",
)
async def create_invoice(
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Create a new GST-compliant invoice."""
    invoice = await invoice_service.create_invoice(
        db,
        institution_id=body.institution_id,
        subtotal=body.subtotal,
        payment_id=body.payment_id,
        buyer_gstin=body.buyer_gstin,
        buyer_state_code=body.buyer_state_code,
    )
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Retrieve a single invoice by its ID."""
    invoice = await invoice_service.get_invoice_by_id(db, invoice_id)
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
)
async def list_invoices(
    institution_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> InvoiceListResponse:
    """Return a paginated list of invoices."""
    items, total = await invoice_service.list_invoices(
        db,
        institution_id=institution_id,
        page=page,
        size=size,
    )
    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "/{invoice_id}/regenerate",
    response_model=InvoiceResponse,
    summary="Regenerate invoice PDF",
)
async def regenerate_invoice_pdf(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Regenerate the PDF for an existing invoice and upload to R2."""
    invoice = await invoice_service.regenerate_invoice_pdf(db, invoice_id)
    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update an invoice",
)
async def update_invoice(
    invoice_id: uuid.UUID,
    body: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Update invoice status, buyer GSTIN, or PDF key."""
    invoice = await invoice_service.update_invoice(
        db,
        invoice_id,
        status=body.status,
        buyer_gstin=body.buyer_gstin,
        r2_pdf_key=body.r2_pdf_key,
    )
    return InvoiceResponse.model_validate(invoice)
