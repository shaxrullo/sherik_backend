"""Health check views for monitoring service status."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for load balancers and monitoring services.
    
    Returns:
    - 200 OK: Service is healthy
    - 503 Service Unavailable: Service has issues
    
    Checks:
    - Database connectivity
    - Service uptime
    - Basic system status
    """
    health_data = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['checks']['database'] = {
            'status': 'ok',
            'message': 'Database connection successful'
        }
    except Exception as e:
        logger.error(f"Health check: Database error - {str(e)}")
        health_data['status'] = 'unhealthy'
        health_data['checks']['database'] = {
            'status': 'error',
            'message': f'Database connection failed: {str(e)}'
        }
        return Response(health_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # Service info
    health_data['service'] = {
        'name': 'Backend Sherik API',
        'version': '1.0.0',
        'environment': 'production'  # This should come from settings
    }
    
    return Response(health_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check endpoint - more comprehensive than health check.
    Used by Kubernetes/orchestration tools.
    
    Returns:
    - 200 OK: Service is ready to handle requests
    - 503 Service Unavailable: Service is not ready
    """
    readiness_data = {
        'ready': True,
        'timestamp': timezone.now().isoformat(),
        'readiness_checks': {}
    }
    
    # 1. Database connectivity check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM listings_listing")
            cursor.fetchone()
        readiness_data['readiness_checks']['database'] = {
            'status': 'ready',
            'message': 'Database is accessible'
        }
    except Exception as e:
        logger.error(f"Readiness check: Database error - {str(e)}")
        readiness_data['ready'] = False
        readiness_data['readiness_checks']['database'] = {
            'status': 'not_ready',
            'message': f'Database error: {str(e)}'
        }
    
    # 2. Cache connectivity check (if Redis is configured)
    try:
        from django.core.cache import cache
        cache.set('readiness_check', 'ok', 1)
        cache.get('readiness_check')
        readiness_data['readiness_checks']['cache'] = {
            'status': 'ready',
            'message': 'Cache is accessible'
        }
    except Exception as e:
        # Cache is optional, so don't fail the entire check
        logger.warning(f"Readiness check: Cache warning - {str(e)}")
        readiness_data['readiness_checks']['cache'] = {
            'status': 'warning',
            'message': f'Cache not available: {str(e)}'
        }
    
    # 3. Media storage check (optional)
    try:
        from django.core.files.storage import default_storage
        default_storage.exists('.')
        readiness_data['readiness_checks']['storage'] = {
            'status': 'ready',
            'message': 'Media storage is accessible'
        }
    except Exception as e:
        logger.warning(f"Readiness check: Storage warning - {str(e)}")
        readiness_data['readiness_checks']['storage'] = {
            'status': 'warning',
            'message': f'Storage not available: {str(e)}'
        }
    
    http_status = status.HTTP_200_OK if readiness_data['ready'] else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(readiness_data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check endpoint - checks if application process is alive.
    Used by container orchestration (Docker, Kubernetes).
    
    Returns:
    - 200 OK: Application is alive
    - Should always return 200 unless process is completely dead
    """
    return Response({
        'alive': True,
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)
