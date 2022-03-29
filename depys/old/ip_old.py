import contextlib
import functools

import fastapi


def _route(path, **kwargs):
    args = {"path": path, **kwargs}

    def _capture_fn(fn):
        args["endpoint"] = fn
        return args

    return _capture_fn


class RouterMeta(type):
    def __getattribute__(self, name):
        methods = [name.upper()]
        return functools.partial(_route, methods=methods)


class Router(metaclass=RouterMeta):
    """Just a helper."""


@contextlib.contextmanager
def sync_route(syncsession):
    @Router.get("/sync")
    def _sync_route(syncsession=fastapi.Depends(lambda: syncsession)):
        return syncsession.get("https://icanhazip.com").text.strip()

    print("defned the route")
    yield _sync_route


@contextlib.contextmanager
def router(**routes):
    router = fastapi.APIRouter()
    print("made the router")
    for route in routes.values():
        router.add_api_route(**route)
        print("added a route!")
    print("added ALL routes")
    yield router
    print("closing router")


@contextlib.contextmanager
def async_route(asyncsession):
    @Router.get("/async")
    async def _async_route(asyncsession=fastapi.Depends(lambda: asyncsession)):
        return (await asyncsession.get("https://icanhazip.com")).text.strip()

    yield _async_route
