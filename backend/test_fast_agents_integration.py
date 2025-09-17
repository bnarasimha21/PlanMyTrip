#!/usr/bin/env python3
"""
Integration test for fast_agents.py structured output validation
Tests actual functions with mock SERP data to avoid import errors
"""

import os
import sys
import json
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Mock the SERP utilities to avoid import errors
sys.modules['serp_utils'] = MagicMock()

# Mock functions
def mock_search_travel_info(query, city):
    return f"Mock travel info for {query} in {city}"

def mock_search_places(query, city, limit):
    return [{"name": f"Mock Place {i}", "address": f"Address {i}", "rating": 4.5} for i in range(limit)]

def mock_search_restaurants(city, query, limit):
    return [{"name": f"Restaurant {i}", "address": f"Food Street {i}", "rating": 4.0} for i in range(limit)]

def mock_search_attractions(city, query, limit):
    return [{"name": f"Attraction {i}", "address": f"Tourist Area {i}", "rating": 4.5} for i in range(limit)]

def mock_search_activities(city, query, limit):
    return [{"name": f"Activity {i}", "address": f"Activity Zone {i}", "rating": 4.2} for i in range(limit)]

# Set up mocks
sys.modules['serp_utils'].search_travel_info = mock_search_travel_info
sys.modules['serp_utils'].search_places = mock_search_places
sys.modules['serp_utils'].search_restaurants = mock_search_restaurants
sys.modules['serp_utils'].search_attractions = mock_search_attractions
sys.modules['serp_utils'].search_activities = mock_search_activities

# Now import the actual functions
from fast_agents import (
    fast_get_itinerary,
    classify_user_intent,
    fast_handle_question,
    fast_handle_modification,
    fast_extract_trip_request
)

def test_fast_get_itinerary_validation():
    """Test fast_get_itinerary with structured output validation"""

    print("🧪 Testing fast_get_itinerary structured output...")

    test_cases = [
        {"city": "Paris", "interests": "art, food", "days": 2},
        {"city": "Tokyo", "interests": "culture, technology", "days": 3},
        {"city": "Mumbai", "interests": "food, markets", "days": 1}
    ]

    results = []

    for case in test_cases:
        print(f"\n  📍 Testing: {case['city']} - {case['interests']} - {case['days']} days")

        try:
            result = fast_get_itinerary(case["city"], case["interests"], case["days"])

            # Validate structure
            validation_result = {
                "test_case": case,
                "success": True,
                "has_required_keys": all(key in result for key in ["city", "interests", "days", "places"]),
                "places_count": len(result.get("places", [])),
                "places_valid": True,
                "errors": []
            }

            # Validate places structure
            places = result.get("places", [])
            for i, place in enumerate(places):
                if not isinstance(place, dict):
                    validation_result["places_valid"] = False
                    validation_result["errors"].append(f"Place {i} is not a dict")
                    continue

                required_place_fields = ["name", "category", "notes"]
                for field in required_place_fields:
                    if field not in place or not place[field]:
                        validation_result["places_valid"] = False
                        validation_result["errors"].append(f"Place {i} missing {field}")

            # Check data types
            if not isinstance(result.get("city"), str):
                validation_result["errors"].append("City is not a string")
            if not isinstance(result.get("interests"), str):
                validation_result["errors"].append("Interests is not a string")
            if not isinstance(result.get("days"), int):
                validation_result["errors"].append("Days is not an integer")
            if not isinstance(result.get("places"), list):
                validation_result["errors"].append("Places is not a list")

            results.append(validation_result)

            # Print results
            status = "✅" if validation_result["success"] and validation_result["places_valid"] else "❌"
            print(f"    {status} Structure: {'Valid' if validation_result['has_required_keys'] else 'Invalid'}")
            print(f"    📊 Places: {validation_result['places_count']}")
            print(f"    🔍 Places Valid: {'Yes' if validation_result['places_valid'] else 'No'}")

            if validation_result["errors"]:
                print(f"    ⚠️ Errors: {'; '.join(validation_result['errors'])}")

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            results.append({
                "test_case": case,
                "success": False,
                "error": str(e)
            })

    return results

def test_classify_user_intent_validation():
    """Test classify_user_intent with structured output validation"""

    print("\n🧪 Testing classify_user_intent structured output...")

    test_cases = [
        {"input": "can I get a scooter rental in hanoi", "expected": "question"},
        {"input": "add a restaurant to my itinerary", "expected": "modification"},
        {"input": "where can I find good street food", "expected": "question"},
        {"input": "remove the museum from the list", "expected": "modification"},
        {"input": "what's the best time to visit", "expected": "question"}
    ]

    results = []

    for case in test_cases:
        print(f"\n  🗣️ Testing: '{case['input']}'")

        try:
            result = classify_user_intent(case["input"])

            validation_result = {
                "test_case": case,
                "result": result,
                "valid_response": result in ["question", "modification"],
                "matches_expected": result == case["expected"],
                "success": True
            }

            results.append(validation_result)

            status = "✅" if validation_result["valid_response"] else "❌"
            expected_status = "✅" if validation_result["matches_expected"] else "⚠️"

            print(f"    {status} Result: {result}")
            print(f"    {expected_status} Expected: {case['expected']}")

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            results.append({
                "test_case": case,
                "success": False,
                "error": str(e)
            })

    return results

