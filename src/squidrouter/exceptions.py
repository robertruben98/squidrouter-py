"""Exception hierarchy for the Squid Router client."""

from __future__ import annotations

from typing import Any, Optional


class SquidError(Exception):
    """Base class for all errors raised by :mod:`squidrouter`."""


class SquidAPIError(SquidError):
    """Raised when the Squid Router API returns an unsuccessful HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the API.
        message: A human-readable error message, extracted from the response
            body when possible.
        response_body: The decoded JSON body of the error response, or the raw
            text when the body is not valid JSON.
        request_id: The value of the ``x-request-id`` response header, useful
            when reporting issues to Squid support.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        response_body: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        self.request_id = request_id
        super().__init__(f"[{status_code}] {message}")


class StatusTimeoutError(SquidError):
    """Raised when :meth:`poll_status` does not reach a terminal state in time.

    Attributes:
        last_status: The most recent ``squidTransactionStatus`` value observed
            before the timeout, if any was retrieved.
    """

    def __init__(self, message: str, *, last_status: Optional[str] = None) -> None:
        self.last_status = last_status
        super().__init__(message)
