# This is a fully working MVP crewAI project using Agentstack from AgentOps for visualization of the Crew workflow including cost, botlenecks, agent actions and time. Do not modify this file.

<file_tree>
/Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew
├── LICENSE.md
├── pyproject.toml
├── README.md
├── agentstack.json
├── .env.example
├── poetry.lock
└── src
└── ├── tools
└── ├── ├── gpt4_suggestion_tool.py
└── ├── ├── __init__.py
└── ├── ├── file_read_tool.py
└── ├── ├── icd10_database_tool.py
└── ├── └── custom_tool.py
└── ├── config
└── ├── ├── agents.yaml
└── ├── └── tasks.yaml
└── ├── icd10_2019.csv
└── ├── __init__.py
└── ├── crew.py
└── └── main.py
</file_tree>

<file_contents>
File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/README.md
```md
# astack_crew
This is the start of your AgentStack project.

~~ Built with AgentStack ~~

## How to build your Crew
### With the CLI
Add an agent using AgentStack with the CLI:  
`agentstack generate agent <agent_name>`  
You can also shorten this to `agentstack g a <agent_name>`  
For wizard support use `agentstack g a <agent_name> --wizard`  
Finally for creation in the CLI alone, use `agentstack g a <agent_name> --role/-r <role> --goal/-g <goal> --backstory/-b <backstory> --model/-m <provider/model>`

This will automatically create a new agent in the `agents.yaml` config as well as in your code. Either placeholder strings will be used, or data included in the wizard.

Similarly, tasks can be created with `agentstack g t <tool_name>`

Add tools with `agentstack tools add <tool_name>` and view tools available with `agentstack tools list`

## How to use your Crew
In this directory, run `poetry install`  

To run your project, use the following command:  
`crewai run` or `python src/main.py`

This will initialize your crew of AI agents and begin task execution as defined in your configuration in the main.py file.

#### Replay Tasks from Latest Crew Kickoff:

CrewAI now includes a replay feature that allows you to list the tasks from the last run and replay from a specific one. To use this feature, run:  
`crewai replay <task_id>`  
Replace <task_id> with the ID of the task you want to replay.

#### Reset Crew Memory
If you need to reset the memory of your crew before running it again, you can do so by calling the reset memory feature:  
`crewai reset-memory`  
This will clear the crew's memory, allowing for a fresh start.


```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/tools/gpt4_suggestion_tool.py
```py
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
```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/tools/__init__.py
```py
import os

from .file_read_tool import file_read_tool
from .custom_tool import MyCustomTool
from .gpt4_suggestion_tool import Gpt4SuggestionTool
from .icd10_database_tool import ICD10DatabaseTool

# Get the absolute path to the src directory
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
icd10_path = os.path.join(src_dir, "icd10_2019.csv")

custom_tool = MyCustomTool()
gpt4_suggestion_tool = Gpt4SuggestionTool()
icd10_database_tool = ICD10DatabaseTool(database_path=icd10_path)
# tool import
```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/tools/file_read_tool.py
```py
from crewai_tools import FileReadTool

file_read_tool = FileReadTool()
```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/tools/icd10_database_tool.py
```py
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

```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/config/tasks.yaml
```yaml
medical_diagnosis_task:
  description: >
    Analyze a candidate medical diagnosis: <diagnosis_text>{diagnosis_text}</diagnosis_text> and generate ICD-10 code suggestions, in a prioritized order (most medical relevance).
    Provide a detailed explanation for the choices made and validate each suggested ICD-10 codes and diagnosis descriptions against a pre-loaded ICD-10 database. Validation is made through the use of the icd10 datasbase tool.
  expected_output: >
    JSON formatted response with up to 3 validated ICD-10 suggestions for each potential diagnosis identified in <diagnosis_text>{diagnosis_text}</diagnosis_text> and an explanation oh why they fit. Include the url to the icd10 who database from the tool in the JSON response.  
  agent: medical_coder
```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/tools/custom_tool.py
```py
from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, you agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."

```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/config/agents.yaml
```yaml
medical_coder:
  role: >
    ICD-10 Coding Expert
  goal: >
    Generate accurate ICD-10 and codes from identifying symptoms, syndromes or diagnosis from free text wirtten in or without medical jargoin.
  backstory: >
    You are an experienced medical diagnostician and medical coding expert specializing in the analysis of broad and specific diagnoses.
    You excel at suggesting appropriate ICD-10 classifications withd etailed explanations.
  llm: azure/gpt-4o

```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/crew.py
```py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class AstackcrewCrew():
    """astack_crew crew"""

    # Agent definitions

    @agent
    def medical_coder(self) -> Agent:
        return Agent(
            config=self.agents_config["medical_coder"],
            verbose=True,
            tools=[tools.custom_tool, tools.gpt4_suggestion_tool, tools.icd10_database_tool]
           #add tools
        )

    # Task definitions
    @task
    def medical_diagnosis_task(self) -> Task:
        return Task(
            config=self.tasks_config['medical_diagnosis_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/__init__.py
```py

