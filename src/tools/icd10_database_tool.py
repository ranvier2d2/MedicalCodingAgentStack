from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import pandas as pd
from difflib import SequenceMatcher

class ICD10DatabaseToolInput(BaseModel):
    """
    Input schema for the ICD10DatabaseTool used by the validation agent.
    
    Attributes:
        code (str, optional): ICD-10 code to validate against the WHO database.
        description (str, optional): Description to validate against the code's official description.
    """
    code: str = Field(
        None,
        description="ICD-10 code to validate against the WHO database."
    )
    description: str = Field(
        None,
        description="Description to validate against the code's official description."
    )

class ICD10DatabaseTool(BaseTool):
    """
    A validation tool for the Validation Agent to verify ICD-10 codes and descriptions.
    
    Primary responsibilities:
    1. Validate if an ICD-10 code exists in the WHO database
    2. Verify if a description matches the official WHO description for a code
    3. Suggest alternative codes when validation fails
    """
    name: str = "icd10_database_tool"
    description: str = (
        "A validation tool that:\n"
        "1. Validates ICD-10 codes against the WHO database\n"
        "2. Verifies descriptions match official WHO descriptions\n"
        "3. Suggests alternatives when validation fails\n"
        "Used by the Validation Agent to ensure accuracy of medical coding."
    )
    args_schema: Type[BaseModel] = ICD10DatabaseToolInput

    def __init__(self, database_path: str, **kwargs):
        """Initialize with the WHO ICD-10 database."""
        super().__init__(**kwargs)
        self._database = pd.read_csv(database_path)

    def _run(
        self,
        code: str = None,
        description: str = None
    ) -> Dict:
        """
        Validate an ICD-10 code and/or description.

        Args:
            code: ICD-10 code to validate
            description: Description to verify against the code's official description

        Returns:
            For code validation:
            {
                "valid": bool,
                "code": str,
                "official_description": str,  # WHO database description
                "description_match": bool,    # if description provided
                "chapter": str,
                "domain": str,
                "url": str,
                "alternatives": List[Dict]    # if validation fails
            }

        Raises:
            ValueError: If code is not provided
        """
        if not code:
            raise ValueError("Code must be provided for validation")

        match = self._database[self._database["sub-code"] == code]
        
        if match.empty:
            return {
                "valid": False,
                "code": code,
                "note": "Invalid ICD-10 code",
                "alternatives": self._find_alternative_codes(code)
            }

        row = match.iloc[0]
        result = {
            "valid": True,
            "code": code,
            "official_description": row["definition"],
            "chapter": row["chapter"],
            "domain": row["domain"],
            "url": row["url"]
        }

        if description:
            description_match = self._verify_description(
                description, 
                row["definition"]
            )
            result.update({
                "description_match": description_match,
                "provided_description": description,
                "similarity_score": description_match["similarity"] if isinstance(description_match, dict) else None
            })

        return result

    def _verify_description(self, provided: str, official: str) -> Dict:
        """
        Verify if a provided description matches the official WHO description.

        Args:
            provided: Description to verify
            official: Official WHO description

        Returns:
            {
                "matches": bool,
                "similarity": float,
                "note": str
            }
        """
        from difflib import SequenceMatcher
        
        similarity = SequenceMatcher(
            None,
            provided.lower(),
            official.lower()
        ).ratio()

        return {
            "matches": similarity > 0.8,
            "similarity": similarity,
            "note": (
                "Descriptions match" if similarity > 0.8
                else "Descriptions are similar" if similarity > 0.6
                else "Descriptions do not match"
            )
        }

    def _find_alternative_codes(self, code: str) -> List[Dict]:
        """
        Find alternative codes in the same category when validation fails.

        Args:
            code: Invalid ICD-10 code

        Returns:
            List of alternative codes in the same category, each containing:
            {
                "code": str,
                "description": str,
                "domain": str
            }
        """
        # Find codes in the same domain
        code_prefix = code.split('.')[0]
        similar_codes = self._database[
            self._database["sub-code"].str.startswith(code_prefix)
        ]
        
        return [
            {
                "code": row["sub-code"],
                "description": row["definition"],
                "domain": row["domain"]
            }
            for _, row in similar_codes.iterrows()
        ][:5]  # Limit to 5 alternatives
