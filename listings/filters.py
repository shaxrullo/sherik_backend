import django_filters
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    """E'lonlarni filtrlash uchun filterset."""

    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label="Minimal narx")
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label="Maksimal narx")
    city = django_filters.NumberFilter(field_name='city__id', label="Shahar ID")
    city_slug = django_filters.CharFilter(field_name='city__slug', lookup_expr='iexact', label="Shahar slugi")
    district = django_filters.NumberFilter(field_name='district__id', label="Tuman ID")
    listing_type = django_filters.ChoiceFilter(choices=Listing.ListingType.choices, label="E'lon turi")
    gender_preference = django_filters.ChoiceFilter(choices=Listing.GenderPreference.choices, label="Jins talabi")
    min_capacity = django_filters.NumberFilter(field_name='capacity', lookup_expr='gte', label="Minimal joylar soni")

    class Meta:
        model = Listing
        fields = [
            'city',
            'city_slug',
            'district',
            'listing_type',
            'gender_preference',
            'min_price',
            'max_price',
            'min_capacity',
        ]

