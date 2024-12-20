import json
import sys
from datetime import datetime
from crew import AstackcrewCrew
import agentops
import logging

# Initialize AgentOps with default tags
agentops.init(default_tags=['crewai', 'agentstack'])

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run():
    """
    Run the crew with default inputs.
    """
    logging.info("Starting the crew...")
    inputs = {
        "diagnosis_text": "Chronic Fatigue Syndrome, Down Syndrome, Marfan Syndrome, CHARGE syndrome, Cushing's syndrome",
    }
    try:
        result = AstackcrewCrew().crew().kickoff(inputs=inputs)
        logging.info(f"Crew execution result: {result}")
    except Exception as e:
        logging.error(f"An error occurred during crew execution: {e}")
        raise

if __name__ == '__main__':
    """
    Default to running the crew when no command is specified.
    """
    try:
        run()
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user.")
        sys.exit(0)
