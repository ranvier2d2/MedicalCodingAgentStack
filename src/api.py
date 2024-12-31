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
from threading import Lock

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
ops_initialized = False
first_run = True

def maybe_init_agentops():
    """Initialize AgentOps on-demand if not already done."""
    global ops_initialized
    if not ops_initialized:
        agentops.init()
        logger.info("AgentOps initialized on-demand.")
        ops_initialized = True

def get_or_create_session(multi_session: bool = False) -> Optional[agentops.Session]:
    """Get existing session or create new one based on mode."""
    global first_run
    
    # Always ensure AgentOps is initialized
    maybe_init_agentops()
    
    if multi_session:
        # In multi-session mode, always create a new session with agents
        session = agentops.start_session()
        session.create_agent("medical_coder", str(uuid4()))
        session.create_agent("validation_agent", str(uuid4()))
        session.create_agent("reporting_agent", str(uuid4()))
        logger.info("Created new session with agents for multi-session mode")
        return session
    
    # In single-session mode:
    if first_run:
        # First run doesn't need start_session()
        first_run = False
        return None
    else:
        # Subsequent runs need a new session
        session = agentops.start_session()
        logger.info("Created new session for subsequent single-session mode run")
        return session

# ------------------------------------------------------------------------------
# 3) Pydantic Models
# ------------------------------------------------------------------------------
class RunInput(BaseModel):
    """Data required to start the Crew process."""
    diagnosis_text: str

class PartialResult(BaseModel):
    """Partial result of a Crew run."""
    subtask_name: str
    output: str
    details: Any | None
    timestamp: str

class TaskStatus(BaseModel):
    """Track the status of a Crew run: partial results, final result, etc."""
    status: str  # "running", "completed", or "failed"
    result: str | None
    error: str | None
    progress_summary: str
    partials: list[PartialResult]

# ------------------------------------------------------------------------------
# 4) In-Memory Task Storage
# ------------------------------------------------------------------------------
tasks: Dict[str, TaskStatus] = {}
tasks_lock = Lock()  # Lock for thread-safe access to tasks dict

# Cache for crew configuration
TOTAL_SUBTASKS = len(AstackcrewCrew().crew().tasks)

def is_task_running(task_id: str) -> bool:
    """Check if a task is currently running."""
    with tasks_lock:
        return task_id in tasks and tasks[task_id].status == "running"

def update_task_status(task_id: str, status_update: Dict[str, Any]) -> None:
    """Thread-safe update of task status."""
    with tasks_lock:
        if task_id not in tasks:
            tasks[task_id] = TaskStatus(
                status="running",
                result=None,
                error=None,
                progress_summary="0/0 subtasks completed",
                partials=[]
            )
        task_status = tasks[task_id]
        for key, value in status_update.items():
            setattr(task_status, key, value)

# ------------------------------------------------------------------------------
# 5) Subtask Callback
# ------------------------------------------------------------------------------
def create_crew_task_callback(task_id: str, session_id: str | None = None):
    """
    Returns a function that CrewAI will call once each subtask finishes,
    allowing us to capture partial results in the global 'tasks' dict.
    """
    def crew_task_callback(task_result):
        if session_id:
            try:
                session = agentops.get_session(session_id)
                record_subtask_event(task_id, "medical_coder", "subtask_complete", task_result.__dict__["raw"])
            except Exception as e:
                logger.error(f"[{task_id}] Error recording subtask event: {e}")
        logger.info(f"[{task_id}] Subtask output: {task_result.__dict__}")

        update_task_status(task_id, {
            "partials": tasks[task_id].partials + [
                PartialResult(
                    subtask_name=getattr(task_result, "name", "unknown_task"),
                    output=getattr(task_result, "raw", "No raw output"),
                    details=getattr(task_result, "json_dict", None),
                    timestamp=datetime.utcnow().isoformat(),
                )
            ]
        })
        logger.info(f"[{task_id}] Added partial: {tasks[task_id].partials[-1]}")

    return crew_task_callback

