"""Tests for SquidClient construction and request configuration."""

import httpx
import pytest
import respx

from squidrouter import SquidClient

BASE = "https://apiplus.squidrouter.com"


def test_integrator_id_is_required():
    with pytest.raises(TypeError):
        SquidClient()  # type: ignore[call-arg]


@respx.mock
def test_sends_integrator_id_header():
    route = respx.get(f"{BASE}/v2/chains").mock(
        return_value=httpx.Response(200, json={"chains": []})
    )
    with SquidClient(integrator_id="test-id") as client:
        client.get_chains()

    assert route.called
    assert route.calls.last.request.headers["x-integrator-id"] == "test-id"


@respx.mock
def test_custom_header_name_and_base_url():
    base = "https://custom.example.com"
    route = respx.get(f"{base}/v2/chains").mock(
        return_value=httpx.Response(200, json={"chains": []})
    )
    with SquidClient(
        integrator_id="abc",
        base_url=base,
        integrator_header="x-my-key",
    ) as client:
        client.get_chains()

    assert route.calls.last.request.headers["x-my-key"] == "abc"
