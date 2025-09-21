"""
Base agent class for trip planning functionality
"""

import os
from typing import Any, Dict, List, Optional
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    """Base class for all trip planning agents"""

    def __init__(self, model: str = "llama3.3-70b-instruct"):
        """Initialize the base agent with gradient LLM"""
        self.llm = ChatGradient(
            model=model,
            api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
        )

    def create_structured_chain(self, prompt_template: str, pydantic_model: BaseModel):
        """Create a structured output chain with proper error handling"""
        parser = JsonOutputParser(pydantic_object=pydantic_model)

        template = PromptTemplate(
            template=prompt_template + "\n\n{format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        return template | self.llm | parser

    def execute_with_fallback(self, chain, prompt: str, pydantic_model: BaseModel, fallback_prompt: str = None):
        """Execute chain with fallback to regular LLM call"""
        try:
            # Try structured output first
            result = chain.invoke({"query": prompt})
            return result
        except Exception as e:
            print(f"[STRUCTURED] Structured output failed, using fallback: {e}")

            # Fallback to regular call
            messages = [
                SystemMessage(content=fallback_prompt or "You are a helpful assistant. Return valid JSON."),
                HumanMessage(content=prompt)
            ]

            llm_result = self.llm.invoke(messages, temperature=0.5, max_tokens=800)
            response = llm_result.content.strip() if llm_result.content else ""

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # Handle empty or invalid responses
            if not response:
                print(f"[FALLBACK] Empty response received")
                # Return appropriate default for classification
                if pydantic_model.__name__ == 'ClassificationResponse':
                    return {'classification': 'question'}
                return {}

            # Parse JSON
            try:
                import json
                parsed = json.loads(response)
                return parsed
            except json.JSONDecodeError:
                print(f"[FALLBACK] JSON parsing failed for response: '{response}'")

                # Try to extract single word responses for classification
                if pydantic_model.__name__ == 'ClassificationResponse':
                    response_lower = response.lower()
                    if 'modification' in response_lower:
                        return {'classification': 'modification'}
                    elif 'question' in response_lower:
                        return {'classification': 'question'}

                # Return default structure based on pydantic model
                try:
                    # Access model_fields from the class itself
                    if hasattr(pydantic_model, '__annotations__'):
                        default_response = {field: None for field in pydantic_model.__annotations__.keys()}
                    else:
                        default_response = {field: None for field in pydantic_model.model_fields.keys()}
                    print(f"[FALLBACK] Using default response: {default_response}")
                    return default_response
                except (AttributeError, TypeError):
                    return {}