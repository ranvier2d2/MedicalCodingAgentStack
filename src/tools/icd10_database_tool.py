# src/referencecrew/tools/icd10_database_tool.py

from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import pandas as pd

class ICD10DatabaseToolInput(BaseModel):
    """Input schema for ICD10DatabaseTool."""
    code: str = Field(None, description="ICD-10 code to validate.")
    description: str = Field(None, description="ICD-10 description to search.")

class ICD10DatabaseTool(BaseTool):
    name: str = "icd10_database_tool"
    description: str = (
        "Validates ICD-10 codes or matches descriptions against a pre-loaded ICD-10 database."
    )
    args_schema: Type[BaseModel] = ICD10DatabaseToolInput

    def __init__(self, database_path: str, **kwargs):
        super().__init__(**kwargs)
        self._database = pd.read_csv(database_path)

    def _run(self, code: str = None, description: str = None) -> Dict:
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
            return {"valid": len(results) > 0, "matches": results}
        else:
            raise ValueError("Either 'code' or 'description' must be provided.")
