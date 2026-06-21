"""Tests for poll_status on both sync and async clients."""

import httpx
import pytest
import respx

from squidrouter import AsyncSquidClient, SquidClient, StatusTimeoutError

BASE = "https://apiplus.squidrouter.com"


@respx.mock
def test_poll_status_returns_on_terminal_state(monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    respx.get(f"{BASE}/v2/status").mock(
        side_effect=[
            httpx.Response(200, json={"squidTransactionStatus": "ongoing"}),
            httpx.Response(200, json={"squidTransactionStatus": "success"}),
        ]
    )
    with SquidClient(integrator_id="id") as client:
        status = client.poll_status(transaction_id="0xhash", interval=1, timeout=100)

    assert status.squid_transaction_status == "success"
    assert sleeps == [1]  # slept once between the two polls


@respx.mock
def test_poll_status_retries_on_404(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    respx.get(f"{BASE}/v2/status").mock(
        side_effect=[
            httpx.Response(404, json={"message": "not indexed yet"}),
            httpx.Response(200, json={"squidTransactionStatus": "success"}),
        ]
    )
    with SquidClient(integrator_id="id") as client:
        status = client.poll_status(transaction_id="0xhash", interval=1, timeout=100)

    assert status.squid_transaction_status == "success"


@respx.mock
def test_poll_status_times_out(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    respx.get(f"{BASE}/v2/status").mock(
        return_value=httpx.Response(200, json={"squidTransactionStatus": "ongoing"})
    )
    with SquidClient(integrator_id="id") as client, pytest.raises(StatusTimeoutError) as exc_info:
        client.poll_status(transaction_id="0xhash", interval=10, timeout=5)

    assert exc_info.value.last_status == "ongoing"


@respx.mock
async def test_async_poll_status_returns_on_terminal_state(monkeypatch):
    async def _no_sleep(_s):
        return None

    monkeypatch.setattr("asyncio.sleep", _no_sleep)
    respx.get(f"{BASE}/v2/status").mock(
        side_effect=[
            httpx.Response(200, json={"squidTransactionStatus": "ongoing"}),
            httpx.Response(200, json={"squidTransactionStatus": "partial_success"}),
        ]
    )
    async with AsyncSquidClient(integrator_id="id") as client:
        status = await client.poll_status(transaction_id="0xhash", interval=1, timeout=100)

    assert status.squid_transaction_status == "partial_success"


@respx.mock
async def test_async_get_route_captures_request_id():
    respx.post(f"{BASE}/v2/route").mock(
        return_value=httpx.Response(
            200,
            headers={"x-request-id": "areq-1"},
            json={"route": {"quoteId": "q"}},
        )
    )
    async with AsyncSquidClient(integrator_id="id") as client:
        resp = await client.get_route({"fromChain": "1"})

    assert resp.request_id == "areq-1"
    assert resp.route.quote_id == "q"
