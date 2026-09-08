"""Basic usage of the FlagDash Python SDK (client tier)."""

from flagdash import EvaluationContext, FlagDashClient


def main() -> None:
    # Initialize client with your client API key
    with FlagDashClient(
        sdk_key="client_your_key_here",
    ) as client:
        # Evaluate a boolean flag
        dark_mode = client.flag("dark-mode", default=False)
        print(f"Dark mode: {dark_mode}")

        # Evaluate with user context for targeting
        ctx = EvaluationContext(
            user_id="alice@example.com",
            attributes={"country": "US", "plan": "pro"},
        )
        checkout_v2 = client.flag("checkout-v2", default=False, context=ctx)
        print(f"Checkout V2 for alice: {checkout_v2}")

        # Get all flags at once
        all_flags = client.all_flags()
        print(f"All flags: {all_flags}")

        # Get a remote config
        api_url = client.config("api-url", default="https://api.default.com")
        print(f"API URL: {api_url}")

        # List all configs
        configs = client.all_configs()
        for c in configs:
            print(f"Config {c.key}: {c.value}")

        # Get AI configs
        agent = client.ai_config("agent.md")
        if agent:
            print(f"Agent: {agent.content[:100]}...")

        ai_configs = client.list_ai_configs()
        for ac in ai_configs:
            print(f"AI Config: {ac.file_name} ({ac.file_type})")


if __name__ == "__main__":
    main()
