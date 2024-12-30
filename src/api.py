import logging
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import agentops

from crew import AstackcrewCrew

# ------------------------------------------------------------------------------
# 1) Configure Logging and FastAPI Application
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentStack API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 2) Define Pydantic Models
# ------------------------------------------------------------------------------
class RunInput(BaseModel):
    """Model for input data when starting a CrewAI run."""
    diagnosis_text: str

class TaskStatus(BaseModel):
    """Model to track status and output of a CrewAI task."""
    status: str  # "running", "completed", or "failed"
    result: Dict[str, Any] | str | None = None
    partials: list[Dict[str, Any]] = []
    error: str | None = None
    progress_summary: str | None = None

# ------------------------------------------------------------------------------
# 3) In-memory Task Storage
# ------------------------------------------------------------------------------
tasks: Dict[str, TaskStatus] = {}

# ------------------------------------------------------------------------------
# 4) Create the Callback for Subtask Updates
# ------------------------------------------------------------------------------
def create_crew_task_callback(task_id: str):
    """
    Returns a callback function that updates the 'tasks' dictionary with partial
    results whenever a CrewAI subtask is completed.
    """
    def crew_task_callback(task_result):
        logger.info(f"TaskOutput for task_id={task_id}: {task_result.__dict__}")

        current_task_status = tasks.get(task_id)
        if not current_task_status:
            current_task_status = TaskStatus(status="running")
            tasks[task_id] = current_task_status

        partial_update = {
            "subtask_name": getattr(task_result, "name", "unknown_task"),
            "output": getattr(task_result, "raw", "No raw output"),
            "details": getattr(task_result, "json_dict", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
        current_task_status.partials.append(partial_update)
        logger.info(f"Updated task {task_id} with partial: {partial_update}")

    return crew_task_callback

# ------------------------------------------------------------------------------
# 5) The Background Task That Runs the Crew
# ------------------------------------------------------------------------------
def run_crew_task(task_id: str, inputs: Dict[str, Any]):
    """
    Executes the Crew in the background. Starts and ends a single AgentOps session
    for this task only.
    """
    logger.info(f"Starting crew task {task_id} in single-session mode")
    
    # 5a) Start a single AgentOps session specifically for this run.
    # As soon as we do this, if there's another session running concurrently,
    # AgentOps will detect multiple sessions. But if you run them one at a time,
    # you'll remain in single-session mode.
    agentops.init(default_tags=["crewai", "agentstack"], skip_auto_end_session=True)

    try:
        # 5b) Build the Crew object
        crew_obj = AstackcrewCrew().crew()
        crew_obj.task_callback = create_crew_task_callback(task_id)

        # 5c) Kick off the Crew
        result = crew_obj.kickoff(inputs=inputs)

        # 5d) Mark completion
        result_content = getattr(result, "raw", str(result))
        tasks[task_id].status = "completed"
        tasks[task_id].result = result_content
        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        # 5e) If there's an error, store it
        logger.error(f"Error in task {task_id}: {e}")
        tasks[task_id] = TaskStatus(status="failed", error=str(e))

    finally:
        # 5f) End the session after the task is done (success or failure)
        final_state = "Success" if tasks[task_id].status == "completed" else "Fail"
        agentops.end_session(end_state=final_state)
        logger.info(f"AgentOps session ended for task {task_id}")

# ------------------------------------------------------------------------------
# 6) Endpoint to Start a New Crew Task
# ------------------------------------------------------------------------------
@app.post("/run")
async def run_crew(inputs: RunInput, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Starts a new Crew run (and implicitly an AgentOps session),
    returning a unique task ID that can be polled for status.
    """
    task_id = str(uuid4())
    logger.info(f"Creating new task with ID: {task_id}")

    tasks[task_id] = TaskStatus(status="running")

    # Schedule the background job
    background_tasks.add_task(run_crew_task, task_id, inputs.dict())
    
    return {"task_id": task_id}

# ------------------------------------------------------------------------------
# 7) Endpoint to Check Status
# ------------------------------------------------------------------------------
@app.get("/status/{task_id}")
async def get_status(task_id: str) -> TaskStatus:
    """
    Polls the status of a given task (running, completed, or failed).
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    # Optionally, we can show progress by comparing partials to total tasks
    task_status = tasks[task_id]
    # For a quick example, assume we have 3 tasks in your Crew:
    crew_obj = AstackcrewCrew().crew()
    total_subtasks = len(crew_obj.tasks)
    completed_subtasks = len(task_status.partials)
    task_status.progress_summary = f"{completed_subtasks}/{total_subtasks} subtasks completed"

    return task_status

# ------------------------------------------------------------------------------
# 8) Main Entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)