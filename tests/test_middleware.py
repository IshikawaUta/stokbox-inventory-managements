"""Test untuk app.py ETagMiddleware."""
from __future__ import annotations

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class FakeScope:
    """Helper untuk membuat ASGI scope sederhana."""
    def __init__(self, method="GET", path="/", headers=None, scope_type="http"):
        self._scope = {
            "type": scope_type,
            "method": method,
            "path": path,
            "headers": headers or [],
        }

    def as_dict(self):
        return self._scope


class TestETagMiddleware:
    @pytest.fixture
    def etag_app(self):
        from app import ETagMiddleware
        return ETagMiddleware

    def _make_app(self, response_body=b'{"key": "value"}', content_type="application/json"):
        """Buat mock app ASGI yang mengembalikan JSON response."""
        async def app(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", content_type.encode("latin-1")),
                    (b"content-length", str(len(response_body)).encode("latin-1")),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": response_body,
                "more_body": False,
            })
        return app

    @pytest.mark.asyncio
    async def test_etag_added_to_json_response(self, etag_app):
        body = b'{"key": "value"}'
        inner_app = self._make_app(body)
        middleware = etag_app(inner_app)

        scope = FakeScope().as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        start_msg = sent_messages[0]
        headers = dict(start_msg["headers"])
        assert b"etag" in headers

    @pytest.mark.asyncio
    async def test_etag_matches_md5_of_body(self, etag_app):
        body = b'{"key": "value"}'
        inner_app = self._make_app(body)
        middleware = etag_app(inner_app)

        scope = FakeScope().as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        expected_etag = hashlib.md5(body).hexdigest()
        start_msg = sent_messages[0]
        headers = dict(start_msg["headers"])
        actual_etag = headers[b"etag"].decode("latin-1").strip('"')
        assert actual_etag == expected_etag

    @pytest.mark.asyncio
    async def test_304_not_modified_for_matching_etag(self, etag_app):
        body = b'{"key": "value"}'
        expected_etag = hashlib.md5(body).hexdigest()
        inner_app = self._make_app(body)
        middleware = etag_app(inner_app)

        scope = FakeScope(headers=[
            (b"if-none-match", f'"{expected_etag}"'.encode("latin-1")),
        ]).as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        assert sent_messages[0]["status"] == 304

    @pytest.mark.asyncio
    async def test_skips_non_get_requests(self, etag_app):
        body = b'{"key": "value"}'
        inner_app = self._make_app(body)
        middleware = etag_app(inner_app)

        scope = FakeScope(method="POST").as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        # Non-GET: response harus dikirim langsung tanpa buffering ETag
        assert len(sent_messages) == 2
        assert sent_messages[0]["status"] == 200
        headers = dict(sent_messages[0]["headers"])
        assert b"etag" not in headers

    @pytest.mark.asyncio
    async def test_skips_non_json_response(self, etag_app):
        body = b"<html><body>Hello</body></html>"
        inner_app = self._make_app(body, content_type="text/html")
        middleware = etag_app(inner_app)

        scope = FakeScope().as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        # Non-JSON: tidak ada ETag header
        headers = dict(sent_messages[0]["headers"])
        assert b"etag" not in headers

    @pytest.mark.asyncio
    async def test_skips_non_http_scope(self, etag_app):
        inner_app = self._make_app()
        middleware = etag_app(inner_app)

        scope = {"type": "websocket"}
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)
        # Non-HTTP scope: middleware meneruskan ke inner app tanpa buffering ETag
        assert len(sent_messages) == 2
        assert sent_messages[0]["status"] == 200
        headers = dict(sent_messages[0]["headers"])
        assert b"etag" not in headers

    @pytest.mark.asyncio
    async def test_etag_not_added_for_non_matching_if_none_match(self, etag_app):
        body = b'{"key": "value"}'
        inner_app = self._make_app(body)
        middleware = etag_app(inner_app)

        scope = FakeScope(headers=[
            (b"if-none-match", b'"different-etag"'),
        ]).as_dict()
        sent_messages = []

        async def send(msg):
            sent_messages.append(msg)

        await middleware(scope, None, send)

        # Harus return 200 dengan body, bukan 304
        assert sent_messages[0]["status"] == 200
        assert len(sent_messages) == 2
