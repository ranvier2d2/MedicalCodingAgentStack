from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class AstackcrewCrew:
    """astack_crew crew"""

    # Agent definitions
    @agent
    def medical_coder(self) -> Agent:
        return Agent(
            config=self.agents_config["medical_coder"],
            verbose=True,
            tools=[tools.custom_tool, tools.gpt4_suggestion_tool, tools.icd10_database_tool],
        )

    # Task definitions
    @task
    def medical_diagnosis_task(self) -> Task:
        return Task(
            config=self.tasks_config['medical_diagnosis_task'],
            async_execution=True  # Enable asynchronous execution for parallel processing
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew with sequential process and async tasks."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,  # Sequential process with asynchronous tasks
            verbose=True,
        )