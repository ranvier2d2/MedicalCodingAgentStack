from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import pandas as pd

class ICD10DatabaseToolInput(BaseModel):
    """
    Input schema for the ICD10DatabaseTool.
    """

    code: str = Field(
        None,
        description="The ICD-10 code to validate. Optional if description is provided."
    )
    description: str = Field(
        None,
        description="The ICD-10 description to search for matches. Optional if code is provided."
    )

class ICD10DatabaseTool(BaseTool):
    """
    A CrewAI tool for validating ICD-10 codes or matching descriptions against a pre-loaded ICD-10 database.
    """

    name: str = "icd10_database_tool"
    description: str = (
        "A tool that validates ICD-10 codes or matches descriptions against a pre-loaded ICD-10 database. "
        "This tool supports exact matching by code or performs searches based on descriptions. "
        "Fallback similarity matching is available when no exact description is found."
    )
    args_schema: Type[BaseModel] = ICD10DatabaseToolInput

    def __init__(self, database_path: str, **kwargs):
        """
        Initializes the ICD10DatabaseTool with a pre-loaded ICD-10 database.

        Args:
            database_path (str): Path to the CSV file containing the ICD-10 database.
            **kwargs: Additional arguments to pass to the BaseTool initializer.
        """
        super().__init__(**kwargs)
        self._database = pd.read_csv(database_path)

    def _run(self, code: str = None, description: str = None) -> Dict:
        """
        Executes the tool with the provided code or description.

        Args:
            code (str, optional): The ICD-10 code to validate.
            description (str, optional): The ICD-10 description to search for.

        Returns:
            Dict: A dictionary containing the validation result. Keys include:
                - `valid` (bool): Whether the code or description was found.
                - `matches` (list): Matching records (if description provided).
                - Additional metadata such as code, description, URL, and chapter.

        Raises:
            ValueError: If neither 'code' nor 'description' is provided.
        """
        if code:
            match = self._database[self._database["sub-code"] == code]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "valid": True,
                    "code": code,
                    "description": row["definition"],
                    "url": row["url"],
                    "chapter": row["chapter"],
                }
            return {"valid": False, "code": code, "note": "Code not found"}
        elif description:
            matches = self._database[
                self._database["definition"].str.contains(description, case=False, na=False)
            ]
            results = matches[["sub-code", "definition", "url", "chapter"]].to_dict("records")
            if not results:
                # Perform similarity search (fallback)
                results = self._find_similar_descriptions(description)
            return {"valid": len(results) > 0, "matches": results}
        else:
            raise ValueError("Either 'code' or 'description' must be provided.")

    def _find_similar_descriptions(self, description: str) -> List[Dict]:
        """
        Finds similar descriptions using a fuzzy matching algorithm.

        Args:
            description (str): The ICD-10 description to match.

        Returns:
            List[Dict]: A list of dictionaries containing matched records from the database.
        """
        from difflib import get_close_matches
        all_descriptions = self._database["definition"].dropna().tolist()
        similar_descriptions = get_close_matches(description, all_descriptions, n=5, cutoff=0.6)
        results = self._database[self._database["definition"].isin(similar_descriptions)]
        return results[["sub-code", "definition", "url", "chapter"]].to_dict("records")
