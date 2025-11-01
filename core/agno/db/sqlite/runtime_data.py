"""Runtime data models for SQLite storage."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class RuntimeData:
    """Runtime execution data model."""

    run_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    status: str = "running"  # running, completed, failed, cancelled
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "reasoning_steps": self.reasoning_steps,
            "tool_calls": self.tool_calls,
            "metrics": self.metrics,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeData":
        """Create from dictionary."""
        return cls(
            run_id=data.get("run_id", str(uuid4())),
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id"),
            user_id=data.get("user_id"),
            input_data=data.get("input_data"),
            output_data=data.get("output_data"),
            reasoning_steps=data.get("reasoning_steps"),
            tool_calls=data.get("tool_calls"),
            metrics=data.get("metrics"),
            status=data.get("status", "running"),
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class ReasoningStep:
    """Individual reasoning step data model."""

    step_id: str
    run_id: str
    step_type: str  # "thinking", "tool_call", "observation", etc.
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None
    duration: Optional[float] = None
    token_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "run_id": self.run_id,
            "step_type": self.step_type,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningStep":
        """Create from dictionary."""
        return cls(
            step_id=data.get("step_id", str(uuid4())),
            run_id=data.get("run_id"),
            step_type=data.get("step_type", ""),
            content=data.get("content"),
            data=data.get("data"),
            timestamp=data.get("timestamp"),
            duration=data.get("duration"),
            token_count=data.get("token_count"),
        )


@dataclass
class ToolCallRecord:
    """Tool call execution record."""

    call_id: str
    run_id: str
    tool_name: str
    tool_args: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    duration: Optional[float] = None
    status: str = "running"  # running, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "run_id": self.run_id,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCallRecord":
        """Create from dictionary."""
        return cls(
            call_id=data.get("call_id", str(uuid4())),
            run_id=data.get("run_id"),
            tool_name=data.get("tool_name", ""),
            tool_args=data.get("tool_args"),
            result=data.get("result"),
            error=data.get("error"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration=data.get("duration"),
            status=data.get("status", "running"),
        )