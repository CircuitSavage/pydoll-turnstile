"""pydoll-turnstile: solve Cloudflare Turnstile on a pydoll tab via Peak.

Public API::

    from pydoll_turnstile import solve_turnstile
    token = await solve_turnstile(tab, api_key="pk_...")
"""

from __future__ import annotations

from .peak import (
    DEFAULT_API_URL,
    TASK_CLOUDFLARE_5S,
    TASK_TURNSTILE,
    PeakClient,
    PeakError,
    build_solve_payload,
)
from .solver import current_url, inject_token, read_sitekey, solve_turnstile

__version__ = "0.1.0"

__all__ = [
    "solve_turnstile",
    "read_sitekey",
    "inject_token",
    "current_url",
    "PeakClient",
    "PeakError",
    "build_solve_payload",
    "DEFAULT_API_URL",
    "TASK_TURNSTILE",
    "TASK_CLOUDFLARE_5S",
    "__version__",
]
