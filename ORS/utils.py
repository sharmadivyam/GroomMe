from .models import WardrobeItem
import random

def generate_otp():
    return str(random.randint(100000, 999999))


def filter_wardrobe_items(user, preferred_styles, occasion, weather_condition):
    items = WardrobeItem.objects.filter(user=user)

    if preferred_styles:
        items = items.filter(style__overlap=preferred_styles)

    if occasion:
        items = items.filter(occasion__contains=[occasion])

    # Simple weather to season mapping
    weather_to_season = {
        'hot': 'summer',
        'cold': 'winter',
        'rainy': 'monsoon',
    }

    season = weather_to_season.get(weather_condition.lower())
    if season:
        items = items.filter(season__contains=[season])

    return items