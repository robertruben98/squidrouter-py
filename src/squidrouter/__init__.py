"""squidrouter-py: a typed Python client for the Squid Router API.

Squid Router is an Axelar-powered aggregator for cross-chain swaps and bridging.
This package provides synchronous (:class:`SquidClient`) and asynchronous
(:class:`AsyncSquidClient`) clients built on ``httpx`` and ``pydantic``.

Every request requires an integrator ID (free from the Squid integrator portal),
sent by default in the ``x-integrator-id`` header.
"""

from .async_client import AsyncSquidClient
from .client import SquidClient
from .exceptions import SquidAPIError, SquidError, StatusTimeoutError
from .models import (
    Chain,
    ChainsResponse,
    Estimate,
    Route,
    RouteRequest,
    RouteResponse,
    StatusResponse,
    Token,
    TokensResponse,
    TransactionRequest,
)

__version__ = "0.1.0"

__all__ = [
    "AsyncSquidClient",
    "Chain",
    "ChainsResponse",
    "Estimate",
    "Route",
    "RouteRequest",
    "RouteResponse",
    "SquidAPIError",
    "SquidClient",
    "SquidError",
    "StatusResponse",
    "StatusTimeoutError",
    "Token",
    "TokensResponse",
    "TransactionRequest",
    "__version__",
]
