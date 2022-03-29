import contextlib
import functools

import anyio
import fastapi.dependencies.utils
import fastapi.params
import uvicorn.workers

from . import acompynent


class Depends(fastapi.params.Depends):
    """Just here to be bit different."""


def _route_decorator(path, **kwargs):
    args = {"path": path, **kwargs}

    def _capture_fn(fn):
        context_deps = []

        endpoint_signature = fastapi.dependencies.utils.get_typed_signature(fn)
        signature_params = endpoint_signature.parameters

        # Grab any parameters that have a default value of Depends.
        for param_name, param in signature_params.items():
            if isinstance(param.default, Depends):
                context_deps.append(param_name)

        @contextlib.contextmanager
        def _dep(**deps):
            args["endpoint"] = functools.partial(
                fn,
                # Replace our depends with the fastapi version and the actual dep.
                **{dep: fastapi.Depends(deps[dep]) for dep in context_deps},
            )
            yield args

        return _dep

    return _capture_fn


HTTP_METHODS = {"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "TRACE", "HEAD"}


class RouterMeta(type):
    def __getattribute__(self, name):
        # Implement @generic_router.method(...) ala fastapi.
        if method_name := getattr(name, "upper", lambda *args, **kwargs: False)():
            if method_name in HTTP_METHODS:
                methods = [name.upper()]
                return functools.partial(_route_decorator, methods=methods)

        return object.__getattribute__(self, name)


class generic_router(metaclass=RouterMeta):
    """Just here to implement RouterMeta."""


class make_router_dep:
    """Hybrid contextmanager and route deorator."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, **routes):
        self.routes = routes
        return self

    def __enter__(self):
        """Make a new router and consume/add routes as deps."""
        _router = fastapi.APIRouter(*self.args, **self.kwargs)
        for route in self.routes.values():
            _router.add_api_route(**route)
        return _router

    def __exit__(self, *exc):
        # TODO: how would we like to handle errors?
        return False

    def __getattribute__(self, name):
        # Implement route decorator functionality.
        if method_name := getattr(name, "upper", lambda *args, **kwargs: False)():
            if method_name in HTTP_METHODS:
                methods = [name.upper()]
                return functools.partial(_route_decorator, methods=methods)

        return object.__getattribute__(self, name)


def make_app_dep(*args, **kwargs):
    """Makes a new FastAPI app and consumes routers as deps."""

    @contextlib.contextmanager
    def _make_app(**routers):
        app = fastapi.FastAPI(*args, **kwargs)
        for router in routers.values():
            app.include_router(router)
        yield app

    return _make_app


def start_system(system):
    """Start a system and return the started context and stack."""
    with contextlib.ExitStack() as stack:
        _system = acompynent.System(system)
        # Async magic.
        portal = stack.enter_context(anyio.start_blocking_portal())
        ctx = stack.enter_context(portal.wrap_async_context_manager(_system.start()))
        # ExitStack magic to capture stack outside of this with.
        _stack = stack.pop_all()
        return (ctx, _stack)


def make_app(ctx, stack, app_key):
    """Extract and configure app from system context."""
    # Configure FastAPI shutdown.
    app = ctx[app_key]
    app.router.on_shutdown = [stack.close]
    return app


def app_factory(system, app_key):
    """Helper to start system and return an app"""
    ctx, stack = start_system(system)
    return make_app(ctx, stack, app_key)


def fastapi_dep(fn):
    """Decorator to help create deps for use with fastapi's Depends.

    FastAPI expects to have a callable inside Depends. Here we wrap the
    dep in a lambda to play ball.

    This also ensures fastapi dep overrides can still work.
    """
    if fastapi.dependencies.utils.is_async_gen_callable(fn):

        @contextlib.asynccontextmanager
        async def _make_dep(*args, **kwargs):
            async for item in fn(*args, **kwargs):
                yield lambda: item

    else:

        @contextlib.contextmanager
        def _make_dep(*args, **kwargs):
            for item in fn(*args, **kwargs):
                yield lambda: item

    return _make_dep


# ==================================================================


class UvicornFactoryWorker(uvicorn.workers.UvicornWorker):
    """I'm _always_ a factory. (Gunicorn helper)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.factory = True


# def __route_decorator__legacy(path, **kwargs):
#     args = {"path": path, **kwargs}
#
#     def _capture_fn(fn):
#         args["endpoint"] = fn
#         return args
#
#     return _capture_fn


# def make_router__legacy(*args, **kwargs):
#     @contextlib.contextmanager
#     def _make_router(**routes):
#         router = fastapi.APIRouter(*args, **kwargs)
#         for route in routes.values():
#             router.add_api_route(**route)
#         yield router
#
#     return _make_router
