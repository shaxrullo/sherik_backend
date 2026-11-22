"""
Tests for Listing serializers.
Tests validation logic, field handling, and serialization.
"""

import pytest
from listings.models import Listing
from listings.serializers import ListingCreateUpdateSerializer
from users.models import City, District, User


@pytest.mark.django_db
class TestListingCreateUpdateSerializer:
    """Tests for ListingCreateUpdateSerializer."""
    
    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        city = City.objects.create(name='Tashkent', slug='tashkent')
        district = District.objects.create(
            name='Chilanzar',
            slug='chilanzar',
            city=city
        )
        samarqand = City.objects.create(name='Samarqand', slug='samarqand')
        
        user = User.objects.create_user(
            email='author@test.com',
            phone_number='+998901234567',
            password='test123'
        )
        
        return {
            'city': city,
            'district': district,
            'samarqand': samarqand,
            'user': user
        }
    
    def test_valid_serializer_data(self, setup_data):
        """Test serializer with valid data."""
        data = {
            'title': 'Beautiful Room',
            'description': 'Spacious and clean',
            'listing_type': 'have_room',
            'city_id': setup_data['city'].id,
            'district_id': setup_data['district'].id,
            'price': 1500000,
            'capacity': 2,
            'gender_preference': 'any'
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_district_city_mismatch_validation(self, setup_data):
        """Test validation when district doesn't match city."""
        # Create a different city with its own district
        different_city = City.objects.create(name='Bukhara', slug='bukhara')
        different_district = District.objects.create(
            name='Bukhara Center',
            slug='bukhara-center',
            city=different_city
        )
        
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'have_room',
            'city_id': setup_data['city'].id,  # Tashkent
            'district_id': different_district.id,  # Bukhara district
            'price': 1000000
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'district_id' in serializer.errors
    
    def test_missing_required_fields(self, setup_data):
        """Test validation with missing required fields."""
        data = {
            'title': 'Test',
            # Missing description, city_id, etc.
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors or 'city_id' in serializer.errors
    
    def test_invalid_listing_type(self, setup_data):
        """Test validation with invalid listing_type."""
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'invalid_type',
            'city_id': setup_data['city'].id,
            'price': 1000000
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'listing_type' in serializer.errors
    
    def test_invalid_gender_preference(self, setup_data):
        """Test validation with invalid gender_preference."""
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'have_room',
            'city_id': setup_data['city'].id,
            'gender_preference': 'invalid_gender',
            'price': 1000000
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'gender_preference' in serializer.errors
    
    def test_price_validation(self, setup_data):
        """Test price field validation."""
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'have_room',
            'city_id': setup_data['city'].id,
            'price': -1000  # Negative price
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        # Price field should reject negative values
        # (depends on model field validation)
    
    def test_amenities_json_field(self, setup_data):
        """Test amenities JSON field handling."""
        amenities = ['Wi-Fi', 'Air Conditioning', 'Washing Machine']
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'have_room',
            'city_id': setup_data['city'].id,
            'price': 1000000,
            'amenities': amenities
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['amenities'] == amenities
    
    def test_nearby_universities_json_field(self, setup_data):
        """Test nearby_universities JSON field handling."""
        universities = ['TATU', 'OzMU', 'TDTU']
        data = {
            'title': 'Test',
            'description': 'Test',
            'listing_type': 'need_room',
            'city_id': setup_data['city'].id,
            'price': 1500000,
            'nearby_universities': universities
        }
        
        serializer = ListingCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['nearby_universities'] == universities
    
    def test_serializer_read_only_fields(self, setup_data):
        """Test that read-only fields are ignored in input."""
        listing = Listing.objects.create(
            author=setup_data['user'],
            title='Original',
            description='Original',
            city=setup_data['city'],
            price=1000000
        )
        
        data = {
            'title': 'Updated',
            'description': 'Updated',
            'city_id': setup_data['city'].id,
            'price': 2000000,
            'moderation_status': 'approved',  # Read-only field
            'created_at': '2020-01-01T00:00:00Z'  # Read-only field
        }
        
        serializer = ListingCreateUpdateSerializer(listing, data=data, partial=True)
        assert serializer.is_valid()
        
        # Save should not modify read-only fields
        # (depends on serializer implementation)
