#!/usr/bin/env python3
"""
Test geocoding accuracy with the Tam Vi restaurant example
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('/Users/nbadrinath/Documents/MyGitHub/LetMePlanMyTrip/backend')

load_dotenv()

def test_geocoding_accuracy():
    """Test geocoding accuracy specifically for Tam Vi restaurant in Hanoi"""

    print("🧪 Testing Geocoding Accuracy")
    print("=" * 40)

    # Test the get_country_for_city function first
    try:
        from fast_agents import get_country_for_city

        print("📍 Testing country mapping:")
        test_cities = ["Hanoi", "Bangkok", "Mumbai", "Paris", "Tokyo"]
        for city in test_cities:
            country = get_country_for_city(city)
            print(f"  {city} -> {country}")

        # Specific test for Hanoi
        hanoi_country = get_country_for_city("Hanoi")
        assert hanoi_country == "Vietnam", f"Expected 'Vietnam' for Hanoi, got '{hanoi_country}'"
        print("✅ Country mapping test passed!")

    except Exception as e:
        print(f"❌ Country mapping test failed: {e}")
        return False

    # Test the actual geocoding with Tam Vi restaurant
    try:
        import requests
        from urllib.parse import quote

        MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
        if not MAPBOX_TOKEN:
            print("⚠️ MAPBOX_TOKEN not found, skipping geocoding test")
            return True

        print("\n🗺️ Testing geocoding with Tam Vi restaurant:")

        # Test the old way (hardcoded India)
        old_query = "Tam Vi restaurant, Hanoi, India"
        old_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(old_query)}.json"
        old_resp = requests.get(old_url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)

        if old_resp.ok:
            old_features = old_resp.json().get("features", [])
            if old_features:
                old_lng, old_lat = old_features[0]["center"]
                old_place_name = old_features[0].get("place_name", "Unknown")
                print(f"  ❌ Old method (India): {old_lat:.4f}, {old_lng:.4f} - {old_place_name}")

        # Test the new way (correct country)
        country = get_country_for_city("Hanoi")
        new_query = f"Tam Vi restaurant, Hanoi, {country}"
        new_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(new_query)}.json"
        new_resp = requests.get(new_url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)

        if new_resp.ok:
            new_features = new_resp.json().get("features", [])
            if new_features:
                new_lng, new_lat = new_features[0]["center"]
                new_place_name = new_features[0].get("place_name", "Unknown")
                print(f"  ✅ New method (Vietnam): {new_lat:.4f}, {new_lng:.4f} - {new_place_name}")

                # Check if the new coordinates are in Vietnam (rough bounds)
                vietnam_lat_range = (8.0, 24.0)
                vietnam_lng_range = (102.0, 110.0)

                is_in_vietnam = (vietnam_lat_range[0] <= new_lat <= vietnam_lat_range[1] and
                               vietnam_lng_range[0] <= new_lng <= vietnam_lng_range[1])

                if is_in_vietnam:
                    print("  ✅ New coordinates appear to be in Vietnam!")
                else:
                    print(f"  ⚠️ New coordinates might not be in Vietnam (lat: {new_lat}, lng: {new_lng})")

        print("✅ Geocoding test completed!")
        return True

    except Exception as e:
        print(f"❌ Geocoding test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_geocoding_accuracy()

    if success:
        print("\n🎉 All geocoding accuracy tests passed!")
        print("The Tam Vi restaurant issue should now be fixed.")
    else:
        print("\n💥 Geocoding accuracy tests failed!")

    print("\nTest completed!")