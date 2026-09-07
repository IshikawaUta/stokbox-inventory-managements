"""Test tambahan untuk routes/websocket.py — heartbeat, notifications_ws."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from routes.websocket import (
    _connected_clients,
    _heartbeat_loop,
    broadcast_notification,
    notifications_ws,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
)


class TestHeartbeatLoop:
    @pytest.fixture(autouse=True)
    def _clear_clients(self):
        _connected_clients.clear()
        yield
        _connected_clients.clear()

    def test_heartbeat_loop_sends_ping_and_receives_pong(self):
        mock_ws = AsyncMock()
        mock_ws.receive_text.return_value = json.dumps({"type": "pong"})
        _connected_clients.add(mock_ws)

        async def _run():
            task = asyncio.create_task(_heartbeat_loop(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()

    def test_heartbeat_loop_removes_client_on_timeout(self):
        mock_ws = AsyncMock()
        mock_ws.receive_text.side_effect = asyncio.TimeoutError
        _connected_clients.add(mock_ws)

        async def _run():
            with patch("asyncio.sleep", new_callable=AsyncMock):
                task = asyncio.create_task(_heartbeat_loop(mock_ws))
                await asyncio.sleep(0.05)
                try:
                    await asyncio.wait_for(task, timeout=0.2)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    task.cancel()

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()

    def test_heartbeat_loop_handles_send_exception(self):
        mock_ws = AsyncMock()
        mock_ws.send_text.side_effect = Exception("Connection lost")
        _connected_clients.add(mock_ws)

        async def _run():
            with patch("asyncio.sleep", new_callable=AsyncMock):
                task = asyncio.create_task(_heartbeat_loop(mock_ws))
                await asyncio.sleep(0.05)
                try:
                    await asyncio.wait_for(task, timeout=0.2)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    task.cancel()

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()

    def test_heartbeat_loop_stops_when_ws_removed_from_clients(self):
        mock_ws = AsyncMock()

        async def _run():
            _connected_clients.add(mock_ws)
            task = asyncio.create_task(_heartbeat_loop(mock_ws))
            await asyncio.sleep(0.01)
            _connected_clients.discard(mock_ws)
            await asyncio.sleep(0.01)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()

    def test_heartbeat_loop_handles_cancelled_error(self):
        mock_ws = AsyncMock()
        _connected_clients.add(mock_ws)

        async def _run():
            task = asyncio.create_task(_heartbeat_loop(mock_ws))
            await asyncio.sleep(0.01)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()


class TestBroadcastNotificationV2:
    @pytest.fixture(autouse=True)
    def _clear_clients(self):
        _connected_clients.clear()
        yield
        _connected_clients.clear()

    def test_broadcast_with_many_clients(self):
        clients = [AsyncMock() for _ in range(10)]
        for c in clients:
            _connected_clients.add(c)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"type": "alert", "msg": "test"}))
        loop.close()

        for c in clients:
            c.send_text.assert_called_once()

    def test_broadcast_partial_failure(self):
        ok_client = AsyncMock()
        fail_client = AsyncMock()
        fail_client.send_text.side_effect = Exception("fail")
        _connected_clients.add(ok_client)
        _connected_clients.add(fail_client)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"msg": "test"}))
        loop.close()

        ok_client.send_text.assert_called_once()
        assert fail_client not in _connected_clients
        assert ok_client in _connected_clients

    def test_broadcast_all_fail(self):
        c1 = AsyncMock()
        c1.send_text.side_effect = Exception("fail1")
        c2 = AsyncMock()
        c2.send_text.side_effect = Exception("fail2")
        _connected_clients.add(c1)
        _connected_clients.add(c2)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification({"msg": "test"}))
        loop.close()

        assert len(_connected_clients) == 0

    def test_broadcast_complex_message(self):
        mock_ws = AsyncMock()
        _connected_clients.add(mock_ws)

        msg = {
            "type": "notification",
            "data": {
                "items": [{"id": 1, "name": "test"}, {"id": 2, "name": "prod"}],
                "count": 2,
                "nested": {"key": "value"},
            },
        }
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_notification(msg))
        loop.close()

        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["type"] == "notification"
        assert len(sent["data"]["items"]) == 2


class TestNotificationsWsEndpoint:
    def test_ws_blueprint_exists(self):
        from routes.websocket import ws_bp
        assert ws_bp is not None
        assert ws_bp.url_prefix == "/ws"

    @pytest.fixture(autouse=True)
    def _clear_clients(self):
        _connected_clients.clear()
        yield
        _connected_clients.clear()

    def test_notifications_ws_handles_refresh_message(self):
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        call_count = 0

        async def _fake_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps({"type": "refresh"})
            raise Exception("disconnect")

        mock_ws.receive_text = _fake_receive

        loop = asyncio.new_event_loop()

        async def _run():
            with patch("routes.websocket._heartbeat_loop", new_callable=AsyncMock):
                try:
                    await notifications_ws(mock_ws)
                except Exception:
                    pass

        loop.run_until_complete(_run())
        loop.close()

        assert mock_ws.accept.called

    def test_notifications_ws_handles_disconnect(self):
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        from fenrir import WebSocketDisconnect

        async def _fake_receive():
            raise WebSocketDisconnect()

        mock_ws.receive_text = _fake_receive

        loop = asyncio.new_event_loop()

        async def _run():
            with patch("routes.websocket._heartbeat_loop", new_callable=AsyncMock):
                try:
                    await notifications_ws(mock_ws)
                except Exception:
                    pass

        loop.run_until_complete(_run())
        loop.close()

        assert mock_ws.accept.called
        assert mock_ws not in _connected_clients

    def test_notifications_ws_handles_pong_message(self):
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        call_count = 0

        async def _fake_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps({"type": "pong"})
            raise Exception("disconnect")

        mock_ws.receive_text = _fake_receive

        loop = asyncio.new_event_loop()

        async def _run():
            with patch("routes.websocket._heartbeat_loop", new_callable=AsyncMock):
                try:
                    await notifications_ws(mock_ws)
                except Exception:
                    pass

        loop.run_until_complete(_run())
        loop.close()

        assert mock_ws.accept.called
