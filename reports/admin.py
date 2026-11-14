from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Report
from listings.models import Listing
from users.services import log_admin_action


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'status',
        'reporter',
        'reported_target_link',
        'reason_short',
        'reviewed_by',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'reason',
        'reporter__email',
        'reported_user__email',
        'reported_listing__title',
    ]
    list_select_related = ['reporter', 'reported_listing', 'reported_user', 'reviewed_by']
    actions = ['hide_reported_listing', 'block_reported_user', 'dismiss_reports', 'mark_in_review']

    fieldsets = (
        ('Shikoyat ma\'lumotlari', {
            'fields': (
                'status',
                'reporter',
                'reported_listing',
                'reported_user',
                'reason',
            )
        }),
        ('Moderatsiya xulosasi', {
            'fields': (
                'reviewed_by',
                'moderator_notes',
                'updated_at',
                'created_at',
            )
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def reason_short(self, obj):
        return (obj.reason[:50] + '...') if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = "Sabab"

    def reported_target_link(self, obj):
        """Shikoyat qilingan e'lon yoki foydalanuvchiga to'g'ridan-to'g'ri admin havola."""
        if obj.reported_listing:
            url = reverse('admin:listings_listing_change', args=[obj.reported_listing.id])
            return format_html('<a href="{}" style="color: #2563eb; font-weight: bold;">E\'lon: {}</a>', url, obj.reported_listing.title)
        elif obj.reported_user:
            url = reverse('admin:users_user_change', args=[obj.reported_user.id])
            return format_html('<a href="{}" style="color: #dc2626; font-weight: bold;">User: {}</a>', url, obj.reported_user.email)
        return "-"
    reported_target_link.short_description = "Shikoyat obyekti"

    @admin.action(description="Shikoyat qilingan e'lonni yashirish (Rad etish va hal qilish)")
    def hide_reported_listing(self, request, queryset):
        count = 0
        now = timezone.now()
        for report in queryset:
            if report.reported_listing:
                listing = report.reported_listing
                listing.status = Listing.Status.CLOSED
                listing.moderation_status = Listing.ModerationStatus.REJECTED
                listing.rejection_reason = f"Shikoyat asosida yashirildi: {report.reason}"
                listing.moderated_by = request.user
                listing.moderated_at = now
                listing.save()

                report.status = Report.Status.RESOLVED
                report.reviewed_by = request.user
                report.moderator_notes = "E'lon yashirildi va shikoyat hal qilindi."
                report.save()

                log_admin_action(request, "REPORT_RESOLVE_HIDE_LISTING", listing, f"Shikoyat #{report.id} asosida e'lon yashirildi")
                count += 1
        self.message_user(request, f"{count} ta shikoyat bo'yicha e'lonlar yashirildi va shikoyat hal qilindi.")

    @admin.action(description="Shikoyat qilingan foydalanuvchini bloklash")
    def block_reported_user(self, request, queryset):
        count = 0
        now = timezone.now()
        for report in queryset:
            target_user = report.reported_user or (report.reported_listing.author if report.reported_listing else None)
            if target_user and not target_user.is_superuser:
                target_user.is_active = False
                target_user.blocked_reason = f"Shikoyat asosida bloklandi: {report.reason}"
                target_user.blocked_at = now
                target_user.save()

                report.status = Report.Status.RESOLVED
                report.reviewed_by = request.user
                report.moderator_notes = f"Foydalanuvchi ({target_user.email}) bloklandi."
                report.save()

                log_admin_action(request, "REPORT_RESOLVE_BLOCK_USER", target_user, f"Shikoyat #{report.id} asosida foydalanuvchi bloklandi")
                count += 1
        self.message_user(request, f"{count} ta foydalanuvchi bloklandi va shikoyat hal qilindi.")

    @admin.action(description="Shikoyatni rad etish (Asossiz deb yopish)")
    def dismiss_reports(self, request, queryset):
        count = queryset.update(
            status=Report.Status.DISMISSED,
            reviewed_by=request.user,
            moderator_notes="Shikoyat asossiz deb topildi.",
        )
        for report in queryset:
            log_admin_action(request, "REPORT_DISMISS", report, "Shikoyat asossiz deb rad etildi")
        self.message_user(request, f"{count} ta shikoyat rad etildi.")

    @admin.action(description="Ko'rib chiqilmoqda (In Review) holatiga o'tkazish")
    def mark_in_review(self, request, queryset):
        count = queryset.update(
            status=Report.Status.IN_REVIEW,
            reviewed_by=request.user,
        )
        self.message_user(request, f"{count} ta shikoyat ko'rib chiqishga olindi.")
