"""WebSocket routes untuk notifikasi real-time (stok rendah, aktivitas, dsb)."""
from __future__ import annotations

import asyncio
import json
from typing import Set

from fenrir import Blueprint, WebSocket, WebSocketDisconnect

from services import barang_service

ws_bp = Blueprint("websocket", url_prefix="/ws")

# ── Kumpulan client yang terhubung ──────────────────────────────────────
_connected_clients: Set[WebSocket] = set()

# ── Heartbeat configuration ─────────────────────────────────────────────
HEARTBEAT_INTERVAL = 30  # detik antara ping
HEARTBEAT_TIMEOUT = 10   # detik menunggu pong sebelum disconnect


async def broadcast_notification(message: dict) -> None:
    """Kirim notifikasi ke semua client yang terhubung."""
    payload = json.dumps(message, ensure_ascii=False, default=str)
    disconnected: list[WebSocket] = []
    for ws in _connected_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)
    # Bersihkan client yang sudah putus
    for ws in disconnected:
        _connected_clients.discard(ws)


async def _heartbeat_loop(websocket: WebSocket) -> None:
    """Kirim ping secara periodik dan tutup koneksi jika pong tidak diterima."""
    try:
        while websocket in _connected_clients:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if websocket not in _connected_clients:
                break
            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
                # Tunggu pong dari client dengan batas waktu
                pong_received = asyncio.Event()

                async def _wait_pong() -> None:
                    try:
                        data = await asyncio.wait_for(
                            websocket.receive_text(), timeout=HEARTBEAT_TIMEOUT
                        )
                        msg = json.loads(data)
                        if msg.get("type") == "pong":
                            pong_received.set()
                    except (asyncio.TimeoutError, Exception):
                        pass

                wait_task = asyncio.create_task(_wait_pong())
                await asyncio.wait_for(pong_received.wait(), timeout=HEARTBEAT_TIMEOUT)
                wait_task.cancel()
                try:
                    await wait_task
                except asyncio.CancelledError:
                    pass
            except asyncio.TimeoutError:
                # Pong tidak diterima dalam batas waktu, tutup koneksi
                _connected_clients.discard(websocket)
                try:
                    await websocket.close()
                except Exception:
                    pass
                break
            except Exception:
                _connected_clients.discard(websocket)
                try:
                    await websocket.close()
                except Exception:
                    pass
                break
    except asyncio.CancelledError:
        pass


@ws_bp.websocket("/notifications")
async def notifications_ws(websocket: WebSocket):
    """Endpoint WebSocket untuk notifikasi real-time.

    - Saat koneksi terbuka, langsung kirim daftar barang stok rendah.
    - Selanjutnya, kirim update secara periodik setiap ~30 detik.
    - Heartbeat ping/pong untuk mendeteksi koneksi mati.
    - Handle disconnect secara graceful.
    """
    await websocket.accept()
    _connected_clients.add(websocket)

    # Mulai heartbeat background task
    heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket))

    try:
        # Kirim data awal: daftar barang stok rendah
        low_stock = barang_service.list_low_stock(limit=20)
        await websocket.send_text(json.dumps({
            "type": "initial",
            "data": low_stock,
        }, ensure_ascii=False, default=str))

        # Dengarkan pesan dari client
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                msg_type = msg.get("type", "").lower() if isinstance(msg, dict) else data.strip().lower()

                if msg_type == "refresh":
                    low_stock = barang_service.list_low_stock(limit=20)
                    await websocket.send_text(json.dumps({
                        "type": "refresh",
                        "data": low_stock,
                    }, ensure_ascii=False, default=str))
                elif msg_type == "pong":
                    # Pong diterima, heartbeat aktif
                    pass
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        _connected_clients.discard(websocket)
