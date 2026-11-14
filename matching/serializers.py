from rest_framework import serializers
from listings.serializers import ListingListSerializer


class MatchBreakdownSerializer(serializers.Serializer):
    """Moslik ballarining mezonlar bo'yicha taqsimoti."""
    location = serializers.IntegerField(help_text="Hudud mosligi (maks 30)")
    gender = serializers.IntegerField(help_text="Jins mosligi (maks 25)")
    lifestyle = serializers.IntegerField(help_text="Turmush tarzi mosligi (maks 30)")
    type = serializers.IntegerField(help_text="Rol va e'lon turi mosligi (maks 15)")


class MatchedListingSerializer(serializers.Serializer):
    """Tavsiya etilgan e'lon va uning moslik ko'rsatkichlari."""

    listing = ListingListSerializer(read_only=True)
    match_score = serializers.IntegerField(help_text="Umumiy moslik foizi (0 dan 100 gacha)")
    match_breakdown = MatchBreakdownSerializer(read_only=True)
    match_details = serializers.ListField(
        child=serializers.CharField(),
        help_text="Moslik bo'yicha izohlar va hisoblangan ballar"
    )


class ListingMatchDetailSerializer(serializers.Serializer):
    """Aniq bitta e'lon bilan moslik tahlili."""

    listing_id = serializers.IntegerField()
    listing_title = serializers.CharField()
    match_score = serializers.IntegerField()
    match_breakdown = MatchBreakdownSerializer(read_only=True)
    match_details = serializers.ListField(child=serializers.CharField())

