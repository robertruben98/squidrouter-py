"""Tests for the Squid Router endpoint methods (chains, tokens, route, status)."""

import json

import httpx
import pytest
import respx

from squidrouter import RouteRequest, SquidAPIError, SquidClient

BASE = "https://apiplus.squidrouter.com"


@respx.mock
def test_get_chains_parses_chains():
    respx.get(f"{BASE}/v2/chains").mock(
        return_value=httpx.Response(
            200,
            json={"chains": [{"chainId": "56", "chainName": "BNB Chain", "chainType": "evm"}]},
        )
    )
    with SquidClient(integrator_id="id") as client:
        chains = client.get_chains()

    assert len(chains.chains) == 1
    assert chains.chains[0].chain_id == "56"
    assert chains.chains[0].chain_name == "BNB Chain"


@respx.mock
def test_get_tokens_parses_tokens():
    respx.get(f"{BASE}/v2/tokens").mock(
        return_value=httpx.Response(
            200,
            json={"tokens": [{"symbol": "USDC", "decimals": 6, "chainId": "42161"}]},
        )
    )
    with SquidClient(integrator_id="id") as client:
        tokens = client.get_tokens()

    assert tokens.tokens[0].symbol == "USDC"
    assert tokens.tokens[0].decimals == 6


@respx.mock
def test_get_route_serializes_camelcase_body_and_captures_request_id():
    route = respx.post(f"{BASE}/v2/route").mock(
        return_value=httpx.Response(
            200,
            headers={"x-request-id": "req-123"},
            json={
                "route": {
                    "estimate": {"toAmount": "999", "toAmountMin": "990"},
                    "transactionRequest": {"target": "0xabc", "data": "0x", "value": "0"},
                    "quoteId": "quote-xyz",
                }
            },
        )
    )
    req = RouteRequest(
        from_chain="56",
        from_token="0x55d398326f99059fF775485246999027B3197955",
        from_amount="1000000000000000",
        to_chain="42161",
        to_token="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        from_address="0xfrom",
        to_address="0xto",
        slippage=1.0,
    )
    with SquidClient(integrator_id="id") as client:
        resp = client.get_route(req)

    sent = json.loads(route.calls.last.request.content)
    assert sent["fromChain"] == "56"
    assert sent["fromAmount"] == "1000000000000000"
    assert sent["toAddress"] == "0xto"
    assert sent["slippage"] == 1.0
    assert "enableBoost" not in sent  # exclude_none

    assert resp.request_id == "req-123"
    assert resp.route is not None
    assert resp.route.quote_id == "quote-xyz"
    assert resp.route.estimate.to_amount == "999"
    assert resp.route.transaction_request.target == "0xabc"


@respx.mock
def test_get_route_accepts_raw_dict():
    route = respx.post(f"{BASE}/v2/route").mock(return_value=httpx.Response(200, json={}))
    with SquidClient(integrator_id="id") as client:
        client.get_route({"fromChain": "1", "toChain": "10"})

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"fromChain": "1", "toChain": "10"}


@respx.mock
def test_get_status_sends_query_params():
    route = respx.get(f"{BASE}/v2/status").mock(
        return_value=httpx.Response(200, json={"squidTransactionStatus": "success"})
    )
    with SquidClient(integrator_id="id") as client:
        status = client.get_status(
            transaction_id="0xhash",
            request_id="req-1",
            from_chain_id="56",
            to_chain_id="42161",
            quote_id="q-1",
        )

    params = dict(route.calls.last.request.url.params)
    assert params["transactionId"] == "0xhash"
    assert params["requestId"] == "req-1"
    assert params["quoteId"] == "q-1"
    assert status.squid_transaction_status == "success"


@respx.mock
def test_api_error_raised_with_details():
    respx.get(f"{BASE}/v2/chains").mock(
        return_value=httpx.Response(
            400,
            headers={"x-request-id": "req-err"},
            json={"message": "integrator id missing"},
        )
    )
    with SquidClient(integrator_id="id") as client, pytest.raises(SquidAPIError) as exc_info:
        client.get_chains()

    err = exc_info.value
    assert err.status_code == 400
    assert "integrator id missing" in err.message
    assert err.request_id == "req-err"
    assert err.response_body == {"message": "integrator id missing"}
