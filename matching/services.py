from users.models import User, LifestylePreference
from listings.models import Listing


def calculate_match_score(user: User, listing: Listing) -> dict:
    """
    Foydalanuvchi va e'lon o'rtasidagi moslik ballini hisoblash.
    Maksimal ball: 100 ball (100%).

    Mezonlar:
    1. Hudud mosligi (30 ball)
    2. Jins mosligi (25 ball)
    3. Turmush tarzi mosligi (30 ball)
    4. Rol va e'lon turi mosligi (15 ball)
    """
    scores = {
        'location': 0,
        'gender': 0,
        'lifestyle': 0,
        'type': 0,
    }
    details = []

    # 1. Hudud mosligi (Maksimal 30 ball)
    if user.city_id and listing.city_id:
        if user.city_id == listing.city_id:
            scores['location'] += 20
            details.append("Shahar bir xil (+20 ball)")

            if user.district_id and listing.district_id and user.district_id == listing.district_id:
                scores['location'] += 10
                details.append("Tuman ham mos keldi (+10 ball)")
        else:
            details.append("Shahar boshqa (0 ball)")
    else:
        # Shahar ko'rsatilmagan bo'lsa neytral ball
        scores['location'] += 10

    # 2. Jins mosligi (Maksimal 25 ball)
    if listing.gender_preference == Listing.GenderPreference.ANY:
        scores['gender'] = 25
        details.append("Jins bo'yicha talab yo'q (+25 ball)")
    elif user.gender and user.gender == listing.gender_preference:
        scores['gender'] = 25
        details.append(f"Jins mos keldi ({user.get_gender_display()}) (+25 ball)")
    elif not user.gender:
        scores['gender'] = 10
        details.append("Foydalanuvchi jinsi belgilanmagan (+10 ball)")
    else:
        scores['gender'] = 0
        details.append("Jins talabga mos kelmadi (0 ball)")

    # 3. Rol va e'lon turi mosligi (Maksimal 15 ball)
    # Agar user joy qidiruvchi (seeker) bo'lsa va e'londa joy bor (have_room) bo'lsa -> a'lo moslik!
    if user.role == User.Role.SEEKER and listing.listing_type == Listing.ListingType.HAVE_ROOM:
        scores['type'] = 15
        details.append("E'lon turi sizning rolingizga to'liq mos (+15 ball)")
    elif user.role == User.Role.HOST and listing.listing_type == Listing.ListingType.NEED_ROOM:
        scores['type'] = 15
        details.append("Sherik qidiryapsiz va e'lon joy qidiruvchidan (+15 ball)")
    else:
        scores['type'] = 8
        details.append("E'lon turi qisman mos (+8 ball)")

    # 4. Turmush tarzi mosligi (Maksimal 30 ball)
    user_lifestyle = getattr(user, 'lifestyle', None)
    author_lifestyle = getattr(listing.author, 'lifestyle', None)

    if user_lifestyle and author_lifestyle:
        lifestyle_score = 0

        # Chekish (8 ball)
        if user_lifestyle.smoking == author_lifestyle.smoking:
            lifestyle_score += 8
            details.append("Chekishga munosabat bir xil (+8 ball)")
        elif (user_lifestyle.smoking == LifestylePreference.Smoking.NO and
              author_lifestyle.smoking == LifestylePreference.Smoking.YES):
            details.append("Chekish odati mos kelmadi (0 ball)")
        else:
            lifestyle_score += 4
            details.append("Chekishga munosabat moslashuvchan (+4 ball)")

        # Tozalik va tartib (8 ball)
        if user_lifestyle.cleanliness == author_lifestyle.cleanliness:
            lifestyle_score += 8
            details.append("Tozalik va tartibga talab bir xil (+8 ball)")
        else:
            lifestyle_score += 4

        # Uy hayvonlari (7 ball)
        if (user_lifestyle.pets == author_lifestyle.pets or
                user_lifestyle.pets == LifestylePreference.Pets.INDIFFERENT or
                author_lifestyle.pets == LifestylePreference.Pets.INDIFFERENT):
            lifestyle_score += 7
            details.append("Hayvonlarga munosabat mos (+7 ball)")
        else:
            details.append("Hayvonlarga munosabat to'g'ri kelmadi (0 ball)")

        # Uyqu rejimi (4 ball)
        if (user_lifestyle.sleep_schedule == author_lifestyle.sleep_schedule or
                user_lifestyle.sleep_schedule == LifestylePreference.SleepSchedule.FLEXIBLE or
                author_lifestyle.sleep_schedule == LifestylePreference.SleepSchedule.FLEXIBLE):
            lifestyle_score += 4
            details.append("Uyqu rejimi mos (+4 ball)")

        # Mehmonlar (3 ball)
        if user_lifestyle.guests == author_lifestyle.guests:
            lifestyle_score += 3
        else:
            lifestyle_score += 1

        scores['lifestyle'] = min(lifestyle_score, 30)
    else:
        # Turmush tarzi to'ldirilmagan bo'lsa o'rtacha ball
        scores['lifestyle'] = 15
        details.append("Turmush tarzi profili to'liq emas (+15 ball)")

    total_score = sum(scores.values())
    total_score = max(0, min(total_score, 100))

    return {
        'total_score': total_score,
        'breakdown': scores,
        'details': details,
    }

