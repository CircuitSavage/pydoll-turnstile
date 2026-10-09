"""Solve Cloudflare Turnstile on a live pydoll tab via the Peak API.

pydoll drives Chrome over the DevTools Protocol with no webdriver, which is
why people reach for it against Cloudflare. When the browser still stalls on
the Turnstile widget, this reads the sitekey, gets a token from Peak, and
injects it so the form or navigation proceeds.

Everything is async to match pydoll. The Peak HTTP call runs in a worker
thread (``asyncio.to_thread``) so the event loop is never blocked. The
functions take any pydoll tab/page that exposes ``execute_script``.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from .peak import DEFAULT_API_URL, TASK_TURNSTILE, PeakClient, PeakError

_READ_SITEKEY_JS = r"""
var el = document.querySelector('[data-sitekey]');
if (el) { return el.getAttribute('data-sitekey'); }
var m = (document.documentElement.outerHTML || '').match(
    /(?:sitekey|render)\s*[:=]\s*["']((?:0x|1x)[^"']+)["']/i);
return m ? m[1] : null;
"""

# Injects a solved token: sets every cf-turnstile-response field, fires
# input/change so listeners react, and calls the widget's success callback.
# The token is embedded as a JSON literal in inject_token rather than passed
# as an argument, since pydoll's execute_script takes no extra args.
_INJECT_TOKEN_BODY = r"""
var fields = document.querySelectorAll(
    'input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"], ' +
    'input#cf-turnstile-response, [name="cf-turnstile-response"]');
if (!fields.length) {
    var holder = document.querySelector('.cf-turnstile') || document.body;
    var inp = document.createElement('input');
    inp.type = 'hidden';
    inp.name = 'cf-turnstile-response';
    holder.appendChild(inp);
    fields = [inp];
}
fields.forEach(function (f) {
    f.value = token;
    f.dispatchEvent(new Event('input', { bubbles: true }));
    f.dispatchEvent(new Event('change', { bubbles: true }));
});
var called = false;
document.querySelectorAll('[data-callback]').forEach(function (w) {
    var name = w.getAttribute('data-callback');
    if (name && typeof window[name] === 'function') {
        window[name](token);
        called = true;
    }
});
return called;
"""


def _value(result):
    """Normalize pydoll's execute_script return across versions.

    Some versions return the raw JS value; others return a CDP
    Runtime.evaluate result like ``{"result": {"value": ...}}``.
    """
    if isinstance(result, dict):
        inner = result.get("result", result)
        if isinstance(inner, dict) and "value" in inner:
            return inner["value"]
    return result


async def _run_js(tab, script: str):
    return _value(await tab.execute_script(script))


async def read_sitekey(tab) -> Optional[str]:
    """Return the Turnstile sitekey on the current page, or None."""
    sitekey = await _run_js(tab, _READ_SITEKEY_JS)
    if sitekey:
        return str(sitekey).strip()
    return None


async def inject_token(tab, token: str) -> None:
    """Inject a solved token into the page's Turnstile widget."""
    script = "var token = " + json.dumps(token) + ";\n" + _INJECT_TOKEN_BODY
    await _run_js(tab, script)


async def current_url(tab) -> Optional[str]:
    try:
        return await _run_js(tab, "return window.location.href")
    except Exception:
        return None


async def solve_turnstile(
    tab,
    api_key: Optional[str] = None,
    proxy: Optional[str] = None,
    sitekey: Optional[str] = None,
    url: Optional[str] = None,
    task_type: str = TASK_TURNSTILE,
    api_url: Optional[str] = None,
    timeout: float = 180.0,
) -> str:
    """Solve the Turnstile challenge on a pydoll ``tab``'s current page.

    Reads the sitekey from the DOM (unless ``sitekey`` is given), asks Peak
    for a token, injects it, and returns the token. ``api_key`` defaults to
    the ``PEAK_API_KEY`` environment variable; ``url`` defaults to the tab's
    current URL. Pass ``proxy`` to mint the token from the browser's egress
    IP; omit it and Peak solves without one.

    Raises :class:`~pydoll_turnstile.peak.PeakError` on failure.
    """
    api_key = api_key or os.environ.get("PEAK_API_KEY")

    if sitekey is None:
        sitekey = await read_sitekey(tab)
    if not sitekey:
        raise PeakError(
            "No Turnstile sitekey found on the page. Pass sitekey= "
            "explicitly if the widget renders in a frame or after load."
        )

    if url is None:
        url = await current_url(tab)

    client = PeakClient(
        api_key, api_url=api_url or DEFAULT_API_URL, proxy=proxy, timeout=timeout
    )
    token = await asyncio.to_thread(client.solve, sitekey, url, proxy, task_type)
    await inject_token(tab, token)
    return token
