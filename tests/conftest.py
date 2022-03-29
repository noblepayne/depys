import fastapi.testclient
import pytest

import depys.app
import depys.utils


# Fixtures from deps.
sync_session = pytest.fixture(depys.app.make_sync_session)
async_session = pytest.fixture(depys.app.make_async_session)


@pytest.fixture
def system():
    yield depys.app.system


@pytest.fixture
def started_system(system):
    ctx, stack = depys.utils.start_system(system)
    yield ctx
    stack.close()


@pytest.fixture
def app(system):
    app = depys.utils.app_factory(system, "app")
    yield app


@pytest.fixture
def client(app):
    with fastapi.testclient.TestClient(app) as client:
        yield client
