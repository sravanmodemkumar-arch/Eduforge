"""Invoice SQLAlchemy model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.payment import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""

    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Represents a GST-compliant invoice."""

    __tablename__ = "invoices"
    __table_args__ = {"schema": "billing"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing.payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )
    cgst: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0,
    )
    sgst: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0,
    )
    igst: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0,
    )
    total: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )
    sac_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="9993",
    )
    buyer_gstin: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )
    seller_gstin: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )
    r2_pdf_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status", schema="billing"),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    payment = relationship("Payment", foreign_keys=[payment_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} total={self.total}>"
