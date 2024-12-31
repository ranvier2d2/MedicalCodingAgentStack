# src/tools/__init__.py

import os


from .gpt4_suggestion_tool import Gpt4SuggestionTool
from .icd10_database_tool import ICD10DatabaseTool

# Get the absolute path to the src directory
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
icd10_path = os.path.join(src_dir, "icd10_2019.csv")

gpt4_suggestion_tool = Gpt4SuggestionTool()
icd10_database_tool = ICD10DatabaseTool(database_path=icd10_path)
# tool import