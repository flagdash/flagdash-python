"""Management-tier usage of the FlagDash Python SDK."""

from flagdash import FlagDashManagementClient


def main() -> None:
    with FlagDashManagementClient(
        sdk_key="management_your_key_here",
    ) as mgmt:
        project_id = "prj_your_project_id"
        environment_id = "env_your_environment_id"

        # ── Flags ──────────────────────────────────────────────
        # Create a flag
        flag = mgmt.create_flag(
            project_id=project_id,
            key="new-checkout",
            name="New Checkout",
            description="Enable the new checkout flow",
            flag_type="boolean",
            tags=["checkout", "payment"],
        )
        print(f"Created flag: {flag.id}")

        # Toggle it on
        result = mgmt.toggle_flag("new-checkout", project_id, environment_id)
        print(f"Toggled: enabled={result['enabled']}")

        # Set rollout to 50%
        mgmt.set_rollout("new-checkout", project_id, environment_id, 50)

        # Set A/B test variations
        variations = mgmt.set_variations(
            "new-checkout",
            project_id,
            environment_id,
            variations=[
                {"key": "control", "name": "Control", "value": {"value": False}, "weight": 50},
                {"key": "variant_a", "name": "Variant A", "value": {"value": True}, "weight": 50},
            ],
        )
        print(f"Set {len(variations)} variations")

        # List all flags
        flags = mgmt.list_flags(project_id)
        print(f"Total flags: {len(flags)}")

        # ── Configs ────────────────────────────────────────────
        # Create a config
        config = mgmt.create_config(
            project_id=project_id,
            key="max-upload-size",
            name="Max Upload Size",
            config_type="number",
            default_value={"value": 10485760},
        )
        print(f"Created config: {config.id}")

        # Update value for an environment
        mgmt.update_config_value(
            "max-upload-size",
            project_id,
            environment_id,
            value={"value": 52428800},
        )

        # ── AI Configs ─────────────────────────────────────────
        # Initialize defaults
        ai_configs = mgmt.initialize_ai_configs(project_id, environment_id)
        print(f"Initialized {len(ai_configs)} AI configs")

        # Create a custom AI config
        ac = mgmt.create_ai_config(
            project_id=project_id,
            environment_id=environment_id,
            file_name="debug-skill.md",
            file_type="skill",
            content="# Debug Skill\n\nHelps with debugging issues.",
            folder="skills",
        )
        print(f"Created AI config: {ac.file_name}")

        # ── Webhooks ───────────────────────────────────────────
        # Create a webhook
        webhook = mgmt.create_webhook(
            project_id=project_id,
            environment_id=environment_id,
            url="https://your-app.com/webhooks/flagdash",
            event_types=["flag.updated", "config.updated"],
            description="Production webhook",
        )
        print(f"Created webhook: {webhook.id}")
        print(f"Signing secret: {webhook.signing_secret}")

        # List deliveries
        deliveries = mgmt.list_webhook_deliveries(webhook.id)
        print(f"Deliveries: {len(deliveries)}")


if __name__ == "__main__":
    main()
