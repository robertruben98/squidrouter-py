# squidrouter-py

[![CI](https://github.com/robertruben98/squidrouter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/robertruben98/squidrouter-py/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/squidrouter-py.svg)](https://pypi.org/project/squidrouter-py/)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://robertruben98.github.io/squidrouter-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/squidrouter-py.svg)](https://pypi.org/project/squidrouter-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/robertruben98/squidrouter-py/blob/main/LICENSE)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A typed, batteries-included Python client for the [Squid Router](https://squidrouter.com)
v2 API — the [Axelar](https://www.axelar.network/)-powered aggregator for
cross-chain swaps and bridging. Sync **and** async, built on
[`httpx`](https://www.python-httpx.org/) and [`pydantic`](https://docs.pydantic.dev/) v2.

## Requirements

- Python **3.9+**
- An **integrator ID** — every Squid API request requires one. It is sent in
  the `x-integrator-id` header. Get a free integrator ID from the
  [Squid integrator portal](https://docs.squidrouter.com) (apply via the link in
  the docs and check your email). The client will not work without it.

## Installation

```bash
pip install squidrouter-py
```

The package installs as `squidrouter-py`; you import it as `squidrouter`.

## Quickstart

```python
from squidrouter import SquidClient, RouteRequest

with SquidClient(integrator_id="YOUR_INTEGRATOR_ID") as client:
    # List supported chains and tokens
    chains = client.get_chains()
    tokens = client.get_tokens()

    # Request a cross-chain route: USDT on BNB Chain -> USDC on Arbitrum
    route = client.get_route(
        RouteRequest(
            from_chain="56",
            from_token="0x55d398326f99059fF775485246999027B3197955",
            from_amount="1000000000000000",
            to_chain="42161",
            to_token="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            from_address="0xYourAddress",
            to_address="0xYourAddress",
            slippage=1.0,
        )
    )

    estimate = route.route.estimate
    print("You will receive ~", estimate.to_amount)

    # The signable transaction is in route.route.transaction_request.
    # Save these two values to track the transaction later:
    request_id = route.request_id          # from the x-request-id response header
    quote_id = route.route.quote_id        # required for Squid Intents status tracking
```

### Tracking transaction status

After you broadcast the route's transaction on-chain, poll for its
cross-chain status. Squid Intents is enabled by default, so you **must** pass the
`quote_id`:

```python
status = client.poll_status(
    transaction_id="0xYourSourceTxHash",
    request_id=request_id,
    from_chain_id="56",
    to_chain_id="42161",
    quote_id=quote_id,
)
print(status.squid_transaction_status)  # e.g. "success"
```

`poll_status` blocks until a terminal state (`success`, `partial_success`,
`needs_gas`, `not_found`) or raises `StatusTimeoutError`. For a single check use
`client.get_status(...)`.

### Async

```python
import asyncio
from squidrouter import AsyncSquidClient

async def main():
    async with AsyncSquidClient(integrator_id="YOUR_INTEGRATOR_ID") as client:
        chains = await client.get_chains()
        print(len(chains.chains), "chains supported")

asyncio.run(main())
```

## Configuration

`SquidClient` / `AsyncSquidClient` accept:

| Argument            | Default                              | Description                                        |
| ------------------- | ------------------------------------ | -------------------------------------------------- |
| `integrator_id`     | — (**required**)                     | Your Squid integrator ID.                          |
| `base_url`          | `https://apiplus.squidrouter.com`    | API base URL.                                      |
| `integrator_header` | `x-integrator-id`                    | Header name carrying the integrator ID.            |
| `timeout`           | `30.0`                               | Request timeout in seconds.                        |
| `client`            | `None`                               | A pre-configured `httpx.Client` / `AsyncClient`.   |

## Error handling

```python
from squidrouter import SquidClient, SquidAPIError

with SquidClient(integrator_id="YOUR_INTEGRATOR_ID") as client:
    try:
        client.get_chains()
    except SquidAPIError as exc:
        print(exc.status_code, exc.message, exc.request_id)
```

- `SquidError` — base class for everything raised by this library.
- `SquidAPIError` — non-2xx API response; carries `status_code`, `message`,
  `response_body`, `request_id`.
- `StatusTimeoutError` — `poll_status` did not reach a terminal state in time;
  carries `last_status`.

## License

[MIT](LICENSE)

This is an unofficial, community-maintained client and is not affiliated with
Squid or Axelar. See the official [Squid documentation](https://docs.squidrouter.com)
for the authoritative API reference.
