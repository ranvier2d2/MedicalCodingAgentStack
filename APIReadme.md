# AgentStack API Documentation

This document provides an overview of the AgentStack API, its endpoints, and how to use it to interact with the backend system.

---

## **Base URL**
The API is hosted locally for development at:
```
http://127.0.0.1:8000
```

---

## **Endpoints**

### **1. Start a New Task**
#### **POST /run**
Initiates a new CrewAI task with the provided input.

#### **Request**
- **URL**: `/run`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
    ```json
    {
        "diagnosis_text": "<diagnosis details>"
    }
    ```
    Example:
    ```json
    {
        "diagnosis_text": "Seizures, Depression, Migraine"
    }
    ```

#### **Response**
- **200 OK**
    ```json
    {
        "task_id": "<unique-task-id>"
    }
    ```
    Example:
    ```json
    {
        "task_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    ```
- **Notes**:
    - Use the `task_id` to query the status of the task.

---

### **2. Query Task Status**
#### **GET /status/{task_id}**
Retrieves the status of a task, including partial outputs and the final result.

#### **Request**
- **URL**: `/status/{task_id}`
- **Method**: `GET`
- **Path Parameter**:
    - `task_id` (string): The unique ID of the task returned from `/run`.

#### **Response**
- **200 OK** (Running Task):
    ```json
    {
        "status": "running",
        "result": null,
        "partials": [
            {
                "subtask_name": "<subtask name>",
                "output": "<subtask output>",
                "details": "<additional details>",
                "timestamp": "<timestamp>"
            }
        ],
        "progress_summary": "<completed subtasks>/<total subtasks> subtasks completed",
        "error": null
    }
    ```
    Example:
    ```json
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
    ```
- **200 OK** (Completed Task):
    ```json
    {
        "status": "completed",
        "result": "<final structured JSON output>",
        "partials": [
            {
                "subtask_name": "<subtask name>",
                "output": "<subtask output>",
                "details": "<additional details>",
                "timestamp": "<timestamp>"
            }
        ],
        "progress_summary": "<completed subtasks>/<total subtasks> subtasks completed",
        "error": null
    }
    ```
    Example:
    ```json
    {
        "status": "completed",
        "result": "<final structured JSON output>",
        "partials": [],
        "progress_summary": "3/3 subtasks completed",
        "error": null
    }
    ```
- **404 Not Found**:
    ```json
    {
        "detail": "Task not found"
    }
    ```
- **Notes**:
    - The `partials` array includes real-time updates for each subtask.
    - The `progress_summary` tracks the number of completed subtasks.

---

## **Frontend Integration Tips**

### **Starting a New Task**
1. **Send a POST request to `/run`**:
    - Include the diagnosis text as input.
    - Store the returned `task_id` for querying progress.

### **Polling for Status**
1. **Send a GET request to `/status/{task_id}`**:
    - Use the `task_id` from the `/run` response.
    - Poll every 2-5 seconds to check the task's progress.

2. **Display Real-Time Updates**:
    - Use the `partials` field to show intermediate results.
    - Show progress using `progress_summary`.

3. **Handle Completed Tasks**:
    - Render the `result` field once the `status` is `completed`.

### **Error Handling**
- Check for `error` in the response and display it to users if present.
- Handle 404 errors gracefully if the `task_id` is invalid or expired.

---

## **API Workflow**

1. **Start a Task**:
    - Send a `POST /run` request.
    - Receive the `task_id`.

2. **Monitor Progress**:
    - Send `GET /status/{task_id}` requests periodically.
    - Display `partials` and `progress_summary` to users.

3. **Display Final Output**:
    - Show the `result` field when the task is `completed`.

---

## **Sample Code for API Usage**

### **Using Python (Requests Library)**
```python
import requests
import time

# Start a new task
url = "http://127.0.0.1:8000/run"
input_data = {"diagnosis_text": "Seizures, Depression, Migraine"}
response = requests.post(url, json=input_data)
task_id = response.json().get("task_id")

# Poll for task status
status_url = f"http://127.0.0.1:8000/status/{task_id}"
while True:
    status_response = requests.get(status_url)
    status_data = status_response.json()

    print(f"Status: {status_data['status']}")
    print(f"Progress: {status_data['progress_summary']}")

    if status_data['status'] == "completed":
        print("Final Result:", status_data['result'])
        break
    elif status_data['status'] == "failed":
        print("Error:", status_data['error'])
        break

    time.sleep(5)
```

---

## **Contact and Support**
If you encounter issues or have questions, please contact the development team or refer to the API documentation provided at `/docs` (FastAPI's Swagger interface).