def record_subtask_event(task_id: str, agent_name: str, event_type: str, content: str):
    """Record a subtask event."""
    try:
        params = {
            "task_id": task_id,
            "agent_name": agent_name,
            "content": content
        }
        event = agentops.Event(
            event_type=event_type,
            params=params,
            returns=None  # No return value for these events
        )
        agentops.record(event)
        logger.info(f"Recorded {event_type} event for task {task_id}")
    except Exception as e:
        logger.error(f"[{task_id}] Error recording subtask event: {str(e)}")

# ------------------------------------------------------------------------------
# 6) Background Task
# ------------------------------------------------------------------------------
def run_crew_task(task_id: str, inputs: Dict[str, Any], multi_session: bool = False):
    """
    Launches the Crew with configurable session handling.
    Supports both multi-session (for testing) and single-session modes.
    """
    logger.info(f"[{task_id}] Starting background run (multi_session={multi_session})")
    session = get_or_create_session(multi_session)

    try:
        # Build and run the Crew
        crew_obj = AstackcrewCrew().crew()
        crew_obj.task_callback = create_crew_task_callback(task_id, session.session_id if session else None)
        
        # Run crew and get result
        result = crew_obj.kickoff(inputs=inputs)
        
        # Record completion
        if session:
            event = agentops.Event(
                event_type="task_completion",
                params={"task_id": task_id},
                returns=getattr(result, "raw", str(result))
            )
            session.record(event)
        
        # Try to parse the final result as JSON if possible
        try:
            final_str = getattr(result, "raw", str(result))
            # Update task status
            update_task_status(task_id, {
                "status": "completed",
                "result": final_str,
                "error": None,
                "progress_summary": f"{TOTAL_SUBTASKS}/{TOTAL_SUBTASKS} subtasks completed"
            })
            logger.info(f"[{task_id}] Crew completed successfully with result: {final_str[:100]}...")
        except Exception as parse_error:
            logger.error(f"[{task_id}] Error parsing final result: {str(parse_error)}")
            update_task_status(task_id, {
                "status": "completed",
                "result": str(result),
                "error": None,
                "progress_summary": f"{TOTAL_SUBTASKS}/{TOTAL_SUBTASKS} subtasks completed"
            })

        # End session if in multi-session mode
        if session and multi_session:
            try:
                session.end_session(end_state="Success")
                logger.info(f"[{task_id}] Ended AgentOps session")
            except Exception as e:
                logger.error(f"[{task_id}] Error ending AgentOps session: {e}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{task_id}] Error in run_crew_task: {error_msg}")
        
        update_task_status(task_id, {
            "status": "failed",
            "result": None,
            "error": error_msg,
            "progress_summary": "Task failed"
        })

        if session and multi_session:
            try:
                session.end_session(end_state="Fail", end_state_reason=error_msg)
            except Exception as end_error:
                logger.error(f"[{task_id}] Error ending AgentOps session: {end_error}")

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
    logger.info(f"[{task_id}] /run called - scheduling background task")

    # Initialize task status
    update_task_status(task_id, {
        "status": "running",
        "result": None,
        "error": None,
        "progress_summary": f"0/{TOTAL_SUBTASKS} subtasks completed",
        "partials": []
    })

    # Use single-session mode for API calls
    background_tasks.add_task(run_crew_task, task_id, inputs.dict(), multi_session=False)

    return {"task_id": task_id}

# ------------------------------------------------------------------------------
# 8) API Endpoint to Check Status
# ------------------------------------------------------------------------------
@app.get("/status/{task_id}")
async def get_status(task_id: str) -> TaskStatus:
    """
    GET /status/<task_id>
    Returns the TaskStatus with partials and final result.
    """
    with tasks_lock:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        status_obj = tasks[task_id]
        
        # Update progress summary using cached total
        completed_subtasks = len(status_obj.partials)
        status_obj.progress_summary = f"{completed_subtasks}/{TOTAL_SUBTASKS} subtasks completed"
        
        return status_obj

# ------------------------------------------------------------------------------
# 9) Uvicorn Entry Point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)