from operator import truediv
from crewai import Agent, Crew, Process, Task
#from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput
import tools

# def has_unvalidated_codes(output: TaskOutput) -> bool:
#     """
#     Determines if the output contains unvalidated codes based on specific criteria.

#     :param output: TaskOutput object to evaluate
#     :return: True if unvalidated codes are found, otherwise False
#     """
#     if not hasattr(output, "json_dict") or not output.json_dict:
#         return False

#     return "unvalidated_codes" in output.json_dict and len(output.json_dict["unvalidated_codes"]) > 0


@CrewBase
class AstackcrewCrew:
    """A Crew setup for a medical diagnosis workflow with conditional task execution."""

    # Agent definitions
    @agent
    def medical_coder(self) -> Agent:
        return Agent(
            config=self.agents_config["medical_coder"],
            verbose=True,
            tools=[tools.gpt4_suggestion_tool],
        )

    @agent
    def validation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['validation_agent'],
            verbose=True,
            tools=[tools.icd10_database_tool],
        )
    @agent
    def reporting_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_agent'],
            verbose=True,
        )

    # Task definitions
    @task
    def medical_diagnosis_task(self) -> Task:
        return Task(
            config=self.tasks_config['medical_diagnosis_task'],
            async_execution=True
        )

    @task
    def validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['validation_task'],
            async_execution=True,  # Run synchronously to ensure proper data validation
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            async_execution=False,  # Run synchronously to ensure proper data validation
        )

    @crew
    def crew(self) -> Crew:
        """Defines the Crew workflow."""
        return Crew(
            agents=self.agents,  # Agents defined above
            tasks=self.tasks,  # Tasks defined above
            process=Process.sequential,  # Sequential execution for better control
            verbose=True,
            # merge_outputs=True  # Aggregate outputs from all tasks
        )
