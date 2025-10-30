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
from langchain_core.messages import SystemMessage, HumanMessage
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

    def _should_use_search(self, user_question: str, current_places: list) -> bool:
        """Heuristic to decide if external search tools are needed"""
        q = (user_question or "").lower()

        # If question explicitly references a place already in itinerary, prefer no search
        try:
            place_names = [p.get('name', '') for p in current_places or [] if isinstance(p, dict)]
            for name in place_names:
                if name and name.lower() in q:
                    return False
        except Exception:
            pass

        # Keywords that typically require fresh/external info
        search_keywords = [
            'best', 'top', 'opening hours', 'hours', 'tickets', 'price', 'prices', 'cost',
            'weather', 'forecast', 'distance', 'how far', 'how to get', 'transport', 'metro',
            'bus', 'train', 'visa', 'safety', 'current', 'near me', 'hotel', 'accommodation',
            'reservation', 'booking', 'recommend', 'recommended', 'kid-friendly', 'budget'
        ]
        if any(k in q for k in search_keywords):
            return True

        # Default: no search unless clearly needed
        return False

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

        # Build a concise itinerary context for better follow-up grounding
        itinerary_summaries = []
        if current_places:
            for place in current_places[:10]:  # limit context size
                if isinstance(place, dict):
                    name = place.get('name') or 'Unknown'
                    category = place.get('category') or ''
                    neighborhood = place.get('neighborhood') or ''
                    short_note = (place.get('notes') or '')[:80]
                    parts = [name]
                    if category:
                        parts.append(f"{category}")
                    if neighborhood:
                        parts.append(f"{neighborhood}")
                    if short_note:
                        parts.append(f"{short_note}")
                    itinerary_summaries.append(" - " + " | ".join(parts))

        itinerary_context = "\n".join(itinerary_summaries) if itinerary_summaries else "(none)"

        # System instruction to keep answers contextual and conversational
        system_message = (
            "You are PlanMyTrip, a friendly travel assistant."
            " Continue the conversation naturally using the provided trip context,"
            " itinerary, and recent messages. If the user references 'day X', 'this', or a place"
            " without naming it, infer from the itinerary. Prefer concise, actionable answers."
            " Do not change the itinerary here; just answer questions."
            " Use external tools/search only when strictly necessary (e.g., fresh details like opening hours, prices, current recommendations)."
        )

        # Prepare messages with recent chat history for continuity
        messages = [("system", system_message)]

        # Map frontend chat history to agent message tuples
        if chat_history and isinstance(chat_history, list):
            recent_history = chat_history[-8:]  # last few turns for context
            for msg in recent_history:
                role = msg.get('type', '').lower()
                content = msg.get('message', '')
                if not content:
                    continue
                if role == 'user':
                    messages.append(("user", content))
                elif role == 'bot':
                    messages.append(("assistant", content))

        # Append the current question with structured context
        context_intro = []
        if city:
            context_intro.append(f"Location: {city}")
        if interests:
            context_intro.append(f"Interests: {interests}")
        context_intro = ". ".join(context_intro)

        current_context_block = (
            f"Context: {context_intro}\n"
            f"Itinerary (up to 10 items):\n{itinerary_context}\n"
            f"User question: {user_question}"
        ).strip()

        messages.append(("user", current_context_block))

        print(f"[QUESTION V2] Processing question with ReAct agent")
        print(f"[QUESTION V2] Messages prepared: {len(messages)} (including system and history)")

        try:
            # Decide whether to allow tool usage for this question
            use_search = self._should_use_search(user_question, current_places)
            print(f"[QUESTION V2] Should use search: {use_search}")

            if not use_search:
                # Answer directly from context without tools
                try:
                    llm_messages = [SystemMessage(content=system_message)]
                    # Replay recent conversation succinctly
                    if chat_history and isinstance(chat_history, list):
                        for msg in chat_history[-6:]:
                            role = (msg.get('type') or '').lower()
                            content = msg.get('message') or ''
                            if not content:
                                continue
                            if role == 'user':
                                llm_messages.append(HumanMessage(content=content))
                            elif role == 'bot':
                                # Use HumanMessage for simplicity if AIMessage not imported; content is what matters
                                llm_messages.append(SystemMessage(content=f"Assistant previously said: {content}"))

                    llm_messages.append(HumanMessage(content=current_context_block))

                    llm_result = self.llm.invoke(llm_messages)
                    response_text = getattr(llm_result, 'content', None) or ""

                    return {
                        "type": "answer",
                        "response": response_text.strip() or f"I'd be happy to help you with information about {city}. Could you please be more specific about what you'd like to know?"
                    }
                except Exception as inner_e:
                    print(f"[QUESTION V2] Direct LLM answer failed, falling back to tool agent: {inner_e}")
                    use_search = True

            if use_search:
                # Use ReAct agent with tools only when needed
                local_agent = None
                try:
                    local_agent = create_react_agent(self.llm, self.tools)
                except Exception as e:
                    print(f"[QUESTION V2] Failed to create local ReAct agent: {e}")

                if local_agent:
                    events = local_agent.stream(
                        {
                            "messages": messages
                        },
                        stream_mode="values",
                    )

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
                    # If tools can't be used, try enhanced search fallback
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
