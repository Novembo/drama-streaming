import pytest
from fakeredis import FakeRedis, FakeServer

# Must be imported before anything from `app`: it sets the environment variables the settings read.
from tests import support


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh schema + a fresh in-memory Redis for every test (rate limits and cache never leak between tests)."""
    from app.core import cache

    cache._client = FakeRedis(server=FakeServer(), decode_responses=True)
    support.reset_database()
    yield
