#!/usr/bin/env python3
"""
Test structured output validation for itinerary generation
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

# Define Pydantic models for structured output validation
class Place(BaseModel):
    name: str = Field(description="Name of the place")
    neighborhood: str = Field(description="Neighborhood or area", default=None)
    category: str = Field(description="Category: food/art/culture/shopping/sightseeing")
    address: str = Field(description="Full address", default=None)
    latitude: float = Field(description="Latitude coordinate", default=None)
    longitude: float = Field(description="Longitude coordinate", default=None)
    notes: str = Field(description="Brief description or notes")

class ItineraryResponse(BaseModel):
    places: List[Place] = Field(description="List of places for the itinerary")

# Initialize Gradient LLM
gradient_llm = ChatGradient(
    model="llama3.3-70b-instruct",
    api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
)

def test_itinerary_structured_output(city: str, interests: str, days: int):
    """Test itinerary generation with structured output validation"""

    prompt = f"""Create a {days}-day travel itinerary for {city} focusing on {interests}.

Requirements:
- Include {max(5, days * 2)} diverse places that match the interests
- Mix of popular attractions and local gems
- Include specific addresses where possible
- Categorize each place appropriately (food, art, culture, shopping, sightseeing)
- Provide helpful notes for each place
- Real places only"""

    # Set up structured output parser
    parser = JsonOutputParser(pydantic_object=ItineraryResponse)

    prompt_template = PromptTemplate(
        template="You are a travel expert. {format_instructions}\n\n{query}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt_template | gradient_llm | parser

    test_results = {
        "city": city,
        "interests": interests,
        "days": days,
        "structured_success": False,
        "validation_success": False,
        "places_count": 0,
        "required_fields_valid": False,
        "category_validation": False,
        "errors": [],
        "places_data": None
    }

    try:
        # Test structured output
        result = chain.invoke({"query": prompt})
        test_results["structured_success"] = True
        test_results["places_data"] = result

        # Validate the response structure
        if isinstance(result, dict) and 'places' in result:
            places = result.get('places', [])
            test_results["places_count"] = len(places)

            # Validate using Pydantic model
            try:
                validated_response = ItineraryResponse(**result)
                test_results["validation_success"] = True

                # Check required fields
                required_fields_check = []
                valid_categories = ['food', 'art', 'culture', 'shopping', 'sightseeing']

                for place in validated_response.places:
                    # Check required fields
                    has_name = bool(place.name and place.name.strip())
                    has_category = bool(place.category and place.category.strip())
                    has_notes = bool(place.notes and place.notes.strip())

                    required_fields_check.append(has_name and has_category and has_notes)

                    # Check category validity
                    if place.category and place.category.lower() in valid_categories:
                        test_results["category_validation"] = True

                test_results["required_fields_valid"] = all(required_fields_check)

            except ValidationError as ve:
                test_results["errors"].append(f"Pydantic validation error: {ve}")
            except Exception as e:
                test_results["errors"].append(f"Validation error: {e}")
        else:
            test_results["errors"].append("Invalid response structure - missing 'places' key")

    except Exception as e:
        test_results["errors"].append(f"Structured output error: {e}")

        # Fallback test with regular JSON parsing
        try:
            messages = [
                SystemMessage(content="You are a travel expert. Return only valid JSON with real, current places."),
                HumanMessage(content=prompt)
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.5, max_tokens=800)
            response = llm_result.content.strip()

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            try:
                data = json.loads(response)
                places = data.get('places', [])
                test_results["places_count"] = len(places)
                test_results["places_data"] = data
                test_results["errors"].append("Fallback to manual JSON parsing succeeded")
            except json.JSONDecodeError as je:
                test_results["errors"].append(f"JSON decode error: {je}")
        except Exception as fe:
            test_results["errors"].append(f"Fallback error: {fe}")

    return test_results

def test_edge_cases():
    """Test edge cases for itinerary validation"""

    edge_cases = [
        {"city": "Paris", "interests": "art, food", "days": 1},
        {"city": "Tokyo", "interests": "culture, shopping, technology", "days": 5},
        {"city": "Mumbai", "interests": "food, markets, bollywood", "days": 3},
        {"city": "Small Town", "interests": "nature, hiking", "days": 2},
    ]

    results = []

    for case in edge_cases:
        print(f"\n🧪 Testing: {case['city']} - {case['interests']} - {case['days']} days")
        result = test_itinerary_structured_output(case["city"], case["interests"], case["days"])
        results.append(result)

        # Print test results
        status = "✅" if result["validation_success"] else "❌"
        print(f"{status} Structured Output: {'Success' if result['structured_success'] else 'Failed'}")
        print(f"{status} Validation: {'Success' if result['validation_success'] else 'Failed'}")
        print(f"📍 Places Count: {result['places_count']}")
        print(f"🏷️ Required Fields: {'Valid' if result['required_fields_valid'] else 'Invalid'}")
        print(f"📂 Categories: {'Valid' if result['category_validation'] else 'Invalid'}")

        if result["errors"]:
            print(f"⚠️ Errors: {'; '.join(result['errors'])}")

    return results

def analyze_field_completeness(results: List[Dict[str, Any]]):
    """Analyze field completeness across all test results"""

    print("\n📊 FIELD COMPLETENESS ANALYSIS")
    print("=" * 50)

    total_places = 0
    field_stats = {
        "name": 0,
        "category": 0,
        "notes": 0,
        "address": 0,
        "neighborhood": 0,
        "coordinates": 0
    }

    for result in results:
        if result.get("places_data") and result.get("validation_success"):
            places = result["places_data"].get("places", [])
            total_places += len(places)

            for place in places:
                if place.get("name"):
                    field_stats["name"] += 1
                if place.get("category"):
                    field_stats["category"] += 1
                if place.get("notes"):
                    field_stats["notes"] += 1
                if place.get("address"):
                    field_stats["address"] += 1
                if place.get("neighborhood"):
                    field_stats["neighborhood"] += 1
                if place.get("latitude") is not None and place.get("longitude") is not None:
                    field_stats["coordinates"] += 1

    print(f"Total Places Analyzed: {total_places}")
    for field, count in field_stats.items():
        percentage = (count / total_places * 100) if total_places > 0 else 0
        print(f"{field.capitalize()}: {count}/{total_places} ({percentage:.1f}%)")

if __name__ == "__main__":
    print("🚀 STARTING ITINERARY STRUCTURED OUTPUT VALIDATION TESTS")
    print("=" * 60)

    # Run edge case tests
    results = test_edge_cases()

    # Analyze results
    successful_tests = sum(1 for r in results if r["validation_success"])
    total_tests = len(results)

    print(f"\n🎯 OVERALL RESULTS")
    print("=" * 30)
    print(f"Successful Tests: {successful_tests}/{total_tests}")
    print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")

    # Analyze field completeness
    analyze_field_completeness(results)

    print(f"\n✅ All tests completed!")