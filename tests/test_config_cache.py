"""Test untuk config/cache.py — SyncCache, cached decorator, dan cache key generation."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from config.cache import SyncCache, _make_cache_key, cached, cache


class TestSyncCacheGet:
    def test_get_existing_key(self):
        c = SyncCache()
        c.set("key1", "value1", ttl=60)
        assert c.get("key1") == "value1"

    def test_get_missing_key(self):
        c = SyncCache()
        assert c.get("nonexistent") is None

    def test_get_returns_none_after_ttl_expiry(self):
        c = SyncCache()
        c.set("key1", "value1", ttl=1)
        with patch("config.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert c.get("key1") is None

    def test_get_returns_value_before_ttl_expiry(self):
        c = SyncCache()
        c.set("key1", "value1", ttl=60)
        assert c.get("key1") == "value1"

    def test_get_zero_ttl_never_expires(self):
        c = SyncCache()
        c.set("key1", "value1", ttl=0)
        with patch("config.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 99999
            assert c.get("key1") == "value1"


class TestSyncCacheSet:
    def test_set_and_get(self):
        c = SyncCache()
        c.set("k", [1, 2, 3])
        assert c.get("k") == [1, 2, 3]

    def test_set_overwrites_existing(self):
        c = SyncCache()
        c.set("k", "old")
        c.set("k", "new")
        assert c.get("k") == "new"

    def test_set_with_custom_ttl(self):
        c = SyncCache()
        c.set("k", "v", ttl=10)
        assert c.get("k") == "v"


class TestSyncCacheInvalidate:
    def test_invalidate_prefix_removes_matching(self):
        c = SyncCache()
        c.set("barang:1", "a")
        c.set("barang:2", "b")
        c.set("kategori:1", "c")
        c.invalidate("barang:")
        assert c.get("barang:1") is None
        assert c.get("barang:2") is None
        assert c.get("kategori:1") == "c"

    def test_invalidate_prefix_no_match(self):
        c = SyncCache()
        c.set("a", 1)
        c.invalidate("xyz")
        assert c.get("a") == 1

    def test_invalidate_empty_prefix(self):
        c = SyncCache()
        c.set("key", "val")
        c.invalidate("")
        assert c.get("key") is None


class TestSyncCacheClear:
    def test_clear_removes_all(self):
        c = SyncCache()
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is None
        assert c.get("b") is None

    def test_clear_empty_cache(self):
        c = SyncCache()
        c.clear()
        assert c.get("any") is None


class TestSingletonCache:
    def test_singleton_instance(self):
        from config.cache import cache as c1
        from config.cache import cache as c2
        assert c1 is c2

    def test_singleton_is_synccache(self):
        assert isinstance(cache, SyncCache)


class TestCachedDecorator:
    def test_cached_caches_result(self):
        call_count = 0

        @cached(ttl=60, key_prefix="test")
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_func(5)
        result2 = expensive_func(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_cached_different_args_different_cache(self):
        call_count = 0

        @cached(ttl=60, key_prefix="test")
        def func(x):
            nonlocal call_count
            call_count += 1
            return x

        func(1)
        func(2)
        assert call_count == 2

    def test_cached_cache_miss_after_invalidation(self):
        call_count = 0

        @cached(ttl=60, key_prefix="test_inv")
        def func():
            nonlocal call_count
            call_count += 1
            return "data"

        func()
        assert call_count == 1
        cache.clear()
        func()
        assert call_count == 2

    def test_cached_preserves_function_metadata(self):
        @cached(ttl=10, key_prefix="meta")
        def my_func():
            """Docstring saya."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Docstring saya."
        assert my_func._cache_prefix == "meta"


class TestMakeCacheKey:
    def test_key_generation_deterministic(self):
        def dummy():
            pass

        key1 = _make_cache_key(dummy, (1, 2), {"a": 3}, "prefix")
        key2 = _make_cache_key(dummy, (1, 2), {"a": 3}, "prefix")
        assert key1 == key2

    def test_key_different_for_different_args(self):
        def dummy():
            pass

        key1 = _make_cache_key(dummy, (1,), {}, "")
        key2 = _make_cache_key(dummy, (2,), {}, "")
        assert key1 != key2

    def test_key_different_for_different_prefix(self):
        def dummy():
            pass

        key1 = _make_cache_key(dummy, (), {}, "p1")
        key2 = _make_cache_key(dummy, (), {}, "p2")
        assert key1 != key2

    def test_key_is_string(self):
        def dummy():
            pass

        key = _make_cache_key(dummy, (), {}, "")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex digest
