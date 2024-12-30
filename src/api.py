import logging
import os
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import agentops
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from crew import AstackcrewCrew

# Suppress OpenTelemetry warnings
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# ------------------------------------------------------------------------------
# 1) Configure Logging and FastAPI
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentStack API")

# Add CORS middleware (configure origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 2) AgentOps Configuration
# ------------------------------------------------------------------------------
# Note: AgentOps initialization is now done per-task in run_crew_task() instead of globally.
# This allows each task to have its own independent session with proper start/end timing.

# ------------------------------------------------------------------------------
# 3) Pydantic Models
# ------------------------------------------------------------------------------
class RunInput(BaseModel):
    """Data required to start the Crew process."""
    diagnosis_text: str

class TaskStatus(BaseModel):
    """Track the status of a Crew run: partial results, final result, etc."""
    status: str  # "running", "completed", or "failed"
    result: Dict[str, Any] | str | None = None
    partials: list[Dict[str, Any]] = []
    error: str | None = None
    progress_summary: str | None = None

# ------------------------------------------------------------------------------
# 4) In-Memory Task Storage
# ------------------------------------------------------------------------------
tasks: Dict[str, TaskStatus] = {}

# ------------------------------------------------------------------------------
# 5) Subtask Callback
# ------------------------------------------------------------------------------
def create_crew_task_callback(task_id: str):
    """
    Returns a function that CrewAI will call once each subtask finishes,
    allowing us to capture partial results in the global 'tasks' dict.
    """
    def crew_task_callback(task_result):
        logger.info(f"[{task_id}] Subtask output: {task_result.__dict__}")

        current_status = tasks.get(task_id)
        if not current_status:
            current_status = TaskStatus(status="running")
            tasks[task_id] = current_status

        partial = {
            "subtask_name": getattr(task_result, "name", "unknown_task"),
            "output": getattr(task_result, "raw", "No raw output"),
            "details": getattr(task_result, "json_dict", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
        current_status.partials.append(partial)
        logger.info(f"[{task_id}] Added partial: {partial}")

    return crew_task_callback

# ------------------------------------------------------------------------------
# 6) Background Task
# ------------------------------------------------------------------------------
def run_crew_task(task_id: str, inputs: Dict[str, Any]):
    """
    Launches the Crew in single-session mode. 
    Each task gets its own AgentOps session that starts when the task starts
    and ends when the task completes or fails.
    """
    logger.info(f"[{task_id}] Starting background run in single-session mode.")

    try:
        # Build the Crew
        crew_obj = AstackcrewCrew().crew()
        crew_obj.task_callback = create_crew_task_callback(task_id)

        # Kick it off
        result = crew_obj.kickoff(inputs=inputs)
        final_str = getattr(result, "raw", str(result))

        # Mark success
        tasks[task_id].status = "completed"
        tasks[task_id].result = final_str
        logger.info(f"[{task_id}] Crew completed successfully.")

    except Exception as e:
        # Mark failure if an error occurs
        logger.error(f"[{task_id}] Error in run_crew_task: {e}")
        tasks[task_id] = TaskStatus(status="failed", error=str(e))

    # finally:
    #     # End the session with AgentOps
    #     end_state = "Success" if tasks[task_id].status == "completed" else "Fail"
    #     try:
    #         agentops.end_session(
    #             end_state=end_state,
    #             end_state_reason=f"Task {task_id} ended with status={tasks[task_id].status}"
    #         )
    #         logger.info(f"[{task_id}] agentops.end_session called with end_state={end_state}.")
    #     except Exception as e:
    #         logger.error(f"[{task_id}] Error ending AgentOps session: {e}")

# ------------------------------------------------------------------------------
# 7) API Endpoint to Launch Crew
# ------------------------------------------------------------------------------
@app.post("/run")
async def run_crew_endpoint(inputs: RunInput, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    POST /run
    Body: { "diagnosis_text": "some text" }
    Returns: { "task_id": "<uuid>" }
    """

    task_id = str(uuid4())
    logger.info(f"[{task_id}] /run called - scheduling background task.")

    # Initialize task status and schedule background task first
    tasks[task_id] = TaskStatus(status="running")
    background_tasks.add_task(run_crew_task, task_id, inputs.model_dump())

    # Try to initialize AgentOps session (but continue even if it fails)
    try:
        # Initialize AgentOps for this endpoint request.
        tags = ["crewai", "agentstack", task_id]
        logger.debug(f"[{task_id}] Initializing AgentOps with tags: {tags}")
        agentops.init(
            default_tags=tags,
            #skip_auto_end_session=True,  # I commented out for testing purposes. 
            # DO NOT add other keys to agentops.init()!
        )
        logger.info(f"[{task_id}] Initialized AgentOps session with tags.")
    except Exception as e:
        logger.error(f"[{task_id}] Error initializing AgentOps session: {e}")
        

    return {"task_id": task_id}
# DO NOT end the session in this endpoint!
# ------------------------------------------------------------------------------
# 8) API Endpoint to Check Status
# ------------------------------------------------------------------------------
@app.get("/status/{task_id}")
async def get_status(task_id: str) -> TaskStatus:
    """
    GET /status/<task_id>
    Returns the TaskStatus with partials and final result.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    status_obj = tasks[task_id]

    # For a simple progress summary
    crew_obj = AstackcrewCrew().crew()
    total_subtasks = len(crew_obj.tasks)
    completed_subtasks = len(status_obj.partials)
    status_obj.progress_summary = f"{completed_subtasks}/{total_subtasks} subtasks completed"

    return status_obj

# ------------------------------------------------------------------------------
# 9) Final Note on Single-Session Concurrency
# ------------------------------------------------------------------------------
"""
Final Note: If You Actually Need True Single-Session At All Times
  • Ensure that you don’t start a second /run request while the first is still going.
    Because if you do, you’ll have two concurrent tasks → two sessions → multi-session mode triggered.
  • Alternatively, you can queue or block subsequent /run calls until the previous one finishes. That’s an
    app-level design choice.

Once you do that, you’ll be strictly single-session: no warnings, no confusion.
If concurrency is needed, consider a multi-session approach.
"""

# ------------------------------------------------------------------------------
# 10) Uvicorn Entry Point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)