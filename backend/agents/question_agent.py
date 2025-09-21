"""
Agent for handling travel questions using OpenAI client with custom endpoint
"""

import os
import json
from openai import OpenAI
from agents.base_agent import BaseAgent
from agents.models import QuestionResponse, AgentState
from agents.tools import search_travel_info_tool

class QuestionAgent(BaseAgent):
    """Agent responsible for answering travel questions using custom OpenAI endpoint"""

    def __init__(self):
        super().__init__()
        # Set up OpenAI client with custom endpoint
        self.agent_endpoint = "https://k5nlsozsryjs3hy5bm6a4txz.agents.do-ai.run/api/v1/"
        self.agent_access_key = "ei3Ze3tHpKpqFrDfaEfgjYN8Mh8iq0IN"
        
        self.client = OpenAI(
            base_url=self.agent_endpoint,
            api_key=self.agent_access_key,
        )

    def answer_question(self, user_question: str, city: str, interests: str,
                       current_places: list = None, chat_history: list = None) -> dict:
        """Answer travel questions using custom OpenAI endpoint"""

        # # Format chat history nicely
        # chat_history_text = ""
        # if chat_history:
        #     chat_history_text = "Chat History:\n"
        #     for msg in chat_history:
        #         # Handle different possible formats
        #         if isinstance(msg, dict):
        #             role = msg.get('role', 'user')
        #             content = msg.get('content', '')
        #         elif isinstance(msg, str):
        #             role = 'user'
        #             content = msg
        #         else:
        #             role = 'user'
        #             content = str(msg)
                
        #         # Skip empty messages
        #         if content.strip():
        #             chat_history_text += f"- {role}: {content}\n"
        #     chat_history_text += "\n"
        # else:
        #     chat_history_text = "No previous chat history.\n\n"

        prompt = f"""{chat_history} User Question: {user_question}

        Please answer the user's question based on the context provided."""

        print(f"[QUESTION V2] Prompt sent to LLM:")
        print(f"[QUESTION V2] {prompt}")
        print(f"[QUESTION V2] --- End of prompt ---")

        try:
            # Call the custom OpenAI endpoint
            response = self.client.chat.completions.create(
                model="n/a",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"include_retrieval_info": False}
            )

            # Extract the response content
            response_content = ""
            for choice in response.choices:
                response_content = choice.message.content
                break

            print(f"[QUESTION V2] Raw LLM response: {response_content}")

            # Clean up the response
            if response_content:
                # Remove any JSON formatting if present
                try:
                    # Try to parse as JSON first
                    json_response = json.loads(response_content)
                    if isinstance(json_response, dict) and 'response' in json_response:
                        response_content = json_response['response']
                    elif isinstance(json_response, str):
                        response_content = json_response
                except json.JSONDecodeError:
                    # If not JSON, use as is
                    pass

                # Ensure response ends with period if it doesn't
                if response_content and not response_content.endswith('.'):
                    response_content += '.'

                print(f"[QUESTION V2] Final processed response: {response_content}")

                return {
                    "type": "answer",
                    "response": response_content
                }
            else:
                # Fallback response
                return {
                    "type": "answer",
                    "response": f"Check {city} travel guides for {user_question.replace('?', '').lower()}."
                }

        except Exception as e:
            print(f"[ERROR] Question V2 error: {type(e).__name__}: {e}")
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
        """Run the question agent V2"""

        user_question = state.metadata.get('instruction', state.query)
        current_places = [p.model_dump() if hasattr(p, 'model_dump') else p for p in state.places]
        chat_history = state.metadata.get('chat_history', [])

        print(f"[QUESTION V2] Chat history received: {len(chat_history) if chat_history else 0} messages")

        result = self.answer_question(
            user_question,
            state.city,
            state.interests,
            current_places,
            chat_history
        )

        state.response = result.get('response', '')
        state.metadata['result_type'] = 'answer'

        return state

    def test_connection(self) -> bool:
        """Test the connection to the custom endpoint"""
        try:
            response = self.client.chat.completions.create(
                model="n/a",
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                extra_body={"include_retrieval_info": True}
            )
            return True
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False
