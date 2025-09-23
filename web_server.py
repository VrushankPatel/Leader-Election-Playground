import asyncio
from aiohttp import web
import os

async def main():
    app = web.Application()
    app.router.add_static('/', os.path.join(os.path.dirname(__file__), 'client'))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print("Web UI served on http://localhost:8080")
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())