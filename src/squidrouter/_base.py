"""Shared configuration and response handling for the Squid clients."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from .exceptions import SquidAPIError

DEFAULT_BASE_URL = "https://apiplus.squidrouter.com"
DEFAULT_INTEGRATOR_HEADER = "x-integrator-id"
DEFAULT_TIMEOUT = 30.0

# Terminal squidTransactionStatus values, per the Squid status documentation.
TERMINAL_STATUSES = frozenset({"success", "partial_success", "needs_gas", "not_found"})


def build_headers(integrator_id: str, integrator_header: str) -> dict[str, str]:
    """Build the default request headers for a Squid client.

    Args:
        integrator_id: The integrator ID issued by the Squid integrator portal.
        integrator_header: The header name to carry the integrator ID.

    Returns:
        A dict of default headers, including the integrator ID and a JSON
        ``Content-Type``.
    """
    return {
        integrator_header: integrator_id,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _extract_message(body: Any, fallback: str) -> str:
    """Pull a human-readable error message out of a decoded error body."""
    if isinstance(body, dict):
        for key in ("message", "error", "errors"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, dict):
                    nested = first.get("message")
                    if isinstance(nested, str):
                        return nested
                if isinstance(first, str):
                    return first
    return fallback


def raise_for_status(response: httpx.Response) -> None:
    """Raise :class:`SquidAPIError` for a non-2xx Squid API response.

    Args:
        response: The HTTP response to inspect.

    Raises:
        SquidAPIError: If the response status code is 400 or greater.
    """
    if response.status_code < 400:
        return

    body: Optional[Any]
    try:
        body = response.json()
    except ValueError:
        body = response.text or None

    message = _extract_message(body, response.reason_phrase or "Squid API error")
    raise SquidAPIError(
        response.status_code,
        message,
        response_body=body,
        request_id=response.headers.get("x-request-id"),
    )
