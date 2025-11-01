"""Configuration data models for SQLite storage."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


@dataclass
class AgentConfig:
    """Agent configuration data model."""

    agent_id: str
    name: str
    model_id: Optional[str] = None
    model_provider: Optional[str] = None
    model_kwargs: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    knowledge: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    guardrails: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    user_id: Optional[str] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model_id": self.model_id,
            "model_provider": self.model_provider,
            "model_kwargs": self.model_kwargs,
            "instructions": self.instructions,
            "tools": self.tools,
            "knowledge": self.knowledge,
            "memory": self.memory,
            "guardrails": self.guardrails,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create from dictionary."""
        return cls(
            agent_id=data.get("agent_id", str(uuid4())),
            name=data.get("name", ""),
            model_id=data.get("model_id"),
            model_provider=data.get("model_provider"),
            model_kwargs=data.get("model_kwargs"),
            instructions=data.get("instructions"),
            tools=data.get("tools"),
            knowledge=data.get("knowledge"),
            memory=data.get("memory"),
            guardrails=data.get("guardrails"),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            user_id=data.get("user_id"),
            status=data.get("status", "active"),
        )


@dataclass
class ToolConfig:
    """Tool configuration data model."""

    tool_id: str
    name: str
    function_definition: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    agent_id: Optional[str] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "function_definition": self.function_definition,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolConfig":
        """Create from dictionary."""
        return cls(
            tool_id=data.get("tool_id", str(uuid4())),
            name=data.get("name", ""),
            function_definition=data.get("function_definition", {}),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            agent_id=data.get("agent_id"),
            status=data.get("status", "active"),
        )


class ModelConfig(BaseModel):
    """Model configuration data model."""

    model_id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human readable model name")
    provider: str = Field(..., description="Model provider (e.g., 'openai', 'anthropic')")
    model_name: str = Field(..., description="Actual model name (e.g., 'gpt-4', 'claude-3')")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Model configuration parameters")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    pricing: Optional[Dict[str, Any]] = Field(None, description="Pricing information")
    limits: Optional[Dict[str, Any]] = Field(None, description="Rate limits and usage limits")
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "kwargs": self.kwargs,
            "capabilities": self.capabilities,
            "pricing": self.pricing,
            "limits": self.limits,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """Create from dictionary."""
        return cls(**data)