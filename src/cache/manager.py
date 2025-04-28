"""
Cache Manager module for Financial Analysis System.
Provides caching functionality to improve performance.
"""

import functools
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple


class CacheManager:
    """
    Manages caching for expensive operations like LLM calls and data analysis.
    """

    def __init__(
        self, cache_dir: str = "cache", max_age_days: int = 7, memcache_size: int = 100
    ):
        """
        Initialise the CacheManager.

        Args:
            cache_dir: Directory to store persistent cache
            max_age_days: Maximum age for cache entries in days
            memcache_size: Maximum number of entries in memory cache
        """
        self.cache_dir = cache_dir
        self.max_age = timedelta(days=max_age_days)
        self.memcache_size = memcache_size
        self.memcache = {}

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        # Initialise lock for thread safety
        self.lock = threading.Lock()

        # Clean old cache entries on startup
        self.clean_old_entries()

    def _generate_key(self, data: Any) -> str:
        """
        Generate a cache key based on the input data.

        Args:
            data: Input data to hash

        Returns:
            Hash string to use as cache key
        """
        # Convert the data to a string and hash it
        if isinstance(data, (dict, list, tuple)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.md5(data_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        # Try memory cache first (faster)
        with self.lock:
            if key in self.memcache:
                entry = self.memcache[key]

                # Check if expired
                if entry["timestamp"] + self.max_age.total_seconds() < time.time():
                    del self.memcache[key]
                    return None

                # Return the cached value
                return entry["value"]

        # Try persistent cache if not in memory
        cache_file = os.path.join(self.cache_dir, f"{key}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache_entry = json.load(f)

                # Check if expired
                timestamp = cache_entry["timestamp"]
                if timestamp + self.max_age.total_seconds() < time.time():
                    # Remove expired entry
                    os.remove(cache_file)
                    return None

                # Add to memory cache for faster access next time
                with self.lock:
                    self._add_to_memcache(key, cache_entry["value"], timestamp)

                return cache_entry["value"]

            except (json.JSONDecodeError, KeyError):
                # Invalid cache entry, remove it
                os.remove(cache_file)
                return None

        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        timestamp = time.time()

        # Add to memory cache
        with self.lock:
            self._add_to_memcache(key, value, timestamp)

        # Add to persistent cache
        cache_entry = {"timestamp": timestamp, "value": value}

        cache_file = os.path.join(self.cache_dir, f"{key}.json")

        with open(cache_file, "w") as f:
            json.dump(cache_entry, f)

    def _add_to_memcache(self, key: str, value: Any, timestamp: float) -> None:
        """
        Add a value to the memory cache, managing size limits.

        Args:
            key: Cache key
            value: Value to cache
            timestamp: Timestamp for the cache entry
        """
        # If we're at capacity, remove the oldest entry
        if len(self.memcache) >= self.memcache_size:
            oldest_key = min(
                self.memcache.keys(), key=lambda k: self.memcache[k]["timestamp"]
            )
            del self.memcache[oldest_key]

        # Add the new entry
        self.memcache[key] = {"timestamp": timestamp, "value": value}

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was found and invalidated, False otherwise
        """
        found = False

        # Remove from memory cache
        with self.lock:
            if key in self.memcache:
                del self.memcache[key]
                found = True

        # Remove from persistent cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            found = True

        return found

    def clean_old_entries(self) -> int:
        """
        Clean old entries from the cache.

        Returns:
            Number of entries cleaned
        """
        count = 0

        # Clean memory cache
        with self.lock:
            current_time = time.time()
            keys_to_remove = []

            for key, entry in self.memcache.items():
                if entry["timestamp"] + self.max_age.total_seconds() < current_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.memcache[key]
                count += 1

        # Clean persistent cache
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                cache_file = os.path.join(self.cache_dir, filename)

                try:
                    with open(cache_file, "r") as f:
                        cache_entry = json.load(f)

                    timestamp = cache_entry["timestamp"]
                    if timestamp + self.max_age.total_seconds() < time.time():
                        os.remove(cache_file)
                        count += 1

                except (json.JSONDecodeError, KeyError):
                    # Invalid cache entry, remove it
                    os.remove(cache_file)
                    count += 1

        return count

    def clear_all(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0

        # Clear memory cache
        with self.lock:
            count += len(self.memcache)
            self.memcache.clear()

        # Clear persistent cache
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                os.remove(os.path.join(self.cache_dir, filename))
                count += 1

        return count

    def cached_function(self, prefix: str = ""):
        """
        Decorator to cache function results.

        Args:
            prefix: Optional prefix for cache keys

        Returns:
            Decorator function
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name, args, and kwargs
                cache_data = {"func": func.__name__, "args": args, "kwargs": kwargs}

                if prefix:
                    key = f"{prefix}_{self._generate_key(cache_data)}"
                else:
                    key = self._generate_key(cache_data)

                # Try to get from cache
                cached_result = self.get(key)
                if cached_result is not None:
                    return cached_result

                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(key, result)

                return result

            return wrapper

        return decorator

    def cached_method(self, prefix: str = ""):
        """
        Decorator to cache class method results.

        Args:
            prefix: Optional prefix for cache keys

        Returns:
            Decorator function
        """

        def decorator(method):
            @functools.wraps(method)
            def wrapper(self_instance, *args, **kwargs):
                # Generate cache key from class name, method name, args, and kwargs
                cache_data = {
                    "class": self_instance.__class__.__name__,
                    "method": method.__name__,
                    "id": id(
                        self_instance
                    ),  # Include instance id to differentiate instances
                    "args": args,
                    "kwargs": kwargs,
                }

                if prefix:
                    key = f"{prefix}_{self._generate_key(cache_data)}"
                else:
                    key = self._generate_key(cache_data)

                # Try to get from cache
                cached_result = self.get(key)
                if cached_result is not None:
                    return cached_result

                # Call the method and cache the result
                result = method(self_instance, *args, **kwargs)
                self.set(key, result)

                return result

            return wrapper

        return decorator

    def timed_invalidation(self, keys_or_prefixes: list, interval_seconds: int):
        """
        Start a thread to invalidate specific keys at regular intervals.

        Args:
            keys_or_prefixes: List of keys or key prefixes to invalidate
            interval_seconds: Interval between invalidations in seconds

        Returns:
            Thread object for the invalidation process
        """

        def invalidation_worker():
            while True:
                for key_or_prefix in keys_or_prefixes:
                    if key_or_prefix.endswith("*"):
                        # This is a prefix, invalidate all matching keys
                        prefix = key_or_prefix[:-1]
                        self._invalidate_by_prefix(prefix)
                    else:
                        # This is a single key
                        self.invalidate(key_or_prefix)

                # Sleep for the specified interval
                time.sleep(interval_seconds)

        # Start the invalidation thread
        thread = threading.Thread(target=invalidation_worker, daemon=True)
        thread.start()

        return thread

    def _invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache entries with keys starting with the specified prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Number of entries invalidated
        """
        count = 0

        # Invalidate in memory cache
        with self.lock:
            keys_to_remove = [key for key in self.memcache if key.startswith(prefix)]
            for key in keys_to_remove:
                del self.memcache[key]
                count += 1

        # Invalidate in persistent cache
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                key = filename[:-5]  # Remove .json extension
                if key.startswith(prefix):
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1

        return count
