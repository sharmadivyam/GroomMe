from .models import WardrobeItem
import random
import requests

def fetch_outfit_images(query, api_key, cse_id, num=4):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "searchType": "image",
        "num": num,
        "safe": "active"
    }

    response = requests.get(url, params=params)
    data = response.json()

    image_urls = []
    for item in data.get("items", []):
        image_urls.append(item["link"])

    return image_urls


def generate_otp():
    return str(random.randint(100000, 999999))


def filter_wardrobe_items(user, preferred_styles, occasion, weather_condition):
    items = WardrobeItem.objects.filter(user=user)
    ranked = []

    weather_to_season = {
        'hot': ['Summer', 'spring'],
        'cold': ['Winter', 'autumn'],
        'rainy': ['Monsoon', 'autumn'],
        'mild': ['Spring', 'autumn'],
        'warm': ['Summer', 'spring']
    }
    seasons = weather_to_season.get(weather_condition.lower(), []) if weather_condition else []

    for item in items:
        score = 0

        # Style match
        if preferred_styles and set(item.style_tags).intersection(preferred_styles):
            score += 1
        
        # Occasion match
        if occasion and occasion.lower() in [o.lower() for o in item.occasion_suitability]:
            score += 1

        # Season match
        if seasons and any(season.lower() in [s.lower() for s in item.season_suitability] for season in seasons):
            score += 1

        ranked.append((score, item))

    # Sort items by score (descending)
    ranked.sort(key=lambda x: x[0], reverse=True)
    filtered_items =[item for score, item in ranked if score > 0]

    if not filtered_items:
        print("No items matched filters. Relaxing criteria and returning all user items.")
        return items  # fallback: return all wardrobe items for user

    return filtered_items
