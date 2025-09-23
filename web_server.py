import asyncio
import os

from aiohttp import web


async def index_handler(request):
    return web.FileResponse(
        os.path.join(os.path.dirname(__file__), "client", "index.html")
    )


async def main():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_static("/", os.path.join(os.path.dirname(__file__), "client"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()
    print("Web UI served on http://localhost:8080")
    # Keep running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
