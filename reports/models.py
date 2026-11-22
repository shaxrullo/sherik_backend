from django.db import models
from django.conf import settings


class Report(models.Model):
    """E'lon yoki foydalanuvchi ustidan shikoyat modeli."""

    class Status(models.TextChoices):
        NEW = 'new', "Yangi"
        IN_REVIEW = 'in_review', "Ko'rib chiqilmoqda"
        RESOLVED = 'resolved', "Hal qilindi (chora ko'rildi)"
        DISMISSED = 'dismissed', "Rad etildi (asossiz)"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        verbose_name="Shikoyat qiluvchi",
    )
    reported_listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Shikoyat qilingan e'lon",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_reports',
        verbose_name="Shikoyat qilingan foydalanuvchi",
    )
    reason = models.TextField(
        verbose_name="Shikoyat sababi va tafsilotlari",
        help_text="Soxta e'lon, haqoratli muomala, firibgarlik va h.k.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Shikoyat holati",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        verbose_name="Ko'rib chiqqan moderator",
    )
    moderator_notes = models.TextField(
        blank=True,
        verbose_name="Moderator xulosasi / izohi",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        verbose_name = "Shikoyat"
        verbose_name_plural = "Shikoyatlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='report_created_idx'),
            models.Index(fields=['status'], name='report_status_idx'),
            models.Index(fields=['reporter_id'], name='report_reporter_idx'),
            models.Index(fields=['reported_listing_id'], name='report_listing_idx'),
            models.Index(fields=['reported_user_id'], name='report_user_idx'),
            models.Index(fields=['reviewed_by_id'], name='report_reviewer_idx'),
            models.Index(fields=['status', 'created_at'], name='report_status_created_idx'),
        ]

    def __str__(self):
        target = f"E'lon #{self.reported_listing_id}" if self.reported_listing_id else f"User #{self.reported_user_id}"
        return f"Shikoyat ({target}) - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Qoida: Bitta e'longa 3 va undan ko'p shikoyat kelsa, e'lon avtomatik pending (qayta ko'rib chiqish) holatiga o'tadi
        if self.reported_listing_id and is_new:
            from listings.models import Listing
            active_reports_count = Report.objects.filter(
                reported_listing_id=self.reported_listing_id,
                status__in=[self.Status.NEW, self.Status.IN_REVIEW]
            ).count()

            if active_reports_count >= 3:
                Listing.objects.filter(
                    id=self.reported_listing_id,
                    moderation_status=Listing.ModerationStatus.APPROVED
                ).update(
                    moderation_status=Listing.ModerationStatus.PENDING
                )
