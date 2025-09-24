#!/usr/bin/env python3
"""
Test script for the new modular agent architecture
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_extraction_agent():
    """Test the extraction agent"""
    try:
        from agents.extraction_agent import ExtractionAgent
        from agents.models import AgentState

        agent = ExtractionAgent()
        state = AgentState(query="Plan a 2-day food tour in Tokyo", metadata={})

        result = agent.run(state)
        print(f"✅ Extraction Agent Test: {result.city}, {result.interests}, {result.days}")
        return True
    except Exception as e:
        print(f"❌ Extraction Agent Test Failed: {e}")
        return False

def test_search_agent():
    """Test the search agent with Tavily"""
    try:
        from agents.search_agent import SearchAgent
        from agents.models import AgentState

        agent = SearchAgent()
        state = AgentState(
            query="Generate itinerary",
            city="Tokyo",
            interests="food",
            days=2,
            metadata={}
        )

        result = agent.run(state)
        print(f"✅ Search Agent Test: Found {len(result.search_results.places) if result.search_results else 0} places")
        return True
    except Exception as e:
        print(f"❌ Search Agent Test Failed: {e}")
        return False

def test_intent_classifier():
    """Test the intent classifier agent"""
    try:
        from agents.intent_classifier_agent import IntentClassifierAgent
        from agents.models import AgentState

        agent = IntentClassifierAgent()
        state = AgentState(
            query="add a restaurant",
            city="Tokyo",
            interests="food",
            days=2,
            metadata={'instruction': 'add a restaurant'}
        )

        result = agent.run(state)
        print(f"✅ Intent Classifier Test: Intent = {result.intent}")
        return True
    except Exception as e:
        print(f"❌ Intent Classifier Test Failed: {e}")
        return False

def test_basic_tools():
    """Test basic Tavily tools"""
    try:
        from agents.tools import search_places_tool, search_travel_info_tool

        places = search_places_tool("best restaurants", "Tokyo", 2)
        print(f"✅ Tavily Tools Test: Found {len(places)} places")

        info = search_travel_info_tool("best time to visit Tokyo")
        print(f"✅ Travel Info Test: Got {len(info)} chars of info")
        return True
    except Exception as e:
        print(f"❌ Tavily Tools Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Modular Agent Architecture...")
    print("=" * 50)

    tests = [
        test_basic_tools,
        test_extraction_agent,
        test_search_agent,
        test_intent_classifier,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The modular agent architecture is working.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()