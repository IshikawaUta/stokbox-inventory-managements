"""Synchronous in-memory cache untuk service layer (sync)."""
from __future__ import annotations

import hashlib
import time
import threading
from functools import wraps
from typing import Any, Callable, Optional


class SyncCache:
    """Thread-safe in-memory cache with TTL support. Synchronous API."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at and time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        with self._lock:
            expires_at = time.time() + ttl if ttl else 0
            self._store[key] = (value, expires_at)

    def invalidate(self, prefix: str) -> None:
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Singleton
cache = SyncCache()


def _make_cache_key(func: Callable, args: tuple, kwargs: dict, key_prefix: str) -> str:
    """Buat cache key dari nama fungsi + args + kwargs."""
    raw = f"{key_prefix}:{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(raw.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """Decorator untuk caching fungsi sync.

    Penggunaan:
        @cached(ttl=120, key_prefix="barang_list")
        def list_barang(keyword: str = "") -> list[dict]:
            ...

    Args:
        ttl: Waktu hidup cache dalam detik (default 300 = 5 menit).
        key_prefix: Prefix untuk cache key (memudahkan invalidasi massal).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _make_cache_key(func, args, kwargs, key_prefix)
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        # Simpan referensi ke fungsi asli untuk keperluan testing/debug
        wrapper._cache_prefix = key_prefix  # type: ignore[attr-defined]
        return wrapper

    return decorator
