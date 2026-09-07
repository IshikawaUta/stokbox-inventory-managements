"""Server-Sent Events (SSE) untuk streaming data real-time."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fenrir import Blueprint, EventSourceResponse

from services import barang_service, aktivitas_service

sse_bp = Blueprint("sse", url_prefix="/api/sse")


async def _generate_stock_alerts() -> AsyncGenerator[dict, None]:
    """Generator untuk alert stok rendah. Polling setiap 15 detik."""
    event_id = 0
    last_count = 0
    while True:
        try:
            low_stock = barang_service.list_low_stock(limit=20)
            current_count = len(low_stock)

            # Kirim alert jika ada perubahan jumlah barang stok rendah
            if current_count != last_count or event_id == 0:
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "stock_alert",
                    "data": json.dumps({
                        "type": "stock_alert",
                        "count": current_count,
                        "items": low_stock,
                        "message": (
                            f"Terdapat {current_count} barang dengan stok rendah"
                            if current_count > 0
                            else "Semua stok barang dalam kondisi aman"
                        ),
                    }, ensure_ascii=False, default=str),
                }
                last_count = current_count

            await asyncio.sleep(15)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(15)


async def _generate_activity() -> AsyncGenerator[dict, None]:
    """Generator untuk aktivitas terbaru. Polling setiap 10 detik."""
    event_id = 0
    last_total = 0
    while True:
        try:
            result = aktivitas_service.list_aktivitas(page=1, per_page=5)
            items = result.get("data", [])
            current_total = result.get("total", 0)

            # Kirim update jika ada aktivitas baru
            if current_total != last_total or event_id == 0:
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "activity_update",
                    "data": json.dumps({
                        "type": "activity",
                        "total": current_total,
                        "items": items,
                    }, ensure_ascii=False, default=str),
                }
                last_total = current_total

            await asyncio.sleep(10)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(10)


@sse_bp.get("/stock-alerts")
async def stock_alerts_sse():
    """SSE endpoint untuk streaming alert stok rendah.

    Client: `new EventSource('/api/sse/stock-alerts')`
    Event: stock_alert — berisi daftar barang stok rendah.
    """
    return EventSourceResponse(_generate_stock_alerts())


@sse_bp.get("/activity")
async def activity_sse():
    """SSE endpoint untuk streaming log aktivitas terbaru.

    Client: `new EventSource('/api/sse/activity')`
    Event: activity_update — berisi aktivitas terbaru.
    """
    return EventSourceResponse(_generate_activity())
