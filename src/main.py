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