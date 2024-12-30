import logging
from typing import Dict, Any
from uuid import uuid4

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import agentops

from crew import AstackcrewCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentStack API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class RunInput(BaseModel):
    diagnosis_text: str

class TaskStatus(BaseModel):
    status: str
    result: Dict[str, Any] | str | None = None
    error: str | None = None

# Store for tracking running tasks
tasks: Dict[str, TaskStatus] = {}

def run_crew_task(task_id: str, inputs: Dict[str, Any]):
    """Background task to run the crew"""
    try:
        logger.info(f"Starting crew task {task_id}")
        result = AstackcrewCrew().crew().kickoff(inputs=inputs)
        result_content = result.raw if hasattr(result, 'raw') else str(result)
        tasks[task_id] = TaskStatus(
            status="completed",
            result=result_content
        )
        logger.info(f"Crew task {task_id} completed successfully")
    except Exception as e:
        logger.error(f"Error in crew task {task_id}: {str(e)}")
        tasks[task_id] = TaskStatus(
            status="failed",
            error=str(e)
        )
        raise

@app.post("/run")
async def run_crew(
    inputs: RunInput,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Run the crew with the provided diagnosis text
    Returns a task ID that can be used to check the status.
    """
    task_id = str(uuid4())
    logger.info(f"Creating new task with ID: {task_id}")
    tasks[task_id] = TaskStatus(status="running")
    
    # Initialize AgentOps with skip_auto_end_session
    agentops.init(default_tags=['crewai', 'agentstack'], skip_auto_end_session=True)
    
    # Execute the task
    background_tasks.add_task(run_crew_task, task_id, inputs.dict())
    
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str) -> TaskStatus:
    """Get the status of a running task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_status = tasks[task_id]
    
    # End AgentOps session if task is complete
    if task_status.status in ["completed", "failed"]:
        agentops.end_session('Success' if task_status.status == "completed" else 'Failure')
    
    return task_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
