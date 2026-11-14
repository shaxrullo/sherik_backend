from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """E'lonlar ro'yxati uchun sahifalash klassi."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

