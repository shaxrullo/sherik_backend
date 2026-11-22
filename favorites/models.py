from django.db import models
from django.conf import settings


class Favorite(models.Model):
    """Foydalanuvchining sevimli e'lonlari modeli."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Foydalanuvchi",
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="E'lon",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Saqlangan sana")

    class Meta:
        verbose_name = "Sevimli e'lon"
        verbose_name_plural = "Sevimli e'lonlar"
        unique_together = ('user', 'listing')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id'], name='favorite_user_idx'),
            models.Index(fields=['listing_id'], name='favorite_listing_idx'),
            models.Index(fields=['created_at'], name='favorite_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.listing.title}"
