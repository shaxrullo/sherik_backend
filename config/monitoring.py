"""
Monitoring and observability utilities for the application.

Integrates with Sentry for error tracking and provides monitoring endpoints.
"""

import sentry_sdk
import logging
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status

logger = logging.getLogger(__name__)


def capture_exception(exc, level='error', tags=None, extra=None):
    """
    Capture an exception in Sentry with additional context.
    
    Args:
        exc: Exception to capture
        level: Severity level (fatal, error, warning, info, debug)
        tags: Dict of tags to add to the event
        extra: Dict of extra data to include
    """
    if settings.SENTRY_DSN and not settings.DEBUG:
        try:
            with sentry_sdk.push_scope() as scope:
                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)
                if extra:
                    for key, value in extra.items():
                        scope.set_extra(key, value)
                
                scope.set_level(level)
                sentry_sdk.capture_exception(exc)
                logger.info(f"Exception captured in Sentry: {exc}")
        except Exception as e:
            logger.warning(f"Error capturing exception in Sentry: {e}")
    else:
        logger.debug(f"Sentry not configured or DEBUG mode - exception not captured: {exc}")


def capture_message(message, level='info', tags=None, extra=None):
    """
    Capture a message in Sentry.
    
    Args:
        message: Message to capture
        level: Severity level
        tags: Dict of tags
        extra: Dict of extra data
    """
    if settings.SENTRY_DSN and not settings.DEBUG:
        try:
            with sentry_sdk.push_scope() as scope:
                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)
                if extra:
                    for key, value in extra.items():
                        scope.set_extra(key, value)
                
                scope.set_level(level)
                sentry_sdk.capture_message(message)
                logger.info(f"Message captured in Sentry: {message}")
        except Exception as e:
            logger.warning(f"Error capturing message in Sentry: {e}")
    else:
        logger.debug(f"Sentry not configured or DEBUG mode - message not captured: {message}")


@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_status(request):
    """
    Monitoring status endpoint - shows Sentry and other monitoring configuration.
    
    Returns:
    - 200 OK with monitoring configuration status
    """
    monitoring_data = {
        'monitoring': {
            'sentry': {
                'enabled': bool(settings.SENTRY_DSN) and not settings.DEBUG,
                'environment': settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else 'unknown',
                'dsn': settings.SENTRY_DSN[:20] + '***' if settings.SENTRY_DSN else None
            },
            'logging': {
                'enabled': True,
                'level': 'INFO'
            },
            'health_checks': {
                'database': True,
                'cache': hasattr(settings, 'CACHES') and settings.CACHES.get('default'),
                'storage': hasattr(settings, 'STORAGES')
            }
        },
        'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
    }
    
    return Response(monitoring_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_sentry(request):
    """
    Test Sentry integration by capturing a test exception.
    
    Returns:
    - 200 OK if Sentry is configured
    - 503 Service Unavailable if Sentry is not configured
    """
    if not settings.SENTRY_DSN:
        return Response(
            {
                'status': 'error',
                'message': 'Sentry not configured (SENTRY_DSN environment variable not set)',
                'debug_mode': settings.DEBUG
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Capture a test exception
        try:
            raise Exception("🧪 Sentry Test Exception - This is a test from the monitoring endpoint")
        except Exception as e:
            capture_exception(
                e,
                level='info',
                tags={'test': 'true', 'endpoint': 'test_sentry'},
                extra={'test_message': 'Sentry integration test'}
            )
        
        return Response(
            {
                'status': 'success',
                'message': 'Test exception sent to Sentry',
                'instruction': 'Check your Sentry dashboard for the test event'
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error testing Sentry: {e}")
        return Response(
            {
                'status': 'error',
                'message': f'Error sending test event: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MonitoringContextManager:
    """Context manager for capturing Sentry events with context."""
    
    def __init__(self, operation_name, tags=None, extra=None):
        self.operation_name = operation_name
        self.tags = tags or {}
        self.extra = extra or {}
        self.scope = None
    
    def __enter__(self):
        if settings.SENTRY_DSN and not settings.DEBUG:
            self.scope = sentry_sdk.push_scope()
            self.scope.__enter__()
            
            # Add automatic tags
            self.scope.set_tag('operation', self.operation_name)
            
            # Add custom tags and extra data
            for key, value in self.tags.items():
                self.scope.set_tag(key, value)
            for key, value in self.extra.items():
                self.scope.set_extra(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scope:
            self.scope.__exit__(exc_type, exc_val, exc_tb)
        
        # Capture exception if one occurred
        if exc_type is not None and settings.SENTRY_DSN and not settings.DEBUG:
            sentry_sdk.capture_exception((exc_type, exc_val, exc_tb))
        
        return False  # Don't suppress the exception


# Example usage in views/services:
# from config.monitoring import MonitoringContextManager, capture_exception
#
# with MonitoringContextManager('list_creation', tags={'user': user.id}):
#     # Your code here
#     result = perform_expensive_operation()
