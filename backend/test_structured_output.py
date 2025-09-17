#!/usr/bin/env python3
"""
Test structured output functionality
"""

import os
from dotenv import load_dotenv
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

# Define Pydantic models for structured output
class ClassificationResponse(BaseModel):
    classification: str = Field(description="Either 'question' or 'modification'")

class Place(BaseModel):
    name: str = Field(description="Name of the place")
    neighborhood: str = Field(description="Neighborhood or area", default=None)
    category: str = Field(description="Category: food/art/culture/shopping/sightseeing")
    address: str = Field(description="Full address", default=None)
    latitude: float = Field(description="Latitude coordinate", default=None)
    longitude: float = Field(description="Longitude coordinate", default=None)
    notes: str = Field(description="Brief description or notes")

class TripExtractionResponse(BaseModel):
    city: str = Field(description="City name")
    interests: str = Field(description="Comma-separated interests")
    days: int = Field(description="Number of days")

# Initialize Gradient LLM
gradient_llm = ChatGradient(
    model="llama3.3-70b-instruct",
    api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
)

def test_classification():
    """Test classification with structured output"""
    user_input = "can I get a scooter rental in hanoi"

    # Set up structured output parser
    parser = JsonOutputParser(pydantic_object=ClassificationResponse)

    prompt_template = PromptTemplate(
        template="You are a precise intent classifier for travel planning. 'question' = asking for information/availability. 'modification' = direct command to change itinerary. Questions about 'can I', 'where can I', 'is there' are ALWAYS questions, not modifications.\\n\\n{format_instructions}\\n\\nClassify: {query}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt_template | gradient_llm | parser

    try:
        result = chain.invoke({"query": user_input})
        classification = result.get('classification', '').lower()
        return classification
    except Exception as e:
        print(f"Structured output failed: {e}")
        return None

def test_extraction():
    """Test trip extraction with structured output"""
    trip_request = "Plan a 3-day art and food tour in Paris"

    # Set up structured output parser
    parser = JsonOutputParser(pydantic_object=TripExtractionResponse)

    prompt_template = PromptTemplate(
        template="Extract travel information from the request.\\n\\n{format_instructions}\\n\\nExtract from: {query}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt_template | gradient_llm | parser

    try:
        result = chain.invoke({"query": trip_request})
        return result
    except Exception as e:
        print(f"Structured output failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing structured output functions...")

    # Test classification
    try:
        result = test_classification()
        if result:
            print(f"✓ Classification test: {result}")
        else:
            print("✗ Classification test failed")
    except Exception as e:
        print(f"✗ Classification error: {e}")

    # Test extraction
    try:
        result = test_extraction()
        if result:
            print(f"✓ Extraction test: {result}")
        else:
            print("✗ Extraction test failed")
    except Exception as e:
        print(f"✗ Extraction error: {e}")

    print("Tests completed!")