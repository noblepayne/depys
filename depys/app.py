import functools

import httpx

from . import a_sync, sync, utils


# Leaving these undecorated allows easy use as a pytest fixture.
def make_sync_session():
    with httpx.Client() as client:
        yield client


async def make_async_session():
    async with httpx.AsyncClient() as aclient:
        yield aclient


system = {
    # System Wide
    "syncsession": (utils.fastapi_dep(make_sync_session), []),
    "asyncsession": (utils.fastapi_dep(make_async_session), []),
    # Sync Route
    "sync_get_ip": (sync.get_ip.sync_route, ["syncsession"]),
    "sync_router": (sync.get_ip.router, ["sync_get_ip"]),
    # Async Route
    "async_get_ip": (a_sync.get_ip.async_route, ["asyncsession"]),
    "async_router": (a_sync.get_ip.router, ["async_get_ip"]),
    # App
    "app": (utils.make_app_dep(), ["sync_router", "async_router"]),
}

app_factory = functools.partial(utils.app_factory, system=system, app_key="app")
