"""
Agent for handling travel questions
"""

from agents.base_agent import BaseAgent
from agents.models import QuestionResponse, AgentState
from agents.tools import search_travel_info_tool

class QuestionAgent(BaseAgent):
    """Agent responsible for answering travel questions"""

    def answer_question(self, user_question: str, city: str, interests: str,
                       current_places: list = None, chat_history: list = None) -> dict:
        """Answer travel questions using SERP API for current information"""

        print(f"[QUESTION] Answering: {user_question}")

        if not user_question or not user_question.strip():
            return {
                "type": "answer",
                "response": "Please ask me a question about your travel plans."
            }

        # Get brief info from SERP API (first 100 chars only)
        serp_info = search_travel_info_tool(user_question, city)[:100]

        # Create very short context
        context = f"Trip: {city}, {interests}"
        if current_places and len(current_places) > 0:
            context += f", Current places: {len(current_places)}"

        prompt = f"""{context}

Question: {user_question}

Context: {serp_info}

Give a direct 1-sentence answer (max 20 words):"""

        # Create structured chain
        chain = self.create_structured_chain(
            "Answer travel questions in exactly 1 sentence. Maximum 20 words. Be direct and helpful.",
            QuestionResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                QuestionResponse,
                "Answer travel questions in exactly 1 sentence. Maximum 20 words. Be direct and helpful."
            )

            response = result.get('response', '')

            # Ensure response ends with period if it doesn't
            if response and not response.endswith('.'):
                response += '.'

            return {
                "type": "answer",
                "response": response
            }

        except Exception as e:
            print(f"[ERROR] Question error: {type(e).__name__}: {e}")
            # Try a simple fallback response
            try:
                simple_response = f"Check {city} travel guides for {user_question.replace('?', '').lower()}."
                return {
                    "type": "answer",
                    "response": simple_response
                }
            except:
                return {
                    "type": "answer",
                    "response": f"You can find that in {city}. Check local recommendations."
                }

    def run(self, state: AgentState) -> AgentState:
        """Run the question agent"""

        user_question = state.metadata.get('instruction', state.query)
        current_places = [p.model_dump() if hasattr(p, 'model_dump') else p for p in state.places]

        result = self.answer_question(
            user_question,
            state.city,
            state.interests,
            current_places,
            state.metadata.get('chat_history', [])
        )

        state.response = result.get('response', '')
        state.metadata['result_type'] = 'answer'

        return state