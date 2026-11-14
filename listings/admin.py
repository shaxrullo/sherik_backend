from django.contrib import admin
from django.utils import timezone
from .models import Listing, ListingPhoto
from users.services import log_admin_action


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 1
    fields = ['image', 'is_main', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'author',
        'city',
        'district',
        'price',
        'listing_type',
        'status',
        'moderation_status',
        'created_at',
    ]
    list_filter = [
        'moderation_status',
        'status',
        'city',
        'listing_type',
        'gender_preference',
        'created_at',
    ]
    search_fields = [
        'title',
        'description',
        'author__email',
        'author__first_name',
        'author__phone_number',
    ]
    list_select_related = ['author', 'city', 'district', 'moderated_by']
    inlines = [ListingPhotoInline]
    actions = ['approve_listings', 'reject_listings', 'hide_listings']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': (
                'author',
                'title',
                'listing_type',
                'description',
                'city',
                'district',
                'address_line',
                'price',
                'capacity',
                'gender_preference',
                'status',
            )
        }),
        ('Moderatsiya', {
            'fields': (
                'moderation_status',
                'rejection_reason',
                'moderated_by',
                'moderated_at',
            )
        }),
        ('Sanalar', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'moderated_at')

    @admin.action(description="Tanlangan e'lonlarni tasdiqlash (Approved)")
    def approve_listings(self, request, queryset):
        now = timezone.now()
        count = queryset.update(
            moderation_status=Listing.ModerationStatus.APPROVED,
            moderated_by=request.user,
            moderated_at=now,
            rejection_reason="",
        )
        for listing in queryset:
            log_admin_action(request, "APPROVE_LISTING", listing, "E'lon moderator tomonidan tasdiqlandi")
        self.message_user(request, f"{count} ta e'lon muvaffaqiyatli tasdiqlandi.")

    @admin.action(description="Tanlangan e'lonlarni rad etish (Reject)")
    def reject_listings(self, request, queryset):
        now = timezone.now()
        count = queryset.update(
            moderation_status=Listing.ModerationStatus.REJECTED,
            rejection_reason="E'lon qoidalariga yoki talablariga mos kelmadi.",
            moderated_by=request.user,
            moderated_at=now,
        )
        for listing in queryset:
            log_admin_action(request, "REJECT_LISTING", listing, "E'lon rad etildi")
        self.message_user(request, f"{count} ta e'lon rad etildi.")

    @admin.action(description="Tanlangan e'lonlarni yashirish (Yopish)")
    def hide_listings(self, request, queryset):
        count = queryset.update(status=Listing.Status.CLOSED)
        for listing in queryset:
            log_admin_action(request, "HIDE_LISTING", listing, "E'lon yashirildi (yopildi)")
        self.message_user(request, f"{count} ta e'lon yashirildi.")


@admin.register(ListingPhoto)
class ListingPhotoAdmin(admin.ModelAdmin):
    list_display = ['listing', 'is_main', 'uploaded_at']
    list_filter = ['is_main', 'uploaded_at']
    search_fields = ['listing__title']
    list_select_related = ['listing']
