Here’s an updated version of the AgentStack API Documentation, incorporating improvements for clarity and any relevant changes:

AgentStack API Documentation

This document provides a comprehensive guide to using the AgentStack API, detailing available endpoints and their functionality for interacting with the backend system.

Base URL

The API is hosted locally for development purposes at:

http://127.0.0.1:8000

Endpoints

1. Start a New Task

POST /run

This endpoint initializes a new CrewAI task based on the provided input.

Request
	•	URL: /run
	•	Method: POST
	•	Headers: Content-Type: application/json
	•	Body:

{
    "diagnosis_text": "<description of the diagnosis>"
}

Example:

{
    "diagnosis_text": "Seizures, Depression, Migraine"
}



Response
	•	200 OK

{
    "task_id": "<unique-task-id>"
}

Example:

{
    "task_id": "123e4567-e89b-12d3-a456-426614174000"
}


	•	Notes:
	•	Use the task_id from the response to track the task’s status using the /status/{task_id} endpoint.

2. Query Task Status

GET /status/{task_id}

This endpoint provides the current status of a task, including intermediate results (partials) and the final output once available.

Request
	•	URL: /status/{task_id}
	•	Method: GET
	•	Path Parameter:
	•	task_id (string): The unique identifier of the task returned from /run.

Response
	•	200 OK (Running Task):

{
    "status": "running",
    "result": null,
    "partials": [
        {
            "subtask_name": "<subtask name>",
            "output": "<intermediate result>",
            "details": "<additional details>",
            "timestamp": "<timestamp>"
        }
    ],
    "progress_summary": "<completed subtasks>/<total subtasks> subtasks completed",
    "error": null
}

Example:

{
    "status": "running",
    "result": null,
    "partials": [
        {
            "subtask_name": "medical_diagnosis_task",
            "output": "<structured JSON output>",
            "details": null,
            "timestamp": "2024-12-30T01:37:08.923607"
        }
    ],
    "progress_summary": "1/3 subtasks completed",
    "error": null
}


	•	200 OK (Completed Task):

{
    "status": "completed",
    "result": "<final structured JSON output>",
    "partials": [],
    "progress_summary": "3/3 subtasks completed",
    "error": null
}


	•	404 Not Found:

{
    "detail": "Task not found"
}


	•	Notes:
	•	The partials field contains real-time updates for completed subtasks.
	•	Use the progress_summary field to display the completion status of the task.

Frontend Integration

1. Starting a Task
	•	Send a POST /run request with the diagnosis_text payload.
	•	Store the returned task_id for querying task progress.

2. Polling for Status
	•	Use GET /status/{task_id} with the task_id from /run to check progress.
	•	Recommended polling interval: 2-5 seconds.
	•	Display the following in the UI:
	•	Intermediate results (partials).
	•	Progress information from progress_summary.

3. Handling Completed Tasks
	•	Show the result field when the task status is completed.

4. Error Handling
	•	Check the error field in responses.
	•	Handle 404 errors gracefully when a task is not found (e.g., expired task ID).

Workflow Summary
	1.	Start a New Task:
	•	Initiate a task using POST /run.
	•	Retrieve the task_id from the response.
	2.	Monitor Progress:
	•	Periodically poll GET /status/{task_id} to monitor task status.
	•	Update the UI with intermediate results (partials) and progress.
	3.	Display Final Output:
	•	Render the result field once the task is completed.

Sample Code for API Usage

Using Python (Requests Library)

import requests
import time

# Step 1: Start a new task
base_url = "http://127.0.0.1:8000"
task_data = {"diagnosis_text": "Seizures, Depression, Migraine"}
response = requests.post(f"{base_url}/run", json=task_data)
task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Step 2: Poll for task status
status_url = f"{base_url}/status/{task_id}"
while True:
    status_response = requests.get(status_url)
    task_status = status_response.json()

    print(f"Task Status: {task_status['status']}")
    print(f"Progress: {task_status['progress_summary']}")

    if task_status["status"] == "completed":
        print("Final Result:", task_status["result"])
        break
    elif task_status["status"] == "failed":
        print("Error:", task_status["error"])
        break

    time.sleep(5)

Contact and Support
	•	For assistance, please contact the development team.
	•	Access the API’s Swagger interface for further details at /docs.

This updated documentation clarifies usage and improves accessibility for developers integrating with the API. Let me know if further refinements are needed!