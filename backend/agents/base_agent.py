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
            response = llm_result.content.strip()

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            try:
                import json
                return json.loads(response)
            except json.JSONDecodeError:
                # Return default structure based on pydantic model
                if hasattr(pydantic_model, 'model_fields'):
                    return {field: None for field in pydantic_model.model_fields.keys()}
                return {}