"""
Pytest configuration file for shared fixtures and configuration.
This file is automatically discovered and loaded by pytest.
"""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
import os

# Configure Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user for authentication tests."""
    return User.objects.create_user(
        email='testuser@example.com',
        phone_number='+998901234567',
        password='testpass123',
        is_verified=False
    )


@pytest.fixture
def verified_test_user(db):
    """Create a verified test user."""
    return User.objects.create_user(
        email='verified@example.com',
        phone_number='+998909876543',
        password='testpass123',
        is_verified=True
    )


@pytest.fixture
def admin_user(db):
    """Create an admin/staff user."""
    return User.objects.create_user(
        email='admin@example.com',
        phone_number='+998909090909',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def test_city(db):
    """Create a test city."""
    from users.models import City
    return City.objects.create(
        name='Tashkent',
        slug='tashkent',
        is_active=True
    )


@pytest.fixture
def test_district(db, test_city):
    """Create a test district."""
    from users.models import District
    return District.objects.create(
        name='Chilanzar',
        slug='chilanzar',
        city=test_city,
        is_active=True
    )


@pytest.fixture
def test_listing(db, test_user, test_city):
    """Create a test listing."""
    from listings.models import Listing
    return Listing.objects.create(
        author=test_user,
        title='Test Listing',
        description='Test Description',
        city=test_city,
        price=1000000,
        listing_type='have_room',
        moderation_status=Listing.ModerationStatus.APPROVED
    )


@pytest.fixture
def authenticated_client(client, test_user):
    """Return a client authenticated with test_user."""
    client.force_login(test_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a client authenticated with admin_user."""
    client.force_login(admin_user)
    return client


# Configure test settings
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Customize Django database configuration for tests."""
    with django_db_blocker.unblock():
        pass


# Mark all tests as django tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "django: mark test as a django test"
    )
