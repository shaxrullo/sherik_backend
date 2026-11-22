# Generated migration for database performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0006_listing_total_residents'),
    ]

    operations = [
        # Listing model indexes
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['created_at'], name='listings_created_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['status'], name='listings_status_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['moderation_status'], name='listings_mod_status_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['author_id'], name='listings_author_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['city_id'], name='listings_city_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['district_id'], name='listings_district_idx'),
        ),
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['listing_type'], name='listings_type_idx'),
        ),
        # Composite index for filtering
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['status', 'moderation_status'], name='listings_status_mod_idx'),
        ),
        # ListingPhoto indexes
        migrations.AddIndex(
            model_name='listingphoto',
            index=models.Index(fields=['listing_id'], name='photo_listing_idx'),
        ),
        migrations.AddIndex(
            model_name='listingphoto',
            index=models.Index(fields=['is_main'], name='photo_main_idx'),
        ),
    ]
