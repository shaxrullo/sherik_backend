# Generated migration to delete test listings from production database

from django.db import migrations


def delete_test_listings(apps, schema_editor):
    Listing = apps.get_model('listings', 'Listing')
    # Delete test listings created during development
    deleted_count, _ = Listing.objects.filter(
        title__in=['Test title min length', 'T', 'Test Listing from script']
    ).delete()
    print(f"Deleted {deleted_count} test listings.")


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0008_alter_listing_moderation_status'),
    ]

    operations = [
        migrations.RunPython(delete_test_listings, migrations.RunPython.noop),
    ]

