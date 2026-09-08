"""Server-tier usage of the FlagDash Python SDK with caching."""

from flagdash import EvaluationContext, FlagDashServerClient


def main() -> None:
    # Initialize server client — includes TTL caching
    with FlagDashServerClient(
        sdk_key="server_your_key_here",
        cache_ttl=60.0,  # Cache for 60 seconds
    ) as client:
        # Evaluate a flag (cached after first call)
        is_enabled = client.flag("checkout-v2", default=False)
        print(f"Checkout V2: {is_enabled}")

        # Evaluate with context (bypasses cache)
        ctx = EvaluationContext(user_id="alice", attributes={"plan": "pro"})
        personalized = client.flag("premium-features", default=False, context=ctx)
        print(f"Premium features for alice: {personalized}")

        # Get full flag details
        flag = client.get_flag("checkout-v2")
        if flag:
            print(f"Flag: {flag.name}, enabled={flag.enabled}, rollout={flag.rollout_percentage}%")
            for v in flag.variations:
                print(f"  Variation: {v.key} (weight={v.weight})")

        # List all flags with metadata
        flags = client.list_flags()
        for f in flags:
            print(f"  {f.key}: enabled={f.enabled}, type={f.flag_type}")

        # Get server-tier config (with metadata)
        config = client.get_config("api-url")
        if config:
            print(f"Config: {config.name} = {config.value}")

        # Get AI config with metadata
        agent = client.ai_config("agent.md")
        if agent:
            print(f"AI Config: {agent.file_name}, active={agent.is_active}")

        # Clear cache to force fresh data
        client.clear_cache()


if __name__ == "__main__":
    main()
