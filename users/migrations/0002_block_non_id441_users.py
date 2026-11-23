from django.db import migrations


def block_non_id441_users(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        username = (getattr(user, 'telegram_username', '') or '').strip().lstrip('@').lower()
        if username == 'id_441':
            user.is_active = True
            user.save(update_fields=['is_active'])
        else:
            user.is_active = False
            user.save(update_fields=['is_active'])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(block_non_id441_users, reverse_func),
    ]
