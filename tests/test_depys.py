import pytest


@pytest.fixture
def current_ip(sync_session):
    return sync_session.get("https://icanhazip.com").text.strip()

@pytest.fixture
def also_current_ip(started_system):
    return started_system["syncsession"]().get("https://icanhazip.com").text.strip()


def test_sync(current_ip, client):
    ip = client.get("/sync/get_ip").text.strip()
    assert ip == current_ip


def test_async(also_current_ip, client):
    ip = client.get("/async/get_ip").text.strip()
    assert ip == also_current_ip
