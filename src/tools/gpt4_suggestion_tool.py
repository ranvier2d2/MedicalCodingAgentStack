from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import json
from litellm import completion


class Gpt4SuggestionToolInput(BaseModel):
    """Input schema for Gpt4SuggestionTool."""
    argument: str = Field(..., description="The medical diagnosis text to analyze.")


class Gpt4SuggestionTool(BaseTool):
    name: str = "gpt4_suggestion_tool"
    description: str = (
        "Generates ICD-10 code suggestions from diagnosis text, providing detailed explanations for each suggestion."
    )
    args_schema: Type[BaseModel] = Gpt4SuggestionToolInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_key = os.getenv("AZURE_API_KEY")
        self._api_base = os.getenv("AZURE_API_BASE")
        self._api_version = os.getenv("AZURE_API_VERSION")

        # Validate environment variables
        missing_vars = [
            var for var in ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
            if not os.getenv(var)
        ]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def _run(self, argument: str) -> str:
        """Generate ICD-10 suggestions for a medical diagnosis."""
        system_message = """You are a medical coding expert specializing in ICD-10 classifications.
    Your task is to analyze medical diagnoses and suggest appropriate codes.
    Always return your response in the specified JSON format with up to 5 relevant ICD-10 codes."""

        prompt = f"""Analyze the following medical diagnosis and suggest appropriate ICD-10 codes.

    Diagnosis: {argument}

    Return your response in this exact JSON format:
    {{
        "icd10_suggestions": [
            {{"code": "S06.0", "description": "Concussion"}},
            {{"code": "R55", "description": "Syncope and collapse"}},
            {{"code": "S00.0", "description": "Superficial injury of scalp"}}
        ],
        "explanation": "Detailed explanation of why these codes are appropriate for the diagnosis",
        "who_database_url": "https://icd.who.int/browse10/2019/en"
    }}"""

        try:
            response = completion(
                model="azure/gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                api_key=self._api_key,
                api_base=self._api_base,
                api_version=self._api_version,
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # Validate and return the JSON response
            response_content = response.get("choices", [])[0].get("message", {}).get("content", "{}")
            response_json = json.loads(response_content)
            return json.dumps(response_json, indent=2)

        except json.JSONDecodeError as e:
            return f"Error decoding JSON response: {str(e)}"
        except KeyError as e:
            return f"Error accessing response content: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"