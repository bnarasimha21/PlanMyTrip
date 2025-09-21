"""
Agent for classifying user intent (question vs modification)
"""

from agents.base_agent import BaseAgent
from agents.models import ClassificationResponse, AgentState

class IntentClassifierAgent(BaseAgent):
    """Agent responsible for classifying user intent"""

    def classify_user_intent(self, user_input: str) -> str:
        """
        Classify whether user input is a question or modification request
        Returns: 'question' or 'modification'
        """

        prompt = f"""
        You are a travel planning intent classifier. Analyze the user's input and determine if it's:
        1. "question" - asking for information, recommendations, or clarification about places, travel, or itinerary
        2. "modification" - requesting direct changes to an itinerary (add/remove/replace/change places)

        User input: "{user_input}"

        Examples:
        - "What's near the museum?" -> question
        - "Add a restaurant" -> modification
        - "Remove the cafe from day 1" -> modification
        - "Tell me about Paris attractions" -> question

        Respond with a JSON object: {{"classification": "question"}} or {{"classification": "modification"}}
        """

        # Create structured chain
        chain = self.create_structured_chain(
            "You are a precise intent classifier for travel planning. Analyze the input and return a JSON object with the classification field.",
            ClassificationResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                ClassificationResponse,
                "You are a precise intent classifier. Return JSON with classification field set to either 'question' or 'modification'."
            )

            # Handle different response formats
            if isinstance(result, dict):
                classification = (result.get('classification') or '').lower()
            elif isinstance(result, str):
                # Handle case where LLM returns just the classification string
                classification = result.lower()
            elif result is None:
                # Handle None response from structured output failure
                classification = ''
            else:
                classification = ''

            # Debug logging
            print(f"[CLASSIFIER] Input: '{user_input}' -> Raw response: {result} -> Classification: '{classification}'")

            # Ensure we only get valid responses
            if classification in ['question', 'modification']:
                print(f"[CLASSIFIER] Final classification: {classification}")
                return classification
            else:
                # Use keyword detection as fallback
                fallback_classification = self._fallback_classification(user_input)
                print(f"[CLASSIFIER] Invalid response '{classification}', using fallback: {fallback_classification}")
                return fallback_classification

        except Exception as e:
            print(f"Classification error: {e}")
            # Use keyword detection as fallback
            return self._fallback_classification(user_input)

    def _fallback_classification(self, user_input: str) -> str:
        """Fallback classification using keyword detection"""
        user_input_lower = user_input.lower()

        # Keywords that indicate modification requests
        modification_keywords = [
            'add', 'remove', 'delete', 'replace', 'change', 'modify', 'update',
            'include', 'exclude', 'swap', 'substitute', 'insert', 'drop'
        ]

        # Keywords that indicate questions
        question_keywords = [
            'what', 'where', 'when', 'how', 'why', 'which', 'who',
            'is', 'are', 'can', 'could', 'would', 'should', 'tell me', 'explain'
        ]

        # Check for modification keywords
        if any(keyword in user_input_lower for keyword in modification_keywords):
            return 'modification'

        # Check for question keywords
        if any(keyword in user_input_lower for keyword in question_keywords):
            return 'question'

        # Default to question if unclear
        return 'question'

    def run(self, state: AgentState) -> AgentState:
        """Run the intent classifier agent"""

        # For modification requests, we need the instruction from metadata
        user_input = state.metadata.get('instruction', state.query)

        intent = self.classify_user_intent(user_input)
        state.intent = intent

        return state