def test_fast_extract_trip_request_validation():
    """Test fast_extract_trip_request with structured output validation"""

    print("\n🧪 Testing fast_extract_trip_request structured output...")

    test_cases = [
        {
            "input": "Plan a 3-day art and food tour in Paris",
            "expected": {"city": "Paris", "interests": "art, food", "days": 3}
        },
        {
            "input": "I want to visit Tokyo for 5 days focusing on culture and technology",
            "expected": {"city": "Tokyo", "interests": "culture, technology", "days": 5}
        },
        {
            "input": "2-day trip to Mumbai for street food and markets",
            "expected": {"city": "Mumbai", "interests": "street food, markets", "days": 2}
        }
    ]

    results = []

    for case in test_cases:
        print(f"\n  📝 Testing: '{case['input']}'")

        try:
            result = fast_extract_trip_request(case["input"])

            validation_result = {
                "test_case": case,
                "result": result,
                "has_required_keys": all(key in result for key in ["city", "interests", "days"]),
                "correct_types": (
                    isinstance(result.get("city"), str) and
                    isinstance(result.get("interests"), str) and
                    isinstance(result.get("days"), int)
                ),
                "success": True
            }

            results.append(validation_result)

            status = "✅" if validation_result["has_required_keys"] and validation_result["correct_types"] else "❌"

            print(f"    {status} Structure: {'Valid' if validation_result['has_required_keys'] else 'Invalid'}")
            print(f"    🏷️ Types: {'Correct' if validation_result['correct_types'] else 'Incorrect'}")
            print(f"    📊 Result: {result}")

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            results.append({
                "test_case": case,
                "success": False,
                "error": str(e)
            })

    return results

def test_fast_handle_question_validation():
    """Test fast_handle_question with structured output validation"""

    print("\n🧪 Testing fast_handle_question structured output...")

    test_cases = [
        {
            "city": "Paris",
            "interests": "art, food",
            "days": 3,
            "question": "What's the best time to visit the Louvre?"
        },
        {
            "city": "Tokyo",
            "interests": "culture",
            "days": 2,
            "question": "How do I get around the city?"
        }
    ]

    results = []

    for case in test_cases:
        print(f"\n  ❓ Testing: '{case['question']}'")

        try:
            result = fast_handle_question(
                case["city"],
                case["interests"],
                case["days"],
                case["question"]
            )

            validation_result = {
                "test_case": case,
                "result": result,
                "has_required_keys": all(key in result for key in ["type", "response"]),
                "correct_type": result.get("type") == "answer",
                "has_response": bool(result.get("response", "").strip()),
                "success": True
            }

            results.append(validation_result)

            status = "✅" if all([
                validation_result["has_required_keys"],
                validation_result["correct_type"],
                validation_result["has_response"]
            ]) else "❌"

            print(f"    {status} Structure: {'Valid' if validation_result['has_required_keys'] else 'Invalid'}")
            print(f"    📝 Response: '{result.get('response', '')[:50]}...'")

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            results.append({
                "test_case": case,
                "success": False,
                "error": str(e)
            })

    return results

def analyze_overall_results(all_results):
    """Analyze overall test results"""

    print(f"\n🎯 OVERALL VALIDATION RESULTS")
    print("=" * 40)

    total_tests = 0
    successful_tests = 0

    for function_name, results in all_results.items():
        function_success = sum(1 for r in results if r.get("success", False))
        total_function_tests = len(results)

        total_tests += total_function_tests
        successful_tests += function_success

        success_rate = (function_success / total_function_tests * 100) if total_function_tests > 0 else 0

        print(f"{function_name}: {function_success}/{total_function_tests} ({success_rate:.1f}%)")

    overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\nOVERALL: {successful_tests}/{total_tests} ({overall_success_rate:.1f}%)")

    return {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "success_rate": overall_success_rate
    }

if __name__ == "__main__":
    print("🚀 STARTING FAST_AGENTS.PY INTEGRATION TESTS")
    print("=" * 50)

    all_results = {}

    # Run all tests
    all_results["fast_get_itinerary"] = test_fast_get_itinerary_validation()
    all_results["classify_user_intent"] = test_classify_user_intent_validation()
    all_results["fast_extract_trip_request"] = test_fast_extract_trip_request_validation()
    all_results["fast_handle_question"] = test_fast_handle_question_validation()

    # Analyze results
    summary = analyze_overall_results(all_results)

    print(f"\n✅ Integration tests completed!")
    print(f"🎉 Success Rate: {summary['success_rate']:.1f}%")