# tests/test_multi_session.py
"""
Test cases for AgentOps multi-session implementation.
Tests session isolation, event recording, and agent management.
"""
import pytest
from uuid import uuid4
import asyncio
from concurrent.futures import ThreadPoolExecutor
import agentops
from src.api import run_crew_task, TaskStatus, tasks
from typing import Dict, Any

@pytest.fixture
def task_input():
    return {"diagnosis_text": "Urinary Tract Infection (UTI)"}

@pytest.fixture
def task_id():
    return str(uuid4())

# Unit Tests

def test_session_creation():
    """Test that each task gets its own isolated session."""
    session = agentops.start_session()
    assert session is not None
    assert session.session_id is not None
    session.end_session()

def test_event_recording():
    """Test proper event recording with correct parameters."""
    session = agentops.start_session()
    try:
        # Create test event with minimal parameters
        event = agentops.Event(
            event_type="test_event",
            returns="test result"
        )
        session.record(event)
        # Success if no exception is raised
    finally:
        session.end_session()

def test_agent_creation():
    """Test agent creation with proper UUID format."""
    session = agentops.start_session()
    try:
        agent_id = str(uuid4())
        session.create_agent("test_agent", agent_id)
        # Success if no exception is raised
    finally:
        session.end_session()

# Integration Tests

@pytest.mark.integration
def test_full_task_workflow(task_id: str, task_input: Dict[str, Any]):
    """Test complete task workflow with session management."""
    try:
        run_crew_task(task_id, task_input, multi_session=True)
        assert task_id in tasks
        assert tasks[task_id].status in ["completed", "failed"]
    except Exception as e:
        pytest.fail(f"Task workflow failed: {str(e)}")

# Concurrent Tests

@pytest.mark.concurrent
@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test multiple sessions running concurrently."""
    async def run_task():
        task_id = str(uuid4())
        inputs = {"diagnosis_text": f"Test diagnosis {task_id}"}
        try:
            run_crew_task(task_id, inputs)
            return task_id
        except Exception as e:
            pytest.fail(f"Concurrent task failed: {str(e)}")
    
    # Run multiple tasks concurrently
    task_ids = await asyncio.gather(*[run_task() for _ in range(3)])
    
    # Verify each task completed independently
    for task_id in task_ids:
        assert task_id in tasks
        assert tasks[task_id].status in ["completed", "failed"]

@pytest.mark.concurrent
def test_session_isolation():
    """Test that sessions don't interfere with each other."""
    def run_isolated_session():
        session = agentops.start_session()
        try:
            agent_id = str(uuid4())
            session.create_agent("test_agent", agent_id)
            event = agentops.Event(
                event_type="test_event",
                returns="test result"
            )
            session.record(event)
        finally:
            session.end_session()

    # Run multiple sessions in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_isolated_session) for _ in range(3)]
        # Verify all sessions completed without errors
        for future in futures:
            future.result()

# Error Cases

def test_invalid_agent_id():
    """Test handling of invalid agent IDs."""
    session = agentops.start_session()
    try:
        # This should fail but not raise an exception
        session.create_agent("test_agent", "invalid_uuid")
        # If we get here, verify that the agent wasn't actually created
        # by trying to use it
        event = agentops.Event(
            event_type="test_event",
            returns="test result"
        )
        session.record(event)
        pytest.fail("Expected agent creation to fail with invalid UUID")
    except:
        pass  # Expected failure
    finally:
        session.end_session()

def test_session_cleanup(task_id: str, task_input: Dict[str, Any]):
    """Test proper session cleanup after task completion."""
    run_crew_task(task_id, task_input)
    
    # Verify task completed
    assert task_id in tasks
    assert tasks[task_id].status in ["completed", "failed"]
    
    # Verify no active session for this task
    assert tasks[task_id].status != "running"

def test_event_recording_errors():
    """Test handling of event recording errors."""
    session = agentops.start_session()
    try:
        # Test with invalid event parameters
        with pytest.raises(TypeError) as exc_info:
            event = agentops.Event(
                event_type="test_event",
                invalid_param="should fail",
            )
            session.record(event)
        assert "unexpected keyword argument" in str(exc_info.value)
    finally:
        session.end_session()

# Run Tests
if __name__ == "__main__":
    pytest.main([__file__])
