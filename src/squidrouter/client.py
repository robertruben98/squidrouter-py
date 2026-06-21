"""Synchronous client for the Squid Router API."""

from __future__ import annotations

import time
from types import TracebackType
from typing import Any, Optional, Union

import httpx

from ._base import (
    DEFAULT_BASE_URL,
    DEFAULT_INTEGRATOR_HEADER,
    DEFAULT_TIMEOUT,
    TERMINAL_STATUSES,
    build_headers,
    raise_for_status,
)
from .exceptions import SquidAPIError, StatusTimeoutError
from .models import (
    ChainsResponse,
    RouteRequest,
    RouteResponse,
    StatusResponse,
    TokensResponse,
)


class SquidClient:
    """Synchronous client for the Squid Router v2 API.

    Squid is an Axelar-powered aggregator for cross-chain swaps and bridging.
    Every request requires an integrator ID, sent by default in the
    ``x-integrator-id`` header. Obtain a free integrator ID from the Squid
    integrator portal (https://docs.squidrouter.com).

    The client may be used as a context manager to ensure the underlying
    connection pool is closed::

        with SquidClient(integrator_id="my-id") as client:
            chains = client.get_chains()

    Args:
        integrator_id: The integrator ID issued by Squid. Required.
        base_url: Base URL of the Squid API. Defaults to the v2 endpoint at
            ``https://apiplus.squidrouter.com``.
        integrator_header: Header name carrying the integrator ID. Defaults to
            ``x-integrator-id``.
        timeout: Request timeout in seconds.
        client: An optional pre-configured :class:`httpx.Client` to use instead
            of creating one internally. When supplied, the caller owns its
            lifecycle and it will not be closed by this client.
    """

    def __init__(
        self,
        integrator_id: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        integrator_header: str = DEFAULT_INTEGRATOR_HEADER,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.integrator_id = integrator_id
        self.base_url = base_url.rstrip("/")
        self.integrator_header = integrator_header
        headers = build_headers(integrator_id, integrator_header)
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )
        if client is not None:
            self._client.headers.update(headers)

    def __enter__(self) -> SquidClient:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client if it is owned by this instance."""
        if self._owns_client:
            self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        response = self._client.request(method, path, params=params, json=json)
        raise_for_status(response)
        return response

    def get_chains(self) -> ChainsResponse:
        """Fetch the chains supported by Squid Router.

        Returns:
            A :class:`~squidrouter.models.ChainsResponse` listing supported
            chains.

        Raises:
            SquidAPIError: If the API returns an unsuccessful status.
        """
        response = self._request("GET", "/v2/chains")
        return ChainsResponse.model_validate(response.json())

    def get_tokens(self) -> TokensResponse:
        """Fetch the tokens supported by Squid Router.

        Returns:
            A :class:`~squidrouter.models.TokensResponse` listing supported
            tokens.

        Raises:
            SquidAPIError: If the API returns an unsuccessful status.
        """
        response = self._request("GET", "/v2/tokens")
        return TokensResponse.model_validate(response.json())

    def get_route(self, request: Union[RouteRequest, dict[str, Any]]) -> RouteResponse:
        """Request an optimal cross-chain route (quote) for a swap or bridge.

        Args:
            request: The route parameters, either a
                :class:`~squidrouter.models.RouteRequest` or a plain dict using
                the API's camelCase field names.

        Returns:
            A :class:`~squidrouter.models.RouteResponse`. Its ``request_id`` is
            populated from the ``x-request-id`` response header; together with
            ``route.quote_id`` it is required to track status.

        Raises:
            SquidAPIError: If the API returns an unsuccessful status.
        """
        payload = request.to_payload() if isinstance(request, RouteRequest) else request
        response = self._request("POST", "/v2/route", json=payload)
        result = RouteResponse.model_validate(response.json())
        result.request_id = response.headers.get("x-request-id")
        return result

    def get_status(
        self,
        *,
        transaction_id: str,
        request_id: Optional[str] = None,
        from_chain_id: Optional[Union[int, str]] = None,
        to_chain_id: Optional[Union[int, str]] = None,
        quote_id: Optional[str] = None,
    ) -> StatusResponse:
        """Fetch the status of a cross-chain transaction.

        Args:
            transaction_id: The source-chain transaction hash.
            request_id: The ``x-request-id`` value returned by
                :meth:`get_route`.
            from_chain_id: The source chain ID.
            to_chain_id: The destination chain ID.
            quote_id: The ``route.quote_id`` from the route response. Required
                for Squid Intents transactions (enabled by default); omitting it
                can cause the transaction to fail.

        Returns:
            A :class:`~squidrouter.models.StatusResponse`.

        Raises:
            SquidAPIError: If the API returns an unsuccessful status.
        """
        params: dict[str, Any] = {"transactionId": transaction_id}
        if request_id is not None:
            params["requestId"] = request_id
        if from_chain_id is not None:
            params["fromChainId"] = from_chain_id
        if to_chain_id is not None:
            params["toChainId"] = to_chain_id
        if quote_id is not None:
            params["quoteId"] = quote_id
        response = self._request("GET", "/v2/status", params=params)
        return StatusResponse.model_validate(response.json())

    def poll_status(
        self,
        *,
        transaction_id: str,
        request_id: Optional[str] = None,
        from_chain_id: Optional[Union[int, str]] = None,
        to_chain_id: Optional[Union[int, str]] = None,
        quote_id: Optional[str] = None,
        interval: float = 5.0,
        timeout: float = 600.0,
    ) -> StatusResponse:
        """Poll :meth:`get_status` until the transaction reaches a terminal state.

        Terminal states are ``success``, ``partial_success``, ``needs_gas`` and
        ``not_found``. A ``404`` (transaction not yet indexed) is treated as
        in-progress and retried.

        Args:
            transaction_id: The source-chain transaction hash.
            request_id: The ``x-request-id`` value returned by
                :meth:`get_route`.
            from_chain_id: The source chain ID.
            to_chain_id: The destination chain ID.
            quote_id: The ``route.quote_id`` from the route response.
            interval: Seconds to wait between polls.
            timeout: Maximum total seconds to poll before giving up.

        Returns:
            The terminal :class:`~squidrouter.models.StatusResponse`.

        Raises:
            StatusTimeoutError: If no terminal state is reached within
                ``timeout`` seconds.
            SquidAPIError: For non-404 API errors.
        """
        deadline = time.monotonic() + timeout
        last_status: Optional[str] = None
        while True:
            try:
                status = self.get_status(
                    transaction_id=transaction_id,
                    request_id=request_id,
                    from_chain_id=from_chain_id,
                    to_chain_id=to_chain_id,
                    quote_id=quote_id,
                )
            except SquidAPIError as exc:
                if exc.status_code != 404:
                    raise
                if time.monotonic() + interval >= deadline:
                    raise StatusTimeoutError(
                        f"Status did not reach a terminal state within {timeout}s",
                        last_status=last_status,
                    ) from exc
                time.sleep(interval)
                continue
            last_status = status.squid_transaction_status or last_status
            if status.squid_transaction_status in TERMINAL_STATUSES:
                return status
            if time.monotonic() + interval >= deadline:
                raise StatusTimeoutError(
                    f"Status did not reach a terminal state within {timeout}s",
                    last_status=last_status,
                )
            time.sleep(interval)
