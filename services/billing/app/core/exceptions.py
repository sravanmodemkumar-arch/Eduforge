"""Custom exception classes for the billing service."""

from __future__ import annotations

from fastapi import HTTPException, status


class PaymentError(HTTPException):
    """Raised when a payment operation fails."""

    def __init__(self, detail: str = "Payment processing failed") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class PaymentNotFoundError(HTTPException):
    """Raised when a payment record cannot be found."""

    def __init__(self, payment_id: str | None = None) -> None:
        detail = f"Payment not found: {payment_id}" if payment_id else "Payment not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SignatureVerificationError(HTTPException):
    """Raised when Razorpay signature verification fails."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed",
        )


class SubscriptionNotFoundError(HTTPException):
    """Raised when a subscription record cannot be found."""

    def __init__(self, subscription_id: str | None = None) -> None:
        detail = (
            f"Subscription not found: {subscription_id}"
            if subscription_id
            else "Subscription not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvoiceNotFoundError(HTTPException):
    """Raised when an invoice record cannot be found."""

    def __init__(self, invoice_id: str | None = None) -> None:
        detail = (
            f"Invoice not found: {invoice_id}" if invoice_id else "Invoice not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvoiceGenerationError(HTTPException):
    """Raised when invoice generation fails."""

    def __init__(self, detail: str = "Invoice generation failed") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class WebhookError(HTTPException):
    """Raised when webhook processing fails."""

    def __init__(self, detail: str = "Webhook processing failed") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
