"""
Pydantic models for agent communication and data structures
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Place(BaseModel):
    """Model for a travel place/destination"""
    name: str = Field(description="Name of the place")
    neighborhood: Optional[str] = Field(description="Neighborhood or area", default=None)
    category: str = Field(description="Category: food/art/culture/shopping/sightseeing")
    address: Optional[str] = Field(description="Full address", default=None)
    latitude: Optional[float] = Field(description="Latitude coordinate", default=None)
    longitude: Optional[float] = Field(description="Longitude coordinate", default=None)
    notes: str = Field(description="Brief description or notes")

class TripExtractionResponse(BaseModel):
    """Response model for trip extraction"""
    # New generic destination fields (preferred)
    destination: Optional[str] = Field(description="Destination name (city or country)", default=None)
    destination_type: Optional[str] = Field(description="Type of destination: city|country", default=None)
    # Backward compatibility
    city: str = Field(description="City name")
    interests: str = Field(description="Comma-separated interests")
    days: int = Field(description="Number of days")

class ItineraryResponse(BaseModel):
    """Response model for itinerary generation"""
    places: List[Place] = Field(description="List of places for the itinerary")

class ClassificationResponse(BaseModel):
    """Response model for intent classification"""
    classification: str = Field(description="Either 'question' or 'modification'")

class QuestionResponse(BaseModel):
    """Response model for questions"""
    response: str = Field(description="Answer to the travel question")

class ModificationResponse(BaseModel):
    """Response model for modifications"""
    type: str = Field(description="Type of response", default="modification")
    response: str = Field(description="Description of changes made")
    places: List[Place] = Field(description="Updated list of places")

class SearchResults(BaseModel):
    """Model for search results from web search (Tavily)"""
    places: List[Dict[str, Any]] = Field(description="List of places from search")
    context: str = Field(description="Formatted context for agents")

class AgentState(BaseModel):
    """State model for LangGraph agents"""
    query: str = Field(description="Original user query")
    # New generic destination fields (preferred)
    destination: Optional[str] = Field(description="Target destination (city or country)", default=None)
    destination_type: Optional[str] = Field(description="Destination type", default=None)
    city: Optional[str] = Field(description="Target city", default=None)
    interests: Optional[str] = Field(description="User interests", default=None)
    days: Optional[int] = Field(description="Number of days", default=None)
    places: List[Place] = Field(description="Current places in itinerary", default_factory=list)
    search_results: Optional[SearchResults] = Field(description="Search results", default=None)
    intent: Optional[str] = Field(description="User intent (question/modification)", default=None)
    response: Optional[str] = Field(description="Final response", default=None)
    metadata: Dict[str, Any] = Field(description="Additional metadata", default_factory=dict)