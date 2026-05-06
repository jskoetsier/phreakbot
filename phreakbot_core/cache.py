#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caching utilities for PhreakBot."""

import time


class CacheMixin:
    """Mixin for TTL-based caching of user permissions and info."""

    def _is_cache_valid(self, cache_key):
        """Check if a cached item is still valid based on TTL"""
        if cache_key not in self.cache["cache_timestamps"]:
            return False
        age = time.time() - self.cache["cache_timestamps"][cache_key]
        return age < self.cache["cache_ttl"]

    def _cache_set(self, cache_type, key, value):
        """Set a value in the cache with timestamp"""
        cache_key = f"{cache_type}:{key}"
        self.cache[cache_type][key] = value
        self.cache["cache_timestamps"][cache_key] = time.time()
        self.logger.debug(f"Cached {cache_key}")

    def _cache_get(self, cache_type, key):
        """Get a value from cache if it exists and is valid"""
        cache_key = f"{cache_type}:{key}"
        if not self._is_cache_valid(cache_key):
            if key in self.cache[cache_type]:
                del self.cache[cache_type][key]
            if cache_key in self.cache["cache_timestamps"]:
                del self.cache["cache_timestamps"][cache_key]
            return None
        return self.cache[cache_type].get(key)

    def _cache_invalidate(self, cache_type, key=None):
        """Invalidate cache entries. If key is None, invalidate all entries of that type"""
        if key is None:
            self.cache[cache_type] = {}
            keys_to_remove = [
                k for k in self.cache["cache_timestamps"].keys()
                if k.startswith(f"{cache_type}:")
            ]
            for k in keys_to_remove:
                del self.cache["cache_timestamps"][k]
            self.logger.debug(f"Invalidated all {cache_type} cache")
        else:
            cache_key = f"{cache_type}:{key}"
            if key in self.cache[cache_type]:
                del self.cache[cache_type][key]
            if cache_key in self.cache["cache_timestamps"]:
                del self.cache["cache_timestamps"][cache_key]
            self.logger.debug(f"Invalidated cache for {cache_key}")
