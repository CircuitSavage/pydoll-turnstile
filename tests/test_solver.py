"""Unit tests that stub out the browser and the network.

Run with: pytest -q
"""

import asyncio
import re

import pytest

from pydoll_turnstile import PeakError, solve_turnstile
from pydoll_turnstile import peak, solver


def _extract_token(script):
    m = re.search(r'var token = "(.*?)";', script)
    return m.group(1) if m else None


class FakeTab:
    """Just enough of a pydoll tab for the solver."""

    def __init__(self, sitekey=None, url="https://protected.example/login"):
        self._sitekey = sitekey
        self._url = url
        self.injected = None

    async def execute_script(self, script):
        if "cf-turnstile-response" in script and "forEach" in script:
            self.injected = _extract_token(script)
            return True
        if "window.location.href" in script:
            return self._url
        return self._sitekey


def run(coro):
    return asyncio.run(coro)


def test_solves_and_injects(monkeypatch):
    class FakeClient:
        def __init__(self, api_key, api_url=None, proxy=None, timeout=180.0):
            pass

        def solve(self, sitekey, url, proxy=None, task_type="turnstiletask"):
            assert sitekey == "0x4AAAAAAABkMYinukE8nzKd"
            return "SOLVED-TOKEN"

    monkeypatch.setattr(solver, "PeakClient", FakeClient)

    tab = FakeTab(sitekey="0x4AAAAAAABkMYinukE8nzKd")
    token = run(solve_turnstile(tab, api_key="pk_test"))
    assert token == "SOLVED-TOKEN"
    assert tab.injected == "SOLVED-TOKEN"


def test_raises_when_no_sitekey():
    tab = FakeTab(sitekey=None)
    with pytest.raises(PeakError):
        run(solve_turnstile(tab, api_key="pk_test"))


def test_read_sitekey_returns_none_when_absent():
    tab = FakeTab(sitekey=None)
    assert run(solver.read_sitekey(tab)) is None


def test_build_solve_payload_shape():
    body = peak.build_solve_payload(
        "0xSITEKEY", "https://x.example/", "http://u:p@h:1"
    )
    assert body == {
        "task_type": "turnstiletask",
        "url": "https://x.example/",
        "sitekey": "0xSITEKEY",
        "proxy": "http://u:p@h:1",
    }


def test_build_solve_payload_omits_proxy_when_absent():
    body = peak.build_solve_payload("0xSITEKEY", "https://x.example/")
    assert "proxy" not in body


def test_client_requires_api_key():
    with pytest.raises(PeakError):
        peak.PeakClient(api_key="")
