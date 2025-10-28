"""
Agent管理API接口
提供RESTful API用于Agent的增删改查操作
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from agent_manager import AgentCRUDManager
from agent_models import Agent, AgentType, AgentStatus
from models_mgr import ModelsManager
from db_mgr import DBManager


# Pydantic模型定义
class AgentCreateRequest(BaseModel):
    """创建Agent请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    agent_type: AgentType = Field(..., description="Agent类型")
    description: Optional[str] = Field(None, max_length=500, description="Agent描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    instructions: Optional[str] = Field(None, description="指令")
    additional_instructions: Optional[str] = Field(None, description="额外指令")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    tool_names: List[str] = Field(default_factory=list, description="工具名称列表")
    model_configuration_id: Optional[int] = Field(None, description="模型配置ID")
    enable_memory: bool = Field(default=False, description="是否启用记忆")
    memory_config_name: Optional[str] = Field(None, description="记忆配置名称")
    enable_user_memories: bool = Field(default=False, description="是否启用用户记忆")
    enable_agentic_memory: bool = Field(default=False, description="是否启用Agent记忆")
    num_history_runs: int = Field(default=3, description="历史运行次数")
    debug_mode: bool = Field(default=False, description="调试模式")
    show_tool_calls: bool = Field(default=False, description="显示工具调用")
    markdown: bool = Field(default=False, description="Markdown输出")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class AgentCreateFromTemplateRequest(BaseModel):
    """基于模板创建Agent请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    template_name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="Agent描述")
    custom_instructions: Optional[str] = Field(None, description="自定义指令")
    model_configuration_id: Optional[int] = Field(None, description="模型配置ID")
    enable_memory: bool = Field(default=False, description="是否启用记忆")
    memory_config_name: Optional[str] = Field(None, description="记忆配置名称")


class AgentUpdateRequest(BaseModel):
    """更新Agent请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent名称")
    description: Optional[str] = Field(None, max_length=500, description="Agent描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    instructions: Optional[str] = Field(None, description="指令")
    additional_instructions: Optional[str] = Field(None, description="额外指令")
    capabilities: Optional[List[str]] = Field(None, description="能力列表")
    tool_names: Optional[List[str]] = Field(None, description="工具名称列表")
    model_configuration_id: Optional[int] = Field(None, description="模型配置ID")
    enable_user_memories: Optional[bool] = Field(None, description="是否启用用户记忆")
    enable_agentic_memory: Optional[bool] = Field(None, description="是否启用Agent记忆")
    num_history_runs: Optional[int] = Field(None, description="历史运行次数")
    debug_mode: Optional[bool] = Field(None, description="调试模式")
    show_tool_calls: Optional[bool] = Field(None, description="显示工具调用")
    markdown: Optional[bool] = Field(None, description="Markdown输出")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class AgentRunRequest(BaseModel):
    """运行Agent请求模型"""
    message: str = Field(..., min_length=1, description="输入消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    stream: bool = Field(default=False, description="是否流式响应")


class AgentCloneRequest(BaseModel):
    """克隆Agent请求模型"""
    new_name: str = Field(..., min_length=1, max_length=100, description="新Agent名称")


class AgentImportRequest(BaseModel):
    """导入Agent请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    config_data: Dict[str, Any] = Field(..., description="配置数据")
    model_configuration_id: Optional[int] = Field(None, description="模型配置ID")


# 响应模型
class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: int
    agent_uuid: str
    name: str
    description: Optional[str]
    agent_type: str
    status: str
    model_configuration_id: Optional[int]
    system_prompt: Optional[str]
    instructions: Optional[str]
    capabilities: List[str]
    tool_names: List[str]
    enable_user_memories: bool
    enable_agentic_memory: bool
    num_history_runs: int
    debug_mode: bool
    show_tool_calls: bool
    markdown: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class AgentTemplateResponse(BaseModel):
    """Agent模板响应模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    agent_type: str
    system_prompt: Optional[str]
    instructions: Optional[str]
    default_capabilities: List[str]
    default_tool_names: List[str]
    is_system: bool
    is_active: bool

    class Config:
        from_attributes = True


class AgentStatsResponse(BaseModel):
    """Agent统计响应模型"""
    total_uses: int
    success_rate: float
    avg_response_time: float
    total_response_length: int
    daily_usage: List[Dict[str, Any]]


# 路由器
router = APIRouter(prefix="/api/agents", tags=["agents"])


# 依赖注入
def get_agent_manager() -> AgentCRUDManager:
    """获取Agent管理器实例"""
    # 这里需要根据实际应用架构来获取实例
    # 暂时使用全局实例的方式
    global _agent_manager
    return _agent_manager


def _agent_manager() -> AgentCRUDManager:
    """全局Agent管理器实例"""
    pass  # 将在应用启动时初始化


def init_agent_api(db_manager: DBManager, models_manager: ModelsManager) -> APIRouter:
    """初始化Agent API"""

    global _agent_manager
    _agent_manager = AgentCRUDManager(db_manager, models_manager)

    # 初始化数据表
    _agent_manager.initialize_tables()

    return router


# API端点定义
@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    manager: AgentCRUDManager = Depends(get_agent_manager),
    user_id: Optional[int] = None
):
    """创建新的Agent"""
    try:
        agent = manager.create_custom_agent(
            name=request.name,
            agent_type=request.agent_type,
            description=request.description,
            system_prompt=request.system_prompt,
            instructions=request.instructions,
            additional_instructions=request.additional_instructions,
            capabilities=request.capabilities,
            tool_names=request.tool_names,
            user_id=user_id,
            model_configuration_id=request.model_configuration_id,
            enable_memory=request.enable_memory,
            memory_config_name=request.memory_config_name,
            enable_user_memories=request.enable_user_memories,
            enable_agentic_memory=request.enable_agentic_memory,
            num_history_runs=request.num_history_runs,
            debug_mode=request.debug_mode,
            show_tool_calls=request.show_tool_calls,
            markdown=request.markdown,
            metadata_json=request.metadata
        )

        if not agent:
            raise HTTPException(status_code=500, detail="Failed to create agent")

        return AgentResponse.from_orm(agent)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-template", response_model=AgentResponse, status_code=201)
async def create_agent_from_template(
    request: AgentCreateFromTemplateRequest,
    manager: AgentCRUDManager = Depends(get_agent_manager),
    user_id: Optional[int] = None
):
    """基于模板创建Agent"""
    try:
        agent = manager.create_agent_from_template(
            name=request.name,
            template_name=request.template_name,
            description=request.description,
            custom_instructions=request.custom_instructions,
            model_configuration_id=request.model_configuration_id,
            user_id=user_id,
            enable_memory=request.enable_memory,
            memory_config_name=request.memory_config_name
        )

        if not agent:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")

        return AgentResponse.from_orm(agent)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    user_id: Optional[int] = None,
    agent_type: Optional[AgentType] = Query(None, description="Agent类型"),
    status: Optional[AgentStatus] = Query(None, description="Agent状态"),
    limit: int = Query(50, le=100, description="返回数量限制"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """获取Agent列表"""
    try:
        agents = manager.list_user_agents(
            user_id=user_id,
            agent_type=agent_type,
            status=status,
            limit=limit
        )
        return [AgentResponse.from_orm(agent) for agent in agents]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int = Path(..., description="Agent ID"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """获取指定Agent详情"""
    try:
        agent = manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentResponse.from_orm(agent)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uuid/{agent_uuid}", response_model=AgentResponse)
async def get_agent_by_uuid(
    agent_uuid: str = Path(..., description="Agent UUID"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """根据UUID获取Agent"""
    try:
        agent = manager.get_agent_by_uuid(agent_uuid)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentResponse.from_orm(agent)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int = Path(..., description="Agent ID"),
    request: AgentUpdateRequest = ...,
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """更新Agent配置"""
    try:
        agent = manager.update_agent_config(
            agent_id=agent_id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            instructions=request.instructions,
            additional_instructions=request.additional_instructions,
            capabilities=request.capabilities,
            tool_names=request.tool_names,
            model_configuration_id=request.model_configuration_id,
            enable_user_memories=request.enable_user_memories,
            enable_agentic_memory=request.enable_agentic_memory,
            num_history_runs=request.num_history_runs,
            debug_mode=request.debug_mode,
            show_tool_calls=request.show_tool_calls,
            markdown=request.markdown,
            metadata_json=request.metadata
        )

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentResponse.from_orm(agent)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int = Path(..., description="Agent ID"),
    soft_delete: bool = Query(True, description="是否软删除"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """删除Agent"""
    try:
        success = manager.delete_agent(agent_id, soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {"message": "Agent deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: int = Path(..., description="Agent ID"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """激活Agent"""
    try:
        success = manager.activate_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {"message": "Agent activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: int = Path(..., description="Agent ID"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """停用Agent"""
    try:
        success = manager.deactivate_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {"message": "Agent deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: int = Path(..., description="Agent ID"),
    request: AgentRunRequest = ...,
    manager: AgentCRUDManager = Depends(get_agent_manager),
    user_id: Optional[int] = None
):
    """运行Agent"""
    try:
        # 检查Agent是否存在
        agent = manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # 检查Agent状态
        if agent.status != AgentStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Agent is not active")

        # 运行Agent
        response = manager.run_agent(
            agent_id=agent_id,
            message=request.message,
            session_id=request.session_id,
            user_id=user_id,
            stream=request.stream
        )

        return {"response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_id: int = Path(..., description="Agent ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """获取Agent使用统计"""
    try:
        stats = manager.get_agent_statistics(agent_id, days)
        return AgentStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/clone", response_model=AgentResponse)
async def clone_agent(
    agent_id: int = Path(..., description="Agent ID"),
    request: AgentCloneRequest = ...,
    manager: AgentCRUDManager = Depends(get_agent_manager),
    user_id: Optional[int] = None
):
    """克隆Agent"""
    try:
        new_agent = manager.clone_agent(
            agent_id=agent_id,
            new_name=request.new_name,
            user_id=user_id
        )

        if not new_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentResponse.from_orm(new_agent)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/export")
async def export_agent(
    agent_id: int = Path(..., description="Agent ID"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """导出Agent配置"""
    try:
        config = manager.export_agent_config(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent not found")

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=AgentResponse)
async def import_agent(
    request: AgentImportRequest = ...,
    manager: AgentCRUDManager = Depends(get_agent_manager),
    user_id: Optional[int] = None
):
    """导入Agent配置"""
    try:
        agent = manager.import_agent_config(
            config_data=request.config_data,
            name=request.name,
            user_id=user_id,
            model_configuration_id=request.model_configuration_id
        )

        if not agent:
            raise HTTPException(status_code=400, detail="Failed to import agent configuration")

        return AgentResponse.from_orm(agent)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=List[AgentResponse])
async def search_agents(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    user_id: Optional[int] = None,
    agent_type: Optional[AgentType] = Query(None, description="Agent类型"),
    limit: int = Query(20, le=100, description="返回数量限制"),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """搜索Agent"""
    try:
        agents = manager.search_agents(
            query=query,
            user_id=user_id,
            agent_type=agent_type,
            limit=limit
        )
        return [AgentResponse.from_orm(agent) for agent in agents]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[AgentTemplateResponse])
async def list_agent_templates(
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """获取Agent配置模板列表"""
    try:
        templates = manager.list_available_templates()
        return [AgentTemplateResponse.from_orm(template) for template in templates]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory-configs", response_model=List[Dict[str, Any]])
async def list_memory_configs(
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    """获取记忆配置列表"""
    try:
        configs = manager.list_available_memory_configs()
        return [
            {
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "memory_type": config.memory_type,
                "enable_user_memories": config.enable_user_memories,
                "enable_agentic_memory": config.enable_agentic_memory,
                "enable_task_memories": config.enable_task_memories,
                "enable_context_memories": config.enable_context_memories,
                "max_memory_entries": config.max_memory_entries,
                "retention_days": config.retention_days
            }
            for config in configs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))