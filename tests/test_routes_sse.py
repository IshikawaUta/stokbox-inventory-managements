"""Test untuk routes/sse.py — SSE generators dan endpoint properties."""
from __future__ import annotations

import asyncio
import json

import pytest


class TestSSEStockAlerts:
    def test_stock_alerts_endpoint_exists(self):
        from routes.sse import sse_bp
        assert sse_bp is not None

    def test_stock_alerts_blueprint_url_prefix(self):
        from routes.sse import sse_bp
        assert sse_bp.url_prefix == "/api/sse"


class TestSSEActivity:
    def test_activity_endpoint_exists(self):
        from routes.sse import sse_bp
        assert sse_bp is not None


class TestGenerateStockAlerts:
    def test_returns_async_generator(self):
        from routes.sse import _generate_stock_alerts
        import inspect
        gen = _generate_stock_alerts()
        assert inspect.isasyncgen(gen)

    def test_yields_dict_with_required_keys(self):
        from routes.sse import _generate_stock_alerts

        async def _test():
            gen = _generate_stock_alerts()
            try:
                item = await gen.__anext__()
                assert isinstance(item, dict)
                assert "id" in item
                assert "event" in item
                assert "data" in item
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_event_type_is_stock_alert(self):
        from routes.sse import _generate_stock_alerts

        async def _test():
            gen = _generate_stock_alerts()
            try:
                item = await gen.__anext__()
                assert item["event"] == "stock_alert"
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_data_is_valid_json(self):
        from routes.sse import _generate_stock_alerts

        async def _test():
            gen = _generate_stock_alerts()
            try:
                item = await gen.__anext__()
                data = json.loads(item["data"])
                assert isinstance(data, dict)
                assert data["type"] == "stock_alert"
                assert "count" in data
                assert "items" in data
                assert "message" in data
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_first_event_has_event_id_1(self):
        from routes.sse import _generate_stock_alerts

        async def _test():
            gen = _generate_stock_alerts()
            try:
                item = await gen.__anext__()
                assert item["id"] == "1"
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())


class TestGenerateActivity:
    def test_returns_async_generator(self):
        from routes.sse import _generate_activity
        import inspect
        gen = _generate_activity()
        assert inspect.isasyncgen(gen)

    def test_yields_dict_with_required_keys(self):
        from routes.sse import _generate_activity

        async def _test():
            gen = _generate_activity()
            try:
                item = await gen.__anext__()
                assert isinstance(item, dict)
                assert "id" in item
                assert "event" in item
                assert "data" in item
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_event_type_is_activity_update(self):
        from routes.sse import _generate_activity

        async def _test():
            gen = _generate_activity()
            try:
                item = await gen.__anext__()
                assert item["event"] == "activity_update"
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_data_is_valid_json(self):
        from routes.sse import _generate_activity

        async def _test():
            gen = _generate_activity()
            try:
                item = await gen.__anext__()
                data = json.loads(item["data"])
                assert data["type"] == "activity"
                assert "total" in data
                assert "items" in data
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())

    def test_first_event_has_event_id_1(self):
        from routes.sse import _generate_activity

        async def _test():
            gen = _generate_activity()
            try:
                item = await gen.__anext__()
                assert item["id"] == "1"
            finally:
                await gen.aclose()

        asyncio.get_event_loop().run_until_complete(_test())
