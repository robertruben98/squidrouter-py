"""Live integration test against the real Squid Router API.

Skipped by default. To run it, export a real integrator ID:

    SQUID_INTEGRATOR_ID=your-id pytest tests/test_live_integration.py

A free integrator ID is available from the Squid integrator portal
(https://docs.squidrouter.com). These tests make real network calls.
"""

import os

import pytest

from squidrouter import RouteRequest, SquidClient

INTEGRATOR_ID = os.environ.get("SQUID_INTEGRATOR_ID")

pytestmark = pytest.mark.skipif(
    not INTEGRATOR_ID,
    reason="SQUID_INTEGRATOR_ID not set; skipping live integration tests",
)


def test_live_get_chains():
    with SquidClient(integrator_id=INTEGRATOR_ID) as client:
        chains = client.get_chains()
    assert len(chains.chains) > 0
    assert chains.chains[0].chain_id is not None


def test_live_get_route():
    with SquidClient(integrator_id=INTEGRATOR_ID) as client:
        route = client.get_route(
            RouteRequest(
                from_chain="56",
                from_token="0x55d398326f99059fF775485246999027B3197955",
                from_amount="1000000000000000",
                to_chain="42161",
                to_token="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                from_address="0x0000000000000000000000000000000000000000",
                to_address="0x0000000000000000000000000000000000000000",
                slippage=1.0,
            )
        )
    assert route.route is not None
    assert route.request_id is not None
