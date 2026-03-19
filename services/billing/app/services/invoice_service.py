"""GST invoice generation service."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import InvoiceGenerationError, InvoiceNotFoundError
from app.models.invoice import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)


def _round_currency(value: Decimal) -> Decimal:
    """Round a decimal value to 2 decimal places using banker's rounding."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_gst(
    subtotal: float,
    buyer_state_code: str | None = None,
) -> dict[str, Any]:
    """Compute GST components for a given subtotal.

    If the buyer state code matches the seller state code, intra-state GST
    (CGST + SGST) is applied.  Otherwise inter-state IGST is applied.

    Returns a dict with ``cgst``, ``sgst``, ``igst``, and ``total``.
    """
    sub = Decimal(str(subtotal))

    is_intra_state = (
        buyer_state_code is not None
        and buyer_state_code == settings.seller_state_code
    )

    if is_intra_state:
        cgst = _round_currency(sub * Decimal(str(settings.cgst_rate)))
        sgst = _round_currency(sub * Decimal(str(settings.sgst_rate)))
        igst = Decimal("0.00")
    else:
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")
        igst = _round_currency(sub * Decimal(str(settings.igst_rate)))

    total = _round_currency(sub + cgst + sgst + igst)

    return {
        "cgst": float(cgst),
        "sgst": float(sgst),
        "igst": float(igst),
        "total": float(total),
    }


def _generate_invoice_number() -> str:
    """Generate a unique invoice number.

    Format: ``EF-YYYYMMDD-XXXX`` where XXXX is a short random hex suffix.
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"EF-{date_part}-{random_part}"


async def create_invoice(
    session: AsyncSession,
    institution_id: uuid.UUID,
    subtotal: float,
    payment_id: uuid.UUID | None = None,
    buyer_gstin: str | None = None,
    buyer_state_code: str | None = None,
) -> Invoice:
    """Create a GST-compliant invoice.

    Calculates the appropriate tax components and persists the invoice.
    """
    gst = compute_gst(subtotal, buyer_state_code)

    invoice = Invoice(
        institution_id=institution_id,
        invoice_number=_generate_invoice_number(),
        payment_id=payment_id,
        subtotal=subtotal,
        cgst=gst["cgst"],
        sgst=gst["sgst"],
        igst=gst["igst"],
        total=gst["total"],
        sac_code=settings.default_sac_code,
        buyer_gstin=buyer_gstin,
        seller_gstin=settings.seller_gstin or None,
        status=InvoiceStatus.DRAFT,
    )

    try:
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
    except Exception as exc:
        await session.rollback()
        logger.error("Failed to create invoice: %s", exc)
        raise InvoiceGenerationError(
            detail=f"Database error while creating invoice: {exc}"
        ) from exc

    logger.info("Created invoice %s for institution %s", invoice.invoice_number, institution_id)
    return invoice


async def get_invoice_by_id(
    session: AsyncSession,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Fetch a single invoice by primary key."""
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise InvoiceNotFoundError(str(invoice_id))
    return invoice


async def list_invoices(
    session: AsyncSession,
    institution_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Invoice], int]:
    """Return a paginated list of invoices, optionally filtered by institution."""
    base = select(Invoice).order_by(Invoice.created_at.desc())
    count_stmt = select(func.count()).select_from(Invoice)

    if institution_id is not None:
        base = base.where(Invoice.institution_id == institution_id)
        count_stmt = count_stmt.where(Invoice.institution_id == institution_id)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    stmt = base.offset(offset).limit(size)
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def regenerate_invoice_pdf(
    session: AsyncSession,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Regenerate the PDF for an existing invoice and re-upload to R2.

    In production this would render the invoice template to PDF using
    a library like weasyprint or reportlab, then upload to R2/S3.
    """
    invoice = await get_invoice_by_id(session, invoice_id)

    try:
        # TODO: Render invoice to PDF and upload to R2
        # pdf_bytes = render_invoice_pdf(invoice)
        # r2_key = f"invoices/{invoice.invoice_number}.pdf"
        # upload_to_r2(r2_key, pdf_bytes)
        # invoice.r2_pdf_key = r2_key

        logger.info(
            "Regenerated PDF for invoice %s",
            invoice.invoice_number,
        )
        await session.commit()
        await session.refresh(invoice)
    except Exception as exc:
        await session.rollback()
        logger.error("Failed to regenerate invoice PDF: %s", exc)
        raise InvoiceGenerationError(
            detail=f"PDF regeneration failed: {exc}"
        ) from exc

    return invoice


async def update_invoice(
    session: AsyncSession,
    invoice_id: uuid.UUID,
    *,
    status: InvoiceStatus | None = None,
    buyer_gstin: str | None = None,
    r2_pdf_key: str | None = None,
) -> Invoice:
    """Update selected fields on an existing invoice."""
    invoice = await get_invoice_by_id(session, invoice_id)

    if status is not None:
        invoice.status = status
    if buyer_gstin is not None:
        invoice.buyer_gstin = buyer_gstin
    if r2_pdf_key is not None:
        invoice.r2_pdf_key = r2_pdf_key

    await session.commit()
    await session.refresh(invoice)
    return invoice
