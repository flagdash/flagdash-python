"""Deployment-region detection.

Sending a ``region`` on every evaluation lets targeting rules and segments roll
a feature out region by region without the application threading it through
each call.
"""

from __future__ import annotations

import os

from flagdash.types import EvaluationContext

#: Checked in order. ``FLAGDASH_REGION`` wins so a deployment can override
#: whatever the platform reports.
REGION_ENV_VARS = (
    "FLAGDASH_REGION",
    "FLY_REGION",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "GOOGLE_CLOUD_REGION",
    "RAILWAY_REPLICA_REGION",
    "RENDER_REGION",
)


def detect_region() -> str | None:
    """Return a best-effort deployment region from the environment."""
    for var in REGION_ENV_VARS:
        value = os.environ.get(var)
        if value:
            return value
    return None


def resolve_region(region: str | None, auto_detect: bool) -> str | None:
    """Pick the region to send: explicit value, then detection, then none."""
    if region is not None:
        return region
    return detect_region() if auto_detect else None


def merge_region_params(
    region: str | None,
    context: EvaluationContext | None,
) -> dict[str, str] | None:
    """Build query params for an evaluation with ``region`` merged in.

    An explicit ``region`` in the caller's context always wins.
    """
    params = context.to_query_params() if context else {}

    if region and "region" not in params:
        params = {"region": region, **params}

    return params or None
