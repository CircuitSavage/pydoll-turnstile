<a href="https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=pydoll-turnstile">
  <img src="https://raw.githubusercontent.com/CircuitSavage/pydoll-turnstile/main/assets/peak-banner.png" alt="Peak — solve Cloudflare Turnstile & the 5s challenge in ~1s" width="100%">
</a>

# pydoll-turnstile

**pydoll-turnstile** solves Cloudflare Turnstile on a [pydoll](https://github.com/autoscrape-labs/pydoll) tab by injecting a Peak-solved token, so a protected form or navigation proceeds.

## Why

pydoll drives Chrome straight over the DevTools Protocol with no webdriver, which is a big part of why people pick it against Cloudflare. It handles plenty on its own. But the Turnstile widget on a datacenter IP still stalls — the challenge renders, the token never arrives, and the page just sits there.

This reads the sitekey from the DOM, gets a token from Peak, and injects it as the `cf-turnstile-response` value plus the widget's success callback. When pydoll's own handling leaves you stuck on the widget, drop in a Peak API key and the solve goes through.

## Powered by Peak

This package uses [Peak](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=pydoll-turnstile) to solve Turnstile.
- Solve Cloudflare Turnstile & the 5s challenge in about a second
- $0.90 per 1,000 successful Turnstile solves, down to $0.35 at volume
- 1,000 free solves to start, no card.

→ [Get your free API key](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=pydoll-turnstile) · [Docs](https://peak.fo/docs/turnstile?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=pydoll-turnstile) · [Pricing](https://peak.fo/pricing?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=pydoll-turnstile)

## Install

```bash
pip install pydoll-turnstile pydoll-python
```

## Quickstart

```python
import asyncio
import os
from pydoll.browser import Chrome
from pydoll_turnstile import solve_turnstile

os.environ["PEAK_API_KEY"] = "pk_your_api_key"


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to("https://protected.example/login")

        # Reads the sitekey, solves via Peak, injects the token.
        await solve_turnstile(tab)

        # the form / navigation can now proceed


asyncio.run(main())
```

## How it works

1. **Read the sitekey.** An `execute_script` DOM scan finds the `data-sitekey` on the `.cf-turnstile` widget, or the sitekey set through a JS `render()` call.
2. **Solve via Peak.** `POST https://api.peak.fo/solve` with `task_type: "turnstiletask"`, the sitekey, and the tab's current URL. The call runs in a worker thread so the event loop stays free. Pass `proxy=` to mint the token from your browser's egress IP.
3. **Inject the token.** `execute_script` sets every `cf-turnstile-response` field, fires `input`/`change`, and calls the widget's `data-callback` so the form or navigation continues.

## API

```python
await solve_turnstile(
    tab,                  # a pydoll tab/page with execute_script
    api_key=None,         # defaults to env PEAK_API_KEY
    proxy=None,           # optional http://user:pass@ip:port, forwarded to Peak
    sitekey=None,         # override auto-detection (e.g. widget in a frame)
    url=None,             # defaults to the tab's current URL
    task_type="turnstiletask",
    timeout=180.0,
) -> str                  # the injected token
```

`read_sitekey(tab)`, `inject_token(tab, token)`, and `current_url(tab)` are exposed for finer control. Peak also supports `task_type="cloudflare5stask"` for the 5s interstitial.

The API key is read from `PEAK_API_KEY` by default; you can also pass it explicitly. Never hardcode a real key.

## Legitimate use

For automation, QA, and scraping public data you are allowed to access. Respect each target's Terms of Service and robots directives, and do not use this for credential-stuffing or other abuse.

## License

MIT — see [LICENSE](./LICENSE).
