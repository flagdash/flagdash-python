"""Async usage of the FlagDash Python SDK."""

import asyncio

from flagdash import EvaluationContext, FlagDashAsyncClient, FlagDashAsyncServerClient


async def client_example() -> None:
    """Async client-tier usage."""
    async with FlagDashAsyncClient(sdk_key="client_your_key_here") as client:
        # Evaluate flags concurrently
        dark_mode, checkout = await asyncio.gather(
            client.flag("dark-mode", default=False),
            client.flag("checkout-v2", default=False),
        )
        print(f"Dark mode: {dark_mode}, Checkout V2: {checkout}")

        # Get all AI configs
        configs = await client.list_ai_configs()
        for ac in configs:
            print(f"  {ac.file_name}: {ac.file_type}")


async def server_example() -> None:
    """Async server-tier usage with caching."""
    async with FlagDashAsyncServerClient(
        sdk_key="server_your_key_here",
        cache_ttl=30.0,
    ) as client:
        # Evaluate with context
        ctx = EvaluationContext(user_id="bob", attributes={"country": "DE"})
        value = await client.flag("eu-features", default=False, context=ctx)
        print(f"EU features for bob: {value}")

        # Get full flag details
        flag = await client.get_flag("eu-features")
        if flag:
            print(f"Flag details: {flag.name}, variations={len(flag.variations)}")


async def main() -> None:
    await client_example()
    await server_example()


if __name__ == "__main__":
    asyncio.run(main())
