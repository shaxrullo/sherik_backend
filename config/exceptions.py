"""
Custom exception handlers for standardized error responses.

All API errors follow a consistent format:
{
    "status": "error",
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {
        "field_name": ["error message"],
        ...
    },
    "timestamp": "2025-11-22T10:30:00Z"
}
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized error format.
    
    Wraps DRF's default exception handler and reformats responses.
    """
    
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Build custom error response
        error_response = {
            'status': 'error',
            'code': get_error_code(exc, response.status_code),
            'message': get_error_message(exc, response.data),
            'timestamp': timezone.now().isoformat()
        }
        
        # Add details if validation errors
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_response['details'] = extract_validation_details(response.data)
        elif response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_response['details'] = extract_validation_details(response.data)
        
        response.data = error_response
    else:
        # Handle unexpected server errors
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            exc_info=True,
            extra={'context': context}
        )
        
        response = Response(
            {
                'status': 'error',
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred. Please try again later.',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def get_error_code(exc, status_code):
    """
    Map exception types and status codes to error codes.
    """
    exc_class_name = exc.__class__.__name__
    
    code_mapping = {
        'NotFound': 'NOT_FOUND',
        'PermissionDenied': 'PERMISSION_DENIED',
        'AuthenticationFailed': 'AUTHENTICATION_FAILED',
        'NotAuthenticated': 'NOT_AUTHENTICATED',
        'ValidationError': 'VALIDATION_ERROR',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'Throttled': 'RATE_LIMITED',
        'ParseError': 'INVALID_REQUEST',
    }
    
    # Try to find mapping for exception class
    if exc_class_name in code_mapping:
        return code_mapping[exc_class_name]
    
    # Map by status code
    status_code_mapping = {
        400: 'VALIDATION_ERROR',
        401: 'AUTHENTICATION_FAILED',
        403: 'PERMISSION_DENIED',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        422: 'UNPROCESSABLE_ENTITY',
        429: 'RATE_LIMITED',
        500: 'INTERNAL_SERVER_ERROR',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
    }
    
    return status_code_mapping.get(status_code, 'UNKNOWN_ERROR')


def get_error_message(exc, data):
    """
    Extract user-friendly error message from exception or response data.
    """
    # If data has 'detail' key (DRF's default)
    if isinstance(data, dict) and 'detail' in data:
        detail = data['detail']
        if isinstance(detail, str):
            return detail
        return str(detail)
    
    # If data is a string
    if isinstance(data, str):
        return data
    
    # If data is a list
    if isinstance(data, list) and len(data) > 0:
        return str(data[0])
    
    # Default message based on exception
    exc_class_name = exc.__class__.__name__
    messages = {
        'NotFound': 'The requested resource was not found.',
        'PermissionDenied': 'You do not have permission to perform this action.',
        'AuthenticationFailed': 'Authentication credentials are invalid.',
        'NotAuthenticated': 'Authentication credentials were not provided.',
        'ValidationError': 'Invalid input data provided.',
        'MethodNotAllowed': 'HTTP method not allowed for this resource.',
        'Throttled': 'Request rate limit exceeded. Please try again later.',
        'ParseError': 'Invalid request format.',
    }
    
    return messages.get(exc_class_name, 'An error occurred while processing your request.')


def extract_validation_details(data):
    """
    Extract field-level validation error details from response data.
    
    Converts DRF's nested error format to a flat, readable format.
    """
    details = {}
    
    if isinstance(data, dict):
        for field, errors in data.items():
            if isinstance(errors, dict):
                # Nested errors (e.g., nested serializers)
                details[field] = extract_validation_details(errors)
            elif isinstance(errors, list):
                # List of errors for a field
                details[field] = [
                    str(error) if not isinstance(error, str) else error 
                    for error in errors
                ]
            else:
                details[field] = [str(errors)]
    
    return details


class StandardizedAPIException(Exception):
    """Base class for all standardized API exceptions."""
    
    def __init__(self, message=None, code=None, status_code=None, details=None):
        self.message = message or 'An error occurred'
        self.code = code or 'API_ERROR'
        self.status_code = status_code or status.HTTP_400_BAD_REQUEST
        self.details = details or {}
        
        super().__init__(self.message)


class ValidationError(StandardizedAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, message=None, details=None):
        super().__init__(
            message=message or 'Validation failed',
            code='VALIDATION_ERROR',
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )


class ResourceNotFound(StandardizedAPIException):
    """Raised when requested resource is not found."""
    
    def __init__(self, resource_type=None):
        message = f'{resource_type} not found' if resource_type else 'Resource not found'
        super().__init__(
            message=message,
            code='NOT_FOUND',
            status_code=status.HTTP_404_NOT_FOUND
        )


class PermissionError(StandardizedAPIException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message=None):
        super().__init__(
            message=message or 'You do not have permission to perform this action',
            code='PERMISSION_DENIED',
            status_code=status.HTTP_403_FORBIDDEN
        )


class RateLimitExceeded(StandardizedAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after=None):
        super().__init__(
            message='Request rate limit exceeded',
            code='RATE_LIMITED',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.retry_after = retry_after
