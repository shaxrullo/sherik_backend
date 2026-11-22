"""
Optimized matching services with Redis caching.

This module provides cached versions of the matching algorithm
to improve performance on large datasets.
"""

from django.core.cache import cache
from django.db.models import Q
from users.models import User
from listings.models import Listing
from config.cache_utils import cache_key, clear_user_cache, clear_listing_cache
from matching.services import calculate_match_score
import logging

logger = logging.getLogger(__name__)


class CachedMatchingService:
    """Matching service with Redis caching."""
    
    # Cache timeouts
    MATCH_SCORE_TIMEOUT = 3600  # 1 hour
    RECOMMENDATIONS_TIMEOUT = 1800  # 30 minutes
    USER_PREFERENCES_TIMEOUT = 7200  # 2 hours
    
    @staticmethod
    def get_match_score(user: User, listing: Listing, force_refresh=False):
        """
        Get match score with caching.
        
        Args:
            user: User object
            listing: Listing object
            force_refresh: If True, bypass cache and recalculate
        
        Returns:
            Dict with match score details
        """
        if not force_refresh:
            # Try to get from cache
            cache_key_str = cache_key(
                'matching_score',
                f'{user.id}_{listing.id}'
            )
            
            cached_score = cache.get(cache_key_str)
            if cached_score is not None:
                logger.debug(f"Cache hit for match score: user={user.id}, listing={listing.id}")
                return cached_score
        
        # Calculate fresh score
        logger.debug(f"Calculating fresh match score: user={user.id}, listing={listing.id}")
        score = calculate_match_score(user, listing)
        
        # Cache the result
        try:
            cache_key_str = cache_key('matching_score', f'{user.id}_{listing.id}')
            cache.set(
                cache_key_str,
                score,
                CachedMatchingService.MATCH_SCORE_TIMEOUT
            )
        except Exception as e:
            logger.warning(f"Error caching match score: {e}")
        
        return score
    
    @staticmethod
    def get_recommendations_for_user(user: User, limit=20, force_refresh=False):
        """
        Get listing recommendations for a user with caching.
        
        Args:
            user: User object
            limit: Maximum number of recommendations
            force_refresh: If True, bypass cache and recalculate
        
        Returns:
            List of (listing, score) tuples sorted by score
        """
        # Try cache first
        if not force_refresh:
            cache_key_str = cache_key('recommendations', f'{user.id}', limit=limit)
            cached_recs = cache.get(cache_key_str)
            if cached_recs is not None:
                logger.debug(f"Cache hit for recommendations: user={user.id}")
                return cached_recs
        
        logger.debug(f"Calculating fresh recommendations: user={user.id}")
        
        # Get active, approved listings (excluding user's own listings)
        listings = Listing.objects.filter(
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED
        ).exclude(
            author_id=user.id
        ).select_related('author', 'city', 'district')[:100]  # Limit initial query
        
        # Calculate scores for each listing
        scored_listings = []
        for listing in listings:
            try:
                score = CachedMatchingService.get_match_score(user, listing)
                scored_listings.append({
                    'listing': listing,
                    'score': score
                })
            except Exception as e:
                logger.warning(f"Error scoring listing {listing.id}: {e}")
                continue
        
        # Sort by total score descending
        scored_listings.sort(
            key=lambda x: x['score'].get('total_score', 0),
            reverse=True
        )
        
        # Take top recommendations
        recommendations = scored_listings[:limit]
        
        # Cache the recommendations
        try:
            cache_key_str = cache_key('recommendations', f'{user.id}', limit=limit)
            cache.set(
                cache_key_str,
                recommendations,
                CachedMatchingService.RECOMMENDATIONS_TIMEOUT
            )
        except Exception as e:
            logger.warning(f"Error caching recommendations: {e}")
        
        return recommendations
    
    @staticmethod
    def invalidate_user_matching_cache(user_id):
        """
        Invalidate all matching-related cache for a user.
        Call this when user preferences change.
        
        Args:
            user_id: User ID
        """
        clear_user_cache(user_id)
        logger.info(f"Invalidated matching cache for user: {user_id}")
    
    @staticmethod
    def invalidate_listing_matching_cache(listing_id):
        """
        Invalidate all matching-related cache for a listing.
        Call this when listing is modified.
        
        Args:
            listing_id: Listing ID
        """
        clear_listing_cache(listing_id)
        logger.info(f"Invalidated matching cache for listing: {listing_id}")
    
    @staticmethod
    def bulk_invalidate_all_recommendations():
        """
        Invalidate all recommendation caches (expensive operation).
        Call this after major algorithm changes.
        """
        try:
            # Try to delete all recommendations from cache
            # This is backend-specific and may not work for all cache backends
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern('matching_score:*')
                cache.delete_pattern('recommendations:*')
                logger.info("Bulk invalidated all matching caches")
        except Exception as e:
            logger.warning(f"Error bulk invalidating matching cache: {e}")
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics for monitoring."""
        try:
            if hasattr(cache, '_cache'):
                # For local memory cache
                return {
                    'backend': 'locmem',
                    'info': 'Local memory cache - no detailed stats available'
                }
            else:
                # For Redis cache
                info = cache.get_client().info()
                return {
                    'backend': 'redis',
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_operations': info.get('total_commands_processed')
                }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {'error': str(e)}
