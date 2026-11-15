"""Tests for the SSE streaming module."""

import json

from fastapi import FastAPI

from app.market.cache import PriceCache
from app.market.stream import _generate_events, create_stream_router


class FakeRequest:
    """Minimal Request stand-in; disconnects after N is_disconnected checks."""

    def __init__(self, disconnect_after: int = 2, client=True):
        self._calls = 0
        self._after = disconnect_after
        self.client = type("C", (), {"host": "1.2.3.4"})() if client else None

    async def is_disconnected(self) -> bool:
        self._calls += 1
        return self._calls > self._after


async def _collect(cache, request, interval=0.01):
    return [e async for e in _generate_events(cache, request, interval=interval)]


class TestGenerateEvents:
    async def test_first_event_is_retry(self):
        events = await _collect(PriceCache(), FakeRequest(0))
        assert events == ["retry: 1000\n\n"]

    async def test_empty_cache_emits_no_data(self):
        events = await _collect(PriceCache(), FakeRequest(2))
        assert all(not e.startswith("data:") for e in events)

    async def test_emits_all_tickers_in_one_event(self):
        cache = PriceCache()
        cache.update("AAPL", 190.0)
        cache.update("GOOGL", 175.0)
        events = await _collect(cache, FakeRequest(1))
        data = [e for e in events if e.startswith("data:")]
        assert len(data) == 1
        payload = json.loads(data[0][len("data: "):])
        assert set(payload) == {"AAPL", "GOOGL"}
        assert payload["AAPL"]["price"] == 190.0

    async def test_unchanged_version_not_resent(self):
        cache = PriceCache()
        cache.update("AAPL", 190.0)
        events = await _collect(cache, FakeRequest(4))
        assert len([e for e in events if e.startswith("data:")]) == 1

    async def test_no_client_info(self):
        cache = PriceCache()
        cache.update("AAPL", 190.0)
        events = await _collect(cache, FakeRequest(1, client=False))
        assert len(events) == 2


class TestRouter:
    def test_route_registered(self):
        router = create_stream_router(PriceCache())
        assert [r.path for r in router.routes] == ["/api/stream/prices"]

    def test_factory_twice_no_duplicate_routes(self):
        cache = PriceCache()
        create_stream_router(cache)
        router = create_stream_router(cache)
        assert len(router.routes) == 1

    def test_mountable(self):
        app = FastAPI()
        app.include_router(create_stream_router(PriceCache()))
        assert "/api/stream/prices" in app.openapi()["paths"]
