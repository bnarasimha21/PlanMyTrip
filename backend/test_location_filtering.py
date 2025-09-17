#!/usr/bin/env python3
"""
Test location filtering to ensure places are in the correct city
"""

import os
import sys
from unittest.mock import MagicMock

# Mock the SERP utilities to avoid import errors
sys.modules['serp_utils'] = MagicMock()

def mock_search_places(query, city, limit):
    return [{"name": f"Place {i} in {city}", "address": f"Address {i}", "rating": 4.5} for i in range(limit)]

def mock_search_restaurants(city, query, limit):
    return [{"name": f"Restaurant {i}", "address": f"Food Street {i}", "rating": 4.0} for i in range(limit)]

def mock_search_attractions(city, query, limit):
    # Simulate mixed results - some correct, some incorrect
    if city.lower() == "hanoi":
        return [
            {"name": "Hoan Kiem Lake", "address": "Hanoi, Vietnam", "rating": 4.8},
            {"name": "Ho Chi Minh Museum", "address": "Ho Chi Minh City, Vietnam", "rating": 4.5},  # Wrong city
            {"name": "Temple of Literature", "address": "Hanoi, Vietnam", "rating": 4.7}
        ]
    return [{"name": f"Attraction {i}", "address": f"Tourist Area {i}", "rating": 4.5} for i in range(limit)]

def mock_search_activities(city, query, limit):
    return [{"name": f"Activity {i}", "address": f"Activity Zone {i}", "rating": 4.2} for i in range(limit)]

# Set up mocks
sys.modules['serp_utils'].search_places = mock_search_places
sys.modules['serp_utils'].search_restaurants = mock_search_restaurants
sys.modules['serp_utils'].search_attractions = mock_search_attractions
sys.modules['serp_utils'].search_activities = mock_search_activities
sys.modules['serp_utils'].search_travel_info = lambda q, c: f"Mock info for {q} in {c}"

# Mock environment variable
os.environ['DIGITALOCEAN_INFERENCE_KEY'] = 'test-key'

def test_location_filtering():
    """Test that the location filtering works correctly"""

    print("🧪 Testing Location Filtering")
    print("=" * 40)

    # Create test data with mixed locations
    test_places = [
        {"name": "Hoan Kiem Lake", "address": "Hanoi, Vietnam", "notes": "Beautiful lake in Hanoi"},
        {"name": "Ho Chi Minh Museum", "address": "Ho Chi Minh City, Vietnam", "notes": "Museum in Saigon"},
        {"name": "Temple of Literature", "address": "Hanoi, Vietnam", "notes": "Historic temple"},
        {"name": "Bangkok Palace", "address": "Bangkok, Thailand", "notes": "Royal palace"},
        {"name": "Hanoi Old Quarter", "address": "Hanoi, Vietnam", "notes": "Historic quarter"}
    ]

    # Test the filtering logic
    city = "Hanoi"
    filtered_places = []
    wrong_city_keywords = ['ho chi minh', 'saigon', 'bangkok', 'kuala lumpur', 'singapore']
    target_city_lower = city.lower()

    for place in test_places:
        place_name = (place.get('name') or '').lower()
        place_address = (place.get('address') or '').lower()
        place_notes = (place.get('notes') or '').lower()

        # Check if place contains wrong city keywords
        contains_wrong_city = any(keyword in place_name or keyword in place_address or keyword in place_notes
                                for keyword in wrong_city_keywords if keyword != target_city_lower)

        if not contains_wrong_city:
            filtered_places.append(place)
            print(f"✅ Kept: {place['name']}")
        else:
            print(f"❌ Filtered out: {place['name']} (contains wrong city keyword)")

    print(f"\nResults:")
    print(f"Original places: {len(test_places)}")
    print(f"Filtered places: {len(filtered_places)}")
    print(f"Removed: {len(test_places) - len(filtered_places)}")

    # Verify results
    expected_kept = ["Hoan Kiem Lake", "Temple of Literature", "Hanoi Old Quarter"]
    expected_removed = ["Ho Chi Minh Museum", "Bangkok Palace"]

    actual_kept = [p['name'] for p in filtered_places]

    success = True
    for name in expected_kept:
        if name not in actual_kept:
            print(f"❌ ERROR: {name} should have been kept but was filtered out")
            success = False

    for name in expected_removed:
        if name in actual_kept:
            print(f"❌ ERROR: {name} should have been filtered out but was kept")
            success = False

    if success:
        print(f"\n✅ Location filtering test PASSED!")
    else:
        print(f"\n❌ Location filtering test FAILED!")

    return success

if __name__ == "__main__":
    test_location_filtering()