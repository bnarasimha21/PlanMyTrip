"""
Agent for handling travel questions using search-enabled ReAct agent
"""

import os
import json
from typing import List, Dict, Any
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from openai import OpenAI
from agents.base_agent import BaseAgent
from agents.models import QuestionResponse, AgentState
from agents.tools import search_travel_info_tool, search_places_tool

class QuestionAgent(BaseAgent):
    """Agent responsible for answering travel questions using search-enabled ReAct agent"""

    def __init__(self):
        super().__init__()

        # Initialize LLM for ReAct agent
        try:
            # Try OpenAI first
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            print("[QUESTION] OpenAI LLM initialized successfully")
        except Exception as e:
            print(f"[QUESTION] Could not initialize OpenAI LLM, using gradient fallback: {e}")
            # Fallback to gradient LLM from base class
            self.llm = super().llm

        # Create search tools
        self.tools = [
            Tool(
                name="travel_search",
                func=self._search_travel_info,
                description="Search for travel information, recommendations, or answers to travel questions. Use this when the user asks about places, activities, restaurants, attractions, or travel advice."
            ),
            Tool(
                name="place_search",
                func=self._search_places,
                description="Search for specific places like restaurants, attractions, or accommodations in a location. Use this when the user asks for specific place recommendations."
            )
        ]

        # Create the ReAct agent
        try:
            self.agent = create_react_agent(self.llm, self.tools)
            print("[QUESTION] ReAct agent created successfully")
        except Exception as e:
            print(f"[QUESTION] Could not create ReAct agent: {e}")
            self.agent = None

    def _search_travel_info(self, query: str) -> str:
        """Search tool wrapper for travel information"""
        try:
            # Extract location context if available from the query
            location = ""
            if hasattr(self, '_current_city') and self._current_city:
                location = self._current_city

            result = search_travel_info_tool(query, location)
            print(f"[SEARCH] Travel info search for '{query}' in '{location}': {result[:200]}...")
            return result
        except Exception as e:
            print(f"[SEARCH] Travel info search error: {e}")
            return f"Could not search for travel information about: {query}"

    def _search_places(self, query: str) -> str:
        """Search tool wrapper for places"""
        try:
            # Extract location context if available
            location = ""
            if hasattr(self, '_current_city') and self._current_city:
                location = self._current_city

            places = search_places_tool(query, location, num_results=5)

            # Format places for the agent
            if places:
                formatted_places = []
                for place in places:
                    place_str = f"- {place.get('name', 'Unknown')}"
                    if place.get('address'):
                        place_str += f" ({place.get('address')})"
                    if place.get('rating'):
                        place_str += f" - Rating: {place.get('rating')}"
                    if place.get('description'):
                        place_str += f" - {place.get('description')[:100]}..."
                    formatted_places.append(place_str)

                result = "\n".join(formatted_places)
                print(f"[SEARCH] Places search for '{query}' in '{location}': Found {len(places)} places")
                return result
            else:
                return f"No places found for: {query}"

        except Exception as e:
            print(f"[SEARCH] Places search error: {e}")
            return f"Could not search for places: {query}"

    def answer_question(self, user_question: str, city: str, interests: str,
                       current_places: list = None, chat_history: list = None) -> dict:
        """Answer travel questions using search-enabled ReAct agent"""

        # Set current city for search context
        self._current_city = city

        # Prepare context information
        context_parts = []
        if city:
            context_parts.append(f"Location: {city}")
        if interests:
            context_parts.append(f"User interests: {interests}")
        if current_places:
            places_names = [p.get('name', '') for p in current_places if isinstance(p, dict)]
            if places_names:
                context_parts.append(f"Current itinerary places: {', '.join(places_names)}")

        context = ". ".join(context_parts) if context_parts else ""

        # Format the question with context
        full_question = f"{context}. User question: {user_question}" if context else user_question

        print(f"[QUESTION V2] Processing question with ReAct agent")
        print(f"[QUESTION V2] Full question: {full_question}")

        try:
            if self.agent:
                # Use the ReAct agent to answer the question
                print(f"[QUESTION V2] Using ReAct agent for: {full_question}")

                events = self.agent.stream(
                    {
                        "messages": [
                            ("user", full_question)
                        ]
                    },
                    stream_mode="values",
                )

                # Extract the final response from the events
                final_response = ""
                for event in events:
                    if "messages" in event and event["messages"]:
                        last_message = event["messages"][-1]
                        if hasattr(last_message, 'content'):
                            final_response = last_message.content

                print(f"[QUESTION V2] ReAct agent response: {final_response}")

                return {
                    "type": "answer",
                    "response": final_response or f"I'd be happy to help you with information about {city}. Could you please be more specific about what you'd like to know?"
                }
            else:
                # Use enhanced search-based approach as fallback
                return self._enhanced_search_answer(user_question, city, interests, current_places)

        except Exception as e:
            print(f"[QUESTION V2] Error with ReAct agent: {e}")
            return self._fallback_answer(user_question, city, interests)

    def _enhanced_search_answer(self, user_question: str, city: str, interests: str, current_places: list = None) -> dict:
        """Enhanced search-based answer using multiple search strategies"""

        # First try travel info search
        travel_info = search_travel_info_tool(user_question, city)

        # If we get good travel info, use it
        if travel_info and travel_info != "No relevant information found." and len(travel_info) > 50:
            print(f"[QUESTION V2] Using travel info search result")
            return {
                "type": "answer",
                "response": travel_info
            }

        # If travel info is limited, try places search for specific queries
        if any(keyword in user_question.lower() for keyword in ['restaurant', 'eat', 'food', 'place', 'attraction', 'visit', 'see', 'museum', 'hotel']):
            places = search_places_tool(user_question, city, num_results=3)

            if places:
                # Format places into a response
                place_responses = []
                for place in places:
                    place_info = f"• {place.get('name', 'Unknown place')}"
                    if place.get('address'):
                        place_info += f" ({place.get('address')})"
                    if place.get('rating'):
                        place_info += f" - Rating: {place.get('rating')}/5"
                    if place.get('description'):
                        place_info += f" - {place.get('description')[:100]}..."
                    place_responses.append(place_info)

                response = f"Here are some recommendations for {user_question.lower()} in {city}:\n\n" + "\n\n".join(place_responses)

                print(f"[QUESTION V2] Using places search result with {len(places)} places")
                return {
                    "type": "answer",
                    "response": response
                }

        # If we have some travel info but it's limited, enhance it
        if travel_info and travel_info != "No relevant information found.":
            enhanced_response = f"Based on current information about {city}: {travel_info}"
            return {
                "type": "answer",
                "response": enhanced_response
            }

        # Final fallback
        return self._fallback_answer(user_question, city, interests)

    def _fallback_answer(self, user_question: str, city: str, interests: str) -> dict:
        """Fallback method using direct search"""
        try:
            # Try to get information using direct search
            search_result = search_travel_info_tool(user_question, city)

            if search_result and search_result != "No relevant information found.":
                return {
                    "type": "answer",
                    "response": search_result
                }
            else:
                return {
                    "type": "answer",
                    "response": f"I'd recommend checking local {city} travel guides for information about {user_question.replace('?', '').lower()}."
                }
        except Exception as e:
            print(f"[QUESTION V2] Fallback error: {e}")
            return {
                "type": "answer",
                "response": f"You can find information about {user_question.replace('?', '').lower()} in {city} travel resources."
            }

    def run(self, state: AgentState) -> AgentState:
        """Run the question agent"""

        user_question = state.metadata.get('instruction', state.query)
        current_places = [p.model_dump() if hasattr(p, 'model_dump') else p for p in state.places]
        chat_history = state.metadata.get('chat_history', [])

        print(f"[QUESTION] Chat history received: {len(chat_history) if chat_history else 0} messages")

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
