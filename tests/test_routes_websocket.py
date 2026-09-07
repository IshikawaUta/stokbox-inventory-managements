"""Test untuk routes/websocket.py — broadcast_notification, connected clients, heartbeat."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from routes.websocket import (
    _connected_clients,
    broadcast_notification,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
)


class TestHeartbeatConstants:
    def test_heartbeat_interval_exists(self):
        assert HEARTBEAT_INTERVAL == 30

    def test_heartbeat_timeout_exists(self):
        assert HEARTBEAT_TIMEOUT == 10

    def test_heartbeat_interval_positive(self):
        assert HEARTBEAT_INTERVAL > 0

    def test_heartbeat_timeout_less_than_interval(self):
        assert HEARTBEAT_TIMEOUT < HEARTBEAT_INTERVAL


class TestConnectedClients:
    def test_connected_clients_is_set(self):
        assert isinstance(_connected_clients, set)

    def test_connected_clients_initially_empty_after_reset(self):
        _connected_clients.clear()
        assert len(_connected_clients) == 0


class TestBroadcastNotification:
    @pytest.fixture(autouse=True)
    def _clear_clients(self):
        _connected_clients.clear()
        yield
        _connected_clients.clear()

    def test_broadcast_with_no_clients(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"msg": "test"}))
        loop.close()

    def test_broadcast_with_connected_client(self):
        mock_ws = AsyncMock()
        _connected_clients.add(mock_ws)
        msg = {"type": "test", "data": "hello"}

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification(msg))
        loop.close()

        mock_ws.send_text.assert_called_once()
        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["type"] == "test"
        assert sent["data"] == "hello"

    def test_broadcast_with_multiple_clients(self):
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        _connected_clients.add(mock_ws1)
        _connected_clients.add(mock_ws2)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"type": "ping"}))
        loop.close()

        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()

    def test_broadcast_removes_disconnected_client(self):
        mock_ws = AsyncMock()
        mock_ws.send_text.side_effect = Exception("Connection closed")
        _connected_clients.add(mock_ws)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"msg": "test"}))
        loop.close()

        assert mock_ws not in _connected_clients

    def test_broadcast_keeps_connected_client(self):
        mock_ws = AsyncMock()
        _connected_clients.add(mock_ws)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"msg": "test"}))
        loop.close()

        assert mock_ws in _connected_clients

    def test_broadcast_json_serialization(self):
        mock_ws = AsyncMock()
        _connected_clients.add(mock_ws)

        msg = {"count": 5, "items": [1, 2, 3]}
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification(msg))
        loop.close()

        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["count"] == 5
        assert sent["items"] == [1, 2, 3]


class TestWebSocketEndpoint:
    def test_ws_endpoint_exists(self):
        from routes.websocket import ws_bp
        assert ws_bp is not None

    def test_ws_blueprint_url_prefix(self):
        from routes.websocket import ws_bp
        assert ws_bp.url_prefix == "/ws"
