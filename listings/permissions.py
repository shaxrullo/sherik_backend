from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Faqat e'lon muallifiga tahrirlash (PUT, PATCH) va o'chirish (DELETE) huquqini beradi.
    Boshqalar faqat o'qiy oladi (GET, HEAD, OPTIONS).
    """

    def has_object_permission(self, request, view, obj):
        # O'qish so'rovlari (GET, HEAD, OPTIONS) hammaga ruxsat
        if request.method in permissions.SAFE_METHODS:
            return True

        # Tahrirlash/o'chirish faqat muallifga yoki superuser/staff ga ruxsat
        if getattr(request.user, 'is_staff', False):
            return True

        # Agar obyekt ListingPhoto bo'lsa, uning listing.author'i tekshiriladi
        if hasattr(obj, 'listing'):
            return obj.listing.author == request.user

        return obj.author == request.user