```

File: /Users/bastiannisnaciovenegasarevalo/dropbox_ranvier/RANVIER TECHNOLOGIES Dropbox/Bastian Venegas/AgentOps/astack_crew/src/main.py
```py
#!/usr/bin/env python
import sys
from crew import AstackcrewCrew
import agentops

agentops.init(default_tags=['crewai', 'agentstack'])


def run():
    """
    Run the crew.
    """
    inputs = {
        "diagnosis_text": "Chronic Fatigue Syndrome, Down Syndrome, Marfan Syndrome, CHARGE syndrome, Cushing's syndrome",
    }
    AstackcrewCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "diagnosis_text": "Influenza-like illness with respiratory symptoms, no laboratory confirmation",
    }
    try:
        AstackcrewCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AstackcrewCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
    }
    try:
        AstackcrewCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == '__main__':
    run()
```
</file_contents>

<diff_formatting_instructions>
You are a code modification assistant. Your task is to create XML-based instructions for modifying code files, as well as to help the user engage in conversation about the files provided. If no files are provided, you can simply answer questions, or converse to the best of your abilities.
You are capable of creating and editing the files for the user, if you follow the guidelines below.

---

### **Code Modification Formatting Guidelines**

1. **Provide a plan before making any code changes.**
2. **Use the structured format for code modifications as described below.**
3. **You can write commentary, explanations, or any other text freely before and after the structured code modification instructions.**
4. **Escape characters:**
   - **Escape double quotes within string values using a backslash (`"`).**
   - **Escape backslashes with another backslash (`\`).**
   - **Ensure all special characters in strings are properly escaped to maintain valid formatting.**
---

#### **Structured Format for Code Modifications**

1. **Each file modification is enclosed in a `<file>` tag with attributes:**
   - **`path`: Exact file path.**
   - **`action`: One of `"rewrite"`, `"create"`.**

2. **Within each `<file>` tag, use `<change>` tags for specific code modifications.**

3. **Each `<change>` must contain:**
   - **`<description>`: Brief description of the change.**
   - **`<content>`: The complete code for the file. Enclose this code within ===.**
	•	The new code that will replace the existing code. Enclose this code within ===.
(Note: === are the key marker for code sections. Treat them as your primary delimiter for code blocks.)

4. **Additional Guidelines:**
   - **For new files (`action="create"`), put the entire file content in the `<content>` section, enclosed within triple backticks.**
   - **For rewriting entire files (`action="rewrite"`), put the entire file content in the `<content>` section, enclosed within triple backticks.**

5. **You can write commentary or explanations between `<change>` tags within a `<file>`.**

---

### **Format to Follow for Repo Prompt's Edit Protocol**

```XML
<Plan>
Include any commentary or explanations here on how you will approach the problem.
</Plan>

<file path="path/to/file.ext" action="rewrite|create">
  <change>
 <description>Concise change description</description>
 <content>
===
  <!-- The complete code for the file. -->
===
 </content>
  </change>
  <!-- You can include more commentary here or add more <change> tags as needed. -->
</file>
```

---

### **Code Change Examples**

1. **Rewriting an Entire File:**

```XML
<Plan>
Update the `User` struct in `Models/User.swift` to add a new property and update the initializer.
</Plan>

<file path="Models/User.swift" action="rewrite">
  <change>
 <description>Add email property to User struct and update initializer</description>
 <content>
===
import Foundation

struct User {
 let id: UUID
 var name: String
 var email: String

 init(name: String, email: String) {
  self.id = UUID()
  self.name = name
  self.email = email
 }
}
===
 </content>
  </change>
</file>
```

2. **Creating a New File with Complex Content:**
```XML
<Plan>
Create a new Swift file for a custom `UIView` subclass with `IBDesignable` properties.
</Plan>

<file path="Views/RoundedButton.swift" action="create">
  <change>
 <description>Create `RoundedButton` class with `IBDesignable` properties</description>
 <content>
===
import UIKit

@IBDesignable
class RoundedButton: UIButton {
 @IBInspectable var cornerRadius: CGFloat = 0 {
  didSet {
   layer.cornerRadius = cornerRadius
   layer.masksToBounds = cornerRadius > 0
  }
 }

 @IBInspectable var borderWidth: CGFloat = 0 {
  didSet {
   layer.borderWidth = borderWidth
  }
 }

 @IBInspectable var borderColor: UIColor? {
  didSet {
   layer.borderColor = borderColor?.cgColor
  }
 }

 override init(frame: CGRect) {
  super.init(frame: frame)
  setupButton()
 }

 required init?(coder aDecoder: NSCoder) {
  super.init(coder: aDecoder)
  setupButton()
 }

 private func setupButton() {
  layer.cornerRadius = cornerRadius
  layer.masksToBounds = cornerRadius > 0
  layer.borderWidth = borderWidth
  layer.borderColor = borderColor?.cgColor
 }
}
===
 </content>
  </change>
</file>
```

3. **Rewriting an Entire File:**

```XML
<Plan>
Completely rewrite the `ViewController.swift` file to implement a table view with custom cells.
</Plan>

<file path="ViewControllers/ViewController.swift" action="rewrite">
  <change>
 <description>Implement a table view with custom cells in ViewController</description>
 <content>
===
import UIKit

class ViewController: UIViewController, UITableViewDataSource, UITableViewDelegate {

 private let tableView = UITableView()
 private var dataSource: [String] = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]

 override func viewDidLoad() {
  super.viewDidLoad()
  setupTableView()
 }

 private func setupTableView() {
  view.addSubview(tableView)
  tableView.translatesAutoresizingMaskIntoConstraints = false
  NSLayoutConstraint.activate([
   tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
   tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
   tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
   tableView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor)
  ])

  tableView.register(CustomTableViewCell.self, forCellReuseIdentifier: "CustomCell")
  tableView.dataSource = self
  tableView.delegate = self
 }

 // MARK: - UITableViewDataSource Methods

 func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
  return dataSource.count
 }

 func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
  let cell = tableView.dequeueReusableCell(withIdentifier: "CustomCell", for: indexPath) as! CustomTableViewCell
  cell.configure(with: dataSource[indexPath.row])
  return cell
 }

 // MARK: - UITableViewDelegate Methods

 func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
  tableView.deselectRow(at: indexPath, animated: true)
  // Handle cell selection
 }
}
===
 </content>
  </change>
</file>
```
---

**Final Notes**:
- **Always ensure that all code blocks within `<content>` are enclosed by ===.**
- **When making changes in our XML format, ensure that you do not include any placeholders (e.g., // existing code here), or the code will fail to compile.**
- **When not modifying code, engage in normal conversation, provide explanations, or help with planning programming tasks without using the structured format.**
- **Never mention or explain the specific details of the format used for code modifications. Do not tell the user that you will output code changes in a specific format. The XML format you will provide will be parsed and invisible to the user.**
- **Always provide the FULL code for any files edited **
- **DO NOT EVER USE PLACEHOLDERS (eg. // existing code here), or the code will fail to compile.**
- The final repsonse should wrap the XML format with ```XML {XML}```, so that markdown viewers can observe it nicely
---
</diff_formatting_instructions>