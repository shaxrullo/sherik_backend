"""
Caching utilities for the application.

Provides decorators and helpers for Redis caching to improve performance.
"""

import hashlib
import json
from functools import wraps
from django.core.cache import cache
from django.utils.encoding import force_bytes
import logging

logger = logging.getLogger(__name__)


def cache_key(namespace, identifier, **kwargs):
    """
    Generate a cache key from namespace, identifier, and optional parameters.
    
    Args:
        namespace: Cache namespace (e.g., 'matching_scores')
        identifier: Unique identifier (e.g., user_id)
        **kwargs: Additional parameters to include in cache key
    
    Returns:
        Hashed cache key string
    """
    key_data = f"{namespace}:{identifier}"
    
    if kwargs:
        # Sort kwargs for consistency
        sorted_kwargs = sorted(kwargs.items())
        key_data += ":" + json.dumps(sorted_kwargs, sort_keys=True)
    
    # Hash the key to keep it short
    hashed = hashlib.md5(force_bytes(key_data)).hexdigest()
    return f"{namespace}:{hashed}"


def invalidate_cache_prefix(prefix):
    """
    Invalidate all cache keys starting with a prefix.
    
    Note: This requires Django cache backend to support key patterns.
    For Redis, this works naturally. For local cache, deletion is best-effort.
    
    Args:
        prefix: Cache key prefix to invalidate
    """
    try:
        # For Redis backend
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f"{prefix}*")
        # For local/other backends, we can try to delete specific keys if tracked
        logger.info(f"Invalidated cache prefix: {prefix}")
    except Exception as e:
        logger.warning(f"Error invalidating cache prefix {prefix}: {e}")


def cached(timeout=300, prefix=None):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        prefix: Cache key prefix (defaults to function name)
    
    Usage:
        @cached(timeout=600, prefix='my_function')
        def my_expensive_function(user_id, filters=None):
            return expensive_computation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_prefix = prefix or func.__name__
            
            # Create key from arguments
            key_args = str(args) + str(sorted(kwargs.items()))
            func_cache_key = cache_key(cache_prefix, hashlib.md5(force_bytes(key_args)).hexdigest())
            
            # Try to get from cache
            result = cache.get(func_cache_key)
            if result is not None:
                return result
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Store in cache
            try:
                cache.set(func_cache_key, result, timeout)
            except Exception as e:
                logger.warning(f"Error caching result for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    return decorator


def clear_user_cache(user_id):
    """
    Clear all cache entries for a specific user.
    Useful when user data changes (favorites, preferences, etc.)
    
    Args:
        user_id: User ID to clear cache for
    """
    prefixes_to_clear = [
        f'matching_scores:{user_id}',
        f'user_preferences:{user_id}',
        f'user_listings:{user_id}',
        f'user_favorites:{user_id}',
    ]
    
    for prefix in prefixes_to_clear:
        invalidate_cache_prefix(prefix)
    
    logger.info(f"Cleared cache for user: {user_id}")


def clear_listing_cache(listing_id):
    """
    Clear all cache entries for a specific listing.
    Useful when listing data changes.
    
    Args:
        listing_id: Listing ID to clear cache for
    """
    prefixes_to_clear = [
        f'listing_details:{listing_id}',
        f'listing_matching:{listing_id}',
        f'listing_similar:{listing_id}',
    ]
    
    for prefix in prefixes_to_clear:
        invalidate_cache_prefix(prefix)
    
    logger.info(f"Cleared cache for listing: {listing_id}")


class CacheStats:
    """Helper to track cache performance statistics."""
    
    _stats = {
        'hits': 0,
        'misses': 0,
        'errors': 0,
    }
    
    @classmethod
    def record_hit(cls):
        """Record a cache hit."""
        cls._stats['hits'] += 1
    
    @classmethod
    def record_miss(cls):
        """Record a cache miss."""
        cls._stats['misses'] += 1
    
    @classmethod
    def record_error(cls):
        """Record a cache error."""
        cls._stats['errors'] += 1
    
    @classmethod
    def get_stats(cls):
        """Get cache statistics."""
        total = cls._stats['hits'] + cls._stats['misses']
        hit_rate = (cls._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': cls._stats['hits'],
            'misses': cls._stats['misses'],
            'errors': cls._stats['errors'],
            'total': total,
            'hit_rate': f"{hit_rate:.2f}%"
        }
    
    @classmethod
    def reset(cls):
        """Reset statistics."""
        cls._stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
        }
