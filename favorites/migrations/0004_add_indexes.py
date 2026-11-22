# Generated migration for favorites database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('favorites', '0003_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['user_id'], name='favorite_user_idx'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['listing_id'], name='favorite_listing_idx'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['created_at'], name='favorite_created_idx'),
        ),
    ]
