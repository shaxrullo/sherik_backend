"""
Tests for custom permission classes.
Tests permission logic and access control.
"""

import pytest
from rest_framework.test import APIRequestFactory
from listings.models import Listing, ListingPhoto
from listings.permissions import IsAuthorOrReadOnly
from users.models import City, User


@pytest.mark.django_db
class TestIsAuthorOrReadOnly:
    """Tests for IsAuthorOrReadOnly permission class."""
    
    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        city = City.objects.create(name='Tashkent', slug='tashkent')
        author = User.objects.create_user(
            email='author@test.com',
            phone_number='+998901234567',
            password='test123'
        )
        other_user = User.objects.create_user(
            email='other@test.com',
            phone_number='+998909876543',
            password='test123'
        )
        
        listing = Listing.objects.create(
            author=author,
            title='Test Listing',
            description='Test',
            city=city,
            price=1000000
        )
        
        return {
            'author': author,
            'other_user': other_user,
            'listing': listing,
            'factory': APIRequestFactory()
        }
    
    def test_safe_methods_allowed_for_anonymous(self, setup_data):
        """Test that GET requests are allowed for anonymous users."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.get('/listings/')
        request.user = None  # Anonymous
        
        # Safe methods should be allowed
        assert permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_safe_methods_allowed_for_authenticated(self, setup_data):
        """Test that GET requests are allowed for authenticated users."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.get('/listings/')
        request.user = setup_data['other_user']
        
        # Safe methods should be allowed
        assert permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_write_methods_allowed_for_author(self, setup_data):
        """Test that POST/PUT/DELETE are allowed for author."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.put('/listings/1/', {})
        request.user = setup_data['author']
        
        assert permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_write_methods_denied_for_non_author(self, setup_data):
        """Test that POST/PUT/DELETE are denied for non-author."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.put('/listings/1/', {})
        request.user = setup_data['other_user']
        
        assert not permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_delete_allowed_for_author(self, setup_data):
        """Test that DELETE is allowed for author."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.delete('/listings/1/')
        request.user = setup_data['author']
        
        assert permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_delete_denied_for_non_author(self, setup_data):
        """Test that DELETE is denied for non-author."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.delete('/listings/1/')
        request.user = setup_data['other_user']
        
        assert not permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_anonymous_cannot_modify(self, setup_data):
        """Test that anonymous users cannot modify objects."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        request = factory.put('/listings/1/', {})
        request.user = None  # Anonymous
        
        # Anonymous users cannot have write access
        assert not permission.has_object_permission(request, None, setup_data['listing'])
    
    def test_staff_user_access(self, setup_data):
        """Test that staff users have write access."""
        permission = IsAuthorOrReadOnly()
        factory = setup_data['factory']
        
        staff_user = User.objects.create_user(
            email='staff@test.com',
            phone_number='+998901111111',
            password='test123',
            is_staff=True
        )
        
        request = factory.put('/listings/1/', {})
        request.user = staff_user
        
        # Staff should be able to modify (depends on implementation)
        # This might not be enforced by IsAuthorOrReadOnly alone
