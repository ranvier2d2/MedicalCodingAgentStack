import json
import sys
from datetime import datetime
from crew import AstackcrewCrew
import agentops
import logging

# Initialize AgentOps with default tags
agentops.init(default_tags=['crewai', 'agentstack'])

# Configure logging
def run():
    logging.info("Starting the crew...")
    try:
        result = AstackcrewCrew().crew().kickoff(
            inputs={"diagnosis_text": "Seizures, Depression, Migraine"}
        )
        logging.info(f"Crew execution result: {result}")
    except Exception as e:
        logging.error(f"An error occurred during crew execution: {e}")
        raise

    # Example 2: General Symptoms
    # inputs = {
    #     "diagnosis_text": "Fever, Cough, Fatigue"
    # }

    # Example 3: Musculoskeletal and Pain-Related Conditions
    # inputs = {
    #     "diagnosis_text": "Lower Back Pain, Osteoarthritis, Fibromyalgia"

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
    }
    try:
        CptcrewCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CptcrewCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
    }
    try:
        CptcrewCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}") 


if __name__ == '__main__':
    """
    Default to running the crew when no command is specified.
    """
    try:
        run()
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user.")
        sys.exit(0)
