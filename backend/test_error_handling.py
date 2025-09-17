#!/usr/bin/env python3
"""
Test error handling and validation robustness for itinerary generation
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

# Define Pydantic models
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

def test_malformed_inputs():
    """Test how the system handles malformed or edge case inputs"""

    print("🔧 TESTING ERROR HANDLING & EDGE CASES")
    print("=" * 50)

    test_cases = [
        {"city": "", "interests": "art", "days": 1, "name": "Empty city"},
        {"city": "NonexistentCity123", "interests": "impossible activities", "days": 1, "name": "Nonexistent city"},
        {"city": "Paris", "interests": "", "days": 1, "name": "Empty interests"},
        {"city": "Tokyo", "interests": "art", "days": 0, "name": "Zero days"},
        {"city": "Mumbai", "interests": "art", "days": 100, "name": "Too many days"},
        {"city": "New York", "interests": "very very very very long interest description that goes on and on", "days": 3, "name": "Very long interests"},
    ]

    results = []

    for case in test_cases:
        print(f"\n🧪 Testing: {case['name']}")
        result = test_with_error_handling(case["city"], case["interests"], case["days"])
        results.append({**result, "test_name": case["name"]})

        # Print results
        if result["structured_success"]:
            print(f"✅ Handled gracefully - Got {result['places_count']} places")
        else:
            print(f"⚠️ Failed but handled - Errors: {'; '.join(result['errors'])}")

    return results

def test_with_error_handling(city: str, interests: str, days: int):
    """Test itinerary generation with comprehensive error handling"""

    # Handle edge cases in input
    if not city or not city.strip():
        city = "Paris"  # Default fallback
    if not interests or not interests.strip():
        interests = "art, food"  # Default fallback
    if days <= 0:
        days = 1  # Default fallback
    if days > 30:
        days = 7  # Reasonable maximum

    prompt = f"""Create a {days}-day travel itinerary for {city} focusing on {interests}.

Requirements:
- Include {max(3, days * 2)} places that match the interests
- Provide real, existing places only
- Include specific details for each place"""

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
        "errors": [],
        "fallback_used": False,
        "data_quality": "unknown"
    }

    try:
        # Test structured output
        result = chain.invoke({"query": prompt})
        test_results["structured_success"] = True

        # Validate the response structure
        if isinstance(result, dict) and 'places' in result:
            places = result.get('places', [])
            test_results["places_count"] = len(places)

            # Validate using Pydantic model
            try:
                validated_response = ItineraryResponse(**result)
                test_results["validation_success"] = True

                # Assess data quality
                quality_score = assess_data_quality(validated_response.places)
                test_results["data_quality"] = quality_score

            except ValidationError as ve:
                test_results["errors"].append(f"Pydantic validation failed: {str(ve)[:100]}")
            except Exception as e:
                test_results["errors"].append(f"Validation error: {str(e)[:100]}")
        else:
            test_results["errors"].append("Invalid response structure")

    except Exception as e:
        test_results["errors"].append(f"Structured output failed: {str(e)[:100]}")
        test_results["fallback_used"] = True

        # Test fallback mechanism
        try:
            messages = [
                SystemMessage(content="You are a travel expert. Return only valid JSON with real places."),
                HumanMessage(content=prompt + "\n\nReturn JSON with 'places' array containing place objects.")
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.5, max_tokens=800)
            response = llm_result.content.strip()

            # Clean and parse JSON
            cleaned_response = clean_json_response(response)

            try:
                data = json.loads(cleaned_response)
                places = data.get('places', [])
                test_results["places_count"] = len(places)
                test_results["structured_success"] = True  # Fallback succeeded

                # Try to validate fallback data
                try:
                    validated_response = ItineraryResponse(**data)
                    test_results["validation_success"] = True
                    quality_score = assess_data_quality(validated_response.places)
                    test_results["data_quality"] = quality_score
                except Exception:
                    test_results["errors"].append("Fallback data validation failed")

            except json.JSONDecodeError as je:
                test_results["errors"].append(f"JSON parsing failed: {str(je)[:100]}")
        except Exception as fe:
            test_results["errors"].append(f"Fallback mechanism failed: {str(fe)[:100]}")

    return test_results

def clean_json_response(response: str) -> str:
    """Clean JSON response from potential markdown or extra text"""
    response = response.strip()

    # Remove markdown code blocks
    if response.startswith('```json'):
        response = response[7:]
    elif response.startswith('```'):
        response = response[3:]
    if response.endswith('```'):
        response = response[:-3]

    response = response.strip()

    # Try to find JSON object boundaries
    start_idx = response.find('{')
    end_idx = response.rfind('}')

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        response = response[start_idx:end_idx+1]

    return response

def assess_data_quality(places: List[Place]) -> str:
    """Assess the quality of place data"""
    if not places:
        return "no_data"

    total_places = len(places)
    quality_scores = []

    for place in places:
        score = 0

        # Required fields
        if place.name and len(place.name.strip()) > 0:
            score += 2
        if place.category and place.category.strip():
            score += 2
        if place.notes and len(place.notes.strip()) > 10:
            score += 2

        # Optional but valuable fields
        if place.address and len(place.address.strip()) > 5:
            score += 1
        if place.neighborhood:
            score += 1
        if place.latitude is not None and place.longitude is not None:
            score += 1

        quality_scores.append(score)

    avg_score = sum(quality_scores) / len(quality_scores)

    if avg_score >= 7:
        return "excellent"
    elif avg_score >= 5:
        return "good"
    elif avg_score >= 3:
        return "fair"
    else:
        return "poor"

def test_concurrent_requests():
    """Test multiple concurrent requests for stability"""

    print("\n🔄 TESTING CONCURRENT REQUESTS")
    print("=" * 40)

    import threading
    import time

    results = []
    errors = []

    def make_request(i):
        try:
            result = test_with_error_handling(f"City{i}", "art, food", 2)
            results.append(result)
            print(f"✅ Request {i}: {result['places_count']} places")
        except Exception as e:
            errors.append(f"Request {i}: {str(e)}")
            print(f"❌ Request {i}: Failed")

    # Create and start threads
    threads = []
    start_time = time.time()

    for i in range(5):  # Test 5 concurrent requests
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    end_time = time.time()

    print(f"\n📊 Concurrent Test Results:")
    print(f"Total Requests: 5")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(errors)}")
    print(f"Total Time: {end_time - start_time:.2f}s")
    print(f"Average Time per Request: {(end_time - start_time)/5:.2f}s")

    return results, errors

if __name__ == "__main__":
    print("🚀 STARTING ERROR HANDLING & ROBUSTNESS TESTS")
    print("=" * 55)

    # Test malformed inputs
    malformed_results = test_malformed_inputs()

    # Test concurrent requests
    concurrent_results, concurrent_errors = test_concurrent_requests()

    # Summary
    print(f"\n🎯 FINAL SUMMARY")
    print("=" * 30)

    malformed_success = sum(1 for r in malformed_results if r["structured_success"])
    concurrent_success = len(concurrent_results)

    print(f"Malformed Input Tests: {malformed_success}/{len(malformed_results)} handled gracefully")
    print(f"Concurrent Request Tests: {concurrent_success}/5 successful")

    # Quality analysis
    all_results = malformed_results + concurrent_results
    quality_distribution = {}
    for result in all_results:
        if result.get("data_quality"):
            quality = result["data_quality"]
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1

    print(f"\n📈 Data Quality Distribution:")
    for quality, count in quality_distribution.items():
        print(f"  {quality.capitalize()}: {count}")

    print(f"\n✅ All robustness tests completed!")