import asyncio
import os

from pydoll.browser import Chrome
from pydoll_turnstile import solve_turnstile

# Get a free key at https://peak.fo
os.environ.setdefault("PEAK_API_KEY", "pk_your_api_key")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to("https://protected.example/login")
        token = await solve_turnstile(tab)
        print("solved, token length:", len(token))


if __name__ == "__main__":
    asyncio.run(main())
