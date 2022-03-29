import contextlib
import functools

import anyio
import fastapi
import httpx
import uvicorn.workers

from . import acompynent


class UvicornFactoryWorker(uvicorn.workers.UvicornWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.factory = True


@contextlib.contextmanager
def make_sync_session():
    print("starting client")
    with httpx.Client() as client:
        yield client
    print("closing client")


@contextlib.asynccontextmanager
async def make_async_session():
    print("starting aclient")
    async with httpx.AsyncClient() as aclient:
        yield aclient
    print("closing aclient")


@contextlib.contextmanager
def make_app(**ctx):
    print("starting app")
    app = fastapi.FastAPI()

    def get_in_ctx(key):
        assert key in ctx

        def _get_in_ctx():
            return ctx[key]

        return fastapi.Depends(_get_in_ctx)

    @app.get("/")
    def get_ep(client=get_in_ctx("syncsession")):
        print(client)
        return client.get("https://icanhazip.com").text.strip()

    @app.get("/a")
    async def get_ep(client=get_in_ctx("asyncsession")):
        print(client)
        return (await client.get("https://icanhazip.com")).text.strip()

    yield app
    print("closing app")


base_system = {
    "syncsession": (make_sync_session, []),
    "asyncsession": (make_async_session, []),
}
system = {
    **base_system,
    "app": (make_app, base_system.keys()),
}


def _app(system):
    with contextlib.ExitStack() as stack:
        _system = acompynent.System(system)
        # Async magic.
        portal = stack.enter_context(anyio.start_blocking_portal())
        ctx = stack.enter_context(portal.wrap_async_context_manager(_system.start()))
        # ExitStack magic.
        _stack = stack.pop_all()
        # Embed shutdown into app.
        ctx["app"].router.on_shutdown = [_stack.close]
        return ctx["app"]


app = functools.partial(_app, system)
