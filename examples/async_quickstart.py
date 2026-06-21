"""Asynchronous quickstart for squidrouter-py.

Run with your integrator ID in the environment:

    SQUID_INTEGRATOR_ID=your-id python examples/async_quickstart.py

Get a free integrator ID from the Squid integrator portal:
https://docs.squidrouter.com
"""

import asyncio
import os

from squidrouter import AsyncSquidClient, RouteRequest


async def main() -> None:
    integrator_id = os.environ["SQUID_INTEGRATOR_ID"]

    async with AsyncSquidClient(integrator_id=integrator_id) as client:
        chains = await client.get_chains()
        print(f"Squid supports {len(chains.chains)} chains")

        route = await client.get_route(
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

        if route.route and route.route.estimate:
            print("Estimated amount out:", route.route.estimate.to_amount)
        print("request_id:", route.request_id)


if __name__ == "__main__":
    asyncio.run(main())
