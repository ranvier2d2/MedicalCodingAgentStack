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
        "Generates ICD-10 and SNOMED CT code suggestions from diagnosis text."
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
        """Generate ICD-10 and SNOMED CT suggestions for a medical diagnosis."""
        system_message = """You are a medical coding expert specializing in ICD-10 and SNOMED CT classifications.
    Your task is to analyze medical diagnoses and suggest appropriate codes.
    Always return your response in the specified JSON format with exactly 3 codes for each classification system."""

        prompt = f"""Analyze the following medical diagnosis and suggest appropriate ICD-10 and SNOMED CT codes.

    Diagnosis: {argument}

    Return your response in this exact JSON format:
    {{
        "icd10_suggestions": [
            {{"code": "R51.9", "description": "Headache, unspecified"}},
            {{"code": "G44.1", "description": "Vascular headache"}},
            {{"code": "I60.9", "description": "Subarachnoid hemorrhage"}}
        ],
        "snomed_suggestions": [
            {{"code": "25064002", "description": "Headache"}},
            {{"code": "37796009", "description": "Migraine"}},
            {{"code": "55480006", "description": "Thunderclap headache"}}
        ],
        "explanation": "Brief explanation of why you chose these codes"
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