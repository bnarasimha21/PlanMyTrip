"""
Agent for classifying user intent (question vs modification)
"""

from agents.base_agent import BaseAgent
from agents.models import ClassificationResponse, AgentState

class IntentClassifierAgent(BaseAgent):
    """Agent responsible for classifying user intent"""

    def classify_user_intent(self, user_input: str, context: str = None) -> str:
        """
        Classify whether user input is a question or modification request
        Returns: 'question' or 'modification'
        """

        prompt = f"""Classify the following user input as either a "question" or a "modification" request for a travel itinerary.

USER INPUT: "{user_input}"

CONTEXT: {context or "User is planning a trip and has an existing itinerary."}

CLASSIFICATION RULES:
- "question": User is asking for information, advice, recommendations, explanations, or seeking help. This includes questions about availability, possibilities, or general inquiries.
  Examples: "What's the best time to visit?", "How far is X from Y?", "Which place is better?", "What should I know about X?", "Can I get a scooter rental?", "Is there a good restaurant nearby?", "Where can I find X?"

- "modification": User is giving a direct command or explicit request to change, add, remove, or replace something in their itinerary. Look for imperative verbs and direct instructions.
  Examples: "Add a restaurant", "Remove the museum", "Replace X with Y", "Include more shopping places", "Put in a scooter rental", "Take out expensive places"

Respond with ONLY one word: "question" or "modification"."""

        # Create structured chain
        chain = self.create_structured_chain(
            "You are a precise intent classifier for travel planning. 'question' = asking for information/availability. 'modification' = direct command to change itinerary. Questions about 'can I', 'where can I', 'is there' are ALWAYS questions, not modifications.",
            ClassificationResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                ClassificationResponse,
                "You are a precise intent classifier for travel planning. Respond with only 'question' or 'modification'."
            )

            classification = result.get('classification', '').lower()

            # Debug logging
            print(f"[CLASSIFIER] Input: '{user_input}' -> Raw response: '{classification}'")

            # Ensure we only get valid responses
            if classification in ['question', 'modification']:
                print(f"[CLASSIFIER] Final classification: {classification}")
                return classification
            else:
                # Default to question if unclear
                print(f"[CLASSIFIER] Invalid response '{classification}', defaulting to 'question'")
                return 'question'

        except Exception as e:
            print(f"Classification error: {e}")
            # Default to question on error
            return 'question'

    def run(self, state: AgentState) -> AgentState:
        """Run the intent classifier agent"""

        # For modification requests, we need the instruction from metadata
        user_input = state.metadata.get('instruction', state.query)

        # Build context
        context = f"User is planning a {state.days}-day trip to {state.city} with interests in {state.interests}. "
        if state.places:
            place_names = [p.name for p in state.places[:5]]  # First 5 places for context
            context += f"Current itinerary includes: {', '.join(place_names)}."
        else:
            context += "No places in itinerary yet."

        intent = self.classify_user_intent(user_input, context)
        state.intent = intent

        return state