"""
Unit tests for Listing models.
Tests model methods, properties, and business logic.
"""

import pytest
from django.utils import timezone
from listings.models import Listing, ListingPhoto
from users.models import City, District, User
from decimal import Decimal


@pytest.mark.django_db
class TestListingModel:
    """Tests for Listing model."""
    
    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        city = City.objects.create(name='Tashkent', slug='tashkent')
        user = User.objects.create_user(
            email='author@test.com',
            phone_number='+998901234567',
            password='test123'
        )
        return {'city': city, 'user': user}
    
    def test_listing_creation(self, setup_data):
        """Test basic listing creation."""
        listing = Listing.objects.create(
            author=setup_data['user'],
            title='Test Listing',
            description='Test Description',
            city=setup_data['city'],
            price=1000000,
            listing_type=Listing.ListingType.HAVE_ROOM
        )
        
        assert listing.id is not None
        assert listing.title == 'Test Listing'
        assert listing.author == setup_data['user']
        assert listing.moderation_status == Listing.ModerationStatus.PENDING
        assert listing.status == Listing.Status.ACTIVE
    
    def test_listing_string_representation(self, setup_data):
        """Test __str__ method."""
        listing = Listing.objects.create(
            author=setup_data['user'],
            title='Room Available',
            description='Test',
            city=setup_data['city'],
            price=500000
        )
        
        assert 'Room Available' in str(listing)
        assert 'Tashkent' in str(listing)
    
    def test_unverified_user_listing_pending(self, setup_data):
        """Test that unverified user's listing is pending by default."""
        listing = Listing(
            author=setup_data['user'],
            title='Test',
            description='Test',
            city=setup_data['city'],
            price=1000000
        )
        listing.save()
        
        assert listing.moderation_status == Listing.ModerationStatus.PENDING
    
    def test_verified_user_listing_auto_approved(self, setup_data):
        """Test that verified user's listing is auto-approved."""
        user = setup_data['user']
        user.is_verified = True
        user.save()
        
        listing = Listing(
            author=user,
            title='Verified User Listing',
            description='Test',
            city=setup_data['city'],
            price=1000000
        )
        listing.save()
        
        assert listing.moderation_status == Listing.ModerationStatus.APPROVED
        assert listing.moderated_at is not None
    
    def test_staff_user_listing_auto_approved(self, setup_data):
        """Test that staff user's listing is auto-approved."""
        user = setup_data['user']
        user.is_staff = True
        user.save()
        
        listing = Listing(
            author=user,
            title='Staff Listing',
            description='Test',
            city=setup_data['city'],
            price=1000000
        )
        listing.save()
        
        assert listing.moderation_status == Listing.ModerationStatus.APPROVED
    
    def test_listing_meta_ordering(self, setup_data):
        """Test that listings are ordered by created_at descending."""
        listing1 = Listing.objects.create(
            author=setup_data['user'],
            title='First',
            description='Test',
            city=setup_data['city'],
            price=1000000
        )
        listing2 = Listing.objects.create(
            author=setup_data['user'],
            title='Second',
            description='Test',
            city=setup_data['city'],
            price=1000000
        )
        
        listings = Listing.objects.all()
        assert listings[0].id == listing2.id  # Newest first
        assert listings[1].id == listing1.id
    
    def test_listing_price_decimal_field(self, setup_data):
        """Test that price field stores decimal correctly."""
        listing = Listing.objects.create(
            author=setup_data['user'],
            title='Test',
            description='Test',
            city=setup_data['city'],
            price=Decimal('1500000.50')
        )
        
        # Reload from database
        listing.refresh_from_db()
        assert isinstance(listing.price, Decimal)
        assert listing.price == Decimal('1500000')  # Decimal places = 0


@pytest.mark.django_db
class TestListingPhotoModel:
    """Tests for ListingPhoto model."""
    
    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        city = City.objects.create(name='Tashkent', slug='tashkent')
        user = User.objects.create_user(
            email='author@test.com',
            phone_number='+998901234567',
            password='test123'
        )
        listing = Listing.objects.create(
            author=user,
            title='Test Listing',
            description='Test',
            city=city,
            price=1000000
        )
        return {'listing': listing, 'user': user}
    
    def test_listing_photo_creation(self, setup_data):
        """Test basic photo creation."""
        photo = ListingPhoto.objects.create(
            listing=setup_data['listing'],
            image='test/image.jpg',
            is_main=True
        )
        
        assert photo.id is not None
        assert photo.listing == setup_data['listing']
        assert photo.is_main is True
        assert photo.uploaded_at is not None
    
    def test_listing_photo_string_representation(self, setup_data):
        """Test __str__ method."""
        photo = ListingPhoto.objects.create(
            listing=setup_data['listing'],
            image='test/image.jpg'
        )
        
        assert 'Test Listing' in str(photo)
        assert 'rasmi' in str(photo)  # Uzbek for "photo"
    
    def test_listing_photo_ordering(self, setup_data):
        """Test that photos are ordered by is_main descending, then id."""
        photo1 = ListingPhoto.objects.create(
            listing=setup_data['listing'],
            image='test/1.jpg',
            is_main=False
        )
        photo2 = ListingPhoto.objects.create(
            listing=setup_data['listing'],
            image='test/2.jpg',
            is_main=True
        )
        
        photos = ListingPhoto.objects.all()
        assert photos[0].id == photo2.id  # Main photo first
        assert photos[1].id == photo1.id


@pytest.mark.django_db
class TestListingChoices:
    """Tests for Listing model choices/enums."""
    
    def test_listing_type_choices(self):
        """Test ListingType choices."""
        choices = Listing.ListingType.choices
        assert ('have_room', "Joy bor (Sherik kerak)") in choices
        assert ('need_room', "Joy kerak (Ijara qidiryapti)") in choices
    
    def test_gender_preference_choices(self):
        """Test GenderPreference choices."""
        choices = Listing.GenderPreference.choices
        assert ('male', "Faqat erkaklar / yigitlar") in choices
        assert ('female', "Faqat ayollar / qizlar") in choices
        assert ('any', "Farqi yo'q") in choices
    
    def test_status_choices(self):
        """Test Status choices."""
        choices = Listing.Status.choices
        assert ('active', "Faol") in choices
        assert ('closed', "Yopilgan") in choices
    
    def test_moderation_status_choices(self):
        """Test ModerationStatus choices."""
        choices = Listing.ModerationStatus.choices
        assert ('pending', "Kutilmoqda") in choices
        assert ('approved', "Tasdiqlangan") in choices
        assert ('rejected', "Rad etilgan") in choices
    
    def test_currency_choices(self):
        """Test Currency choices."""
        choices = Listing.Currency.choices
        assert ('USD', "USD ($)") in choices
        assert ('UZS', "UZS (so'm)") in choices
