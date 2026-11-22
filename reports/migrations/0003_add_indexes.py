# Generated migration for reports database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['created_at'], name='report_created_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['status'], name='report_status_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['reporter_id'], name='report_reporter_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['reported_listing_id'], name='report_listing_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['reported_user_id'], name='report_user_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['reviewed_by_id'], name='report_reviewer_idx'),
        ),
        # Composite index for filtering
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['status', 'created_at'], name='report_status_created_idx'),
        ),
    ]
