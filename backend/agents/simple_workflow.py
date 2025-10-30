"""
Simplified workflow for orchestrating trip planning agents (without LangGraph dependency)
"""

from typing import Dict, Any
from agents.models import AgentState, Place
from agents.extraction_agent import ExtractionAgent
from agents.search_agent import SearchAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from agents.itinerary_agent import ItineraryAgent
from agents.question_agent import QuestionAgent

class SimpleTripPlanningWorkflow:
    """Simplified workflow for trip planning without LangGraph"""

    def __init__(self):
        """Initialize the workflow with agents"""
        self.extraction_agent = ExtractionAgent()
        self.search_agent = SearchAgent()
        self.intent_classifier = IntentClassifierAgent()
        self.itinerary_agent = ItineraryAgent()
        self.question_agent = QuestionAgent()

    def extract_trip_request(self, trip_request_text: str) -> Dict[str, Any]:
        """Extract trip details from text"""
        initial_state = AgentState(
            query=trip_request_text,
            metadata={}
        )

        # Run only extraction
        result = self.extraction_agent.run(initial_state)

        return {
            "destination": result.destination or result.city,
            "destination_type": result.destination_type or "city",
            "city": result.destination or result.city,  # deprecated mirror
            "interests": result.interests,
            "days": result.days
        }

    def generate_itinerary(self, city: str, interests: str, days: int) -> Dict[str, Any]:
        """Generate a new itinerary"""
        # Initialize state
        state = AgentState(
            query=f"Generate itinerary for {city} for {days} days with interests {interests}",
            destination=city,
            destination_type="city",
            city=city,
            interests=interests,
            days=days,
            places=[],
            metadata={}
        )

        # Run search agent
        state = self.search_agent.run(state)

        # Run itinerary agent
        state = self.itinerary_agent.run(state)

        return {
            "destination": state.destination or state.city,
            "destination_type": state.destination_type or "city",
            "city": state.city,
            "interests": state.interests,
            "days": state.days,
            "places": [p.model_dump() if hasattr(p, 'model_dump') else p.__dict__ for p in state.places],
            "raw_research_text": state.metadata.get('raw_research_text')
        }

    def handle_modification(self, city: str, interests: str, days: int,
                          existing_places: list, instruction: str,
                          original_request: str = None, chat_history: list = None) -> Dict[str, Any]:
        """Handle modification requests"""

        # Convert places to Place objects if needed
        place_objects = []
        for p in existing_places:
            if isinstance(p, dict):
                place_objects.append(Place(**p))
            else:
                place_objects.append(p)

        # Initialize state
        state = AgentState(
            query=instruction,
            destination=city,
            destination_type="city",
            city=city,
            interests=interests,
            days=days,
            places=place_objects,
            metadata={
                'instruction': instruction,
                'original_request': original_request,
                'chat_history': chat_history
            }
        )

        # Run intent classifier
        state = self.intent_classifier.run(state)

        # Run search agent
        # state = self.search_agent.run(state)

        # Route based on intent
        if state.intent == "question":
            # Run question agent
            state = self.question_agent.run(state)

            return {
                "destination": state.destination or state.city,
                "destination_type": state.destination_type or "city",
                "city": state.city,
                "interests": state.interests,
                "days": state.days,
                "places": [p.model_dump() if hasattr(p, 'model_dump') else p.__dict__ for p in state.places],
                "type": "answer",
                "response": state.response
            }
        else:
            # Run itinerary agent for modifications
            state = self.itinerary_agent.run(state)

            return {
                "destination": state.destination or state.city,
                "destination_type": state.destination_type or "city",
                "city": state.city,
                "interests": state.interests,
                "days": state.days,
                "places": [p.model_dump() if hasattr(p, 'model_dump') else p.__dict__ for p in state.places],
                "type": "modification",
                "response": state.response or "I've processed your modification request."
            }

# Global workflow instance
trip_workflow = SimpleTripPlanningWorkflow()