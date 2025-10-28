"""
Agent管理器实现
整合agno_modular模块与数据库管理，提供完整的Agent CRUD功能
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json

from agent_factory import (
    AgentConfig,
    create_agent,
    create_qa_agent,
    create_task_agent,
    create_research_agent,
    create_creative_agent,
    create_custom_agent
)
from composer import (
    AgentSystemConfig,
    compose_agent_system
)
from memory_factory import MemoryConfig, create_memory_manager
from mcp_factory import MCPConfig
from agent_models import (
    Agent,
    AgentConfigTemplate,
    AgentManager as DBAgentManager,
    AgentType,
    AgentStatus,
    MemoryConfig as DBMemoryConfig,
    init_agent_tables
)
from models_mgr import ModelsManager
from db_mgr import DBManager


class AgentCRUDManager:
    """Agent CRUD管理器 - 整合agno_modular和数据库操作"""

    def __init__(self, db_manager: DBManager, models_manager: ModelsManager):
        self.db_manager = db_manager
        self.models_manager = models_manager
        self.agent_db_manager = DBAgentManager(db_manager.engine)

    def initialize_tables(self) -> bool:
        """初始化Agent相关数据表"""
        return init_agent_tables(self.db_manager)

    def create_agent_from_template(
        self,
        name: str,
        template_name: str,
        user_id: Optional[int] = None,
        model_configuration_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
        **kwargs
    ) -> Optional[Agent]:
        """基于模板创建Agent"""

        # 获取模板
        template = self._get_template_by_name(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # 获取模型配置（如果未指定）
        if not model_configuration_id:
            # 使用默认的文本模型配置
            from db_mgr import CapabilityAssignment, ModelCapability
            with Session(self.db_manager.engine) as session:
                stmt = select(CapabilityAssignment).where(
                    CapabilityAssignment.capability_value == ModelCapability.TEXT.value
                )
                assignment = session.exec(stmt).first()
                if assignment:
                    model_configuration_id = assignment.model_configuration_id

        # 创建数据库记录
        agent = self.agent_db_manager.create_agent(
            name=name,
            agent_type=AgentType(template.agent_type),
            model_configuration_id=model_configuration_id,
            system_prompt=template.system_prompt,
            instructions=custom_instructions or template.instructions,
            capabilities=template.default_capabilities,
            tool_names=template.default_tool_names,
            user_id=user_id,
            **kwargs
        )

        return agent

    def create_custom_agent(
        self,
        name: str,
        agent_type: AgentType,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        model_configuration_id: Optional[int] = None,
        enable_memory: bool = False,
        memory_config_name: Optional[str] = None,
        **kwargs
    ) -> Optional[Agent]:
        """创建自定义Agent"""

        # 获取模型配置（如果未指定）
        if not model_configuration_id:
            model_configuration_id = self._get_default_model_config()

        # 获取记忆配置（如果启用）
        memory_config_id = None
        if enable_memory and memory_config_name:
            memory_config_id = self._get_memory_config_id(memory_config_name)

        # 创建数据库记录
        agent = self.agent_db_manager.create_agent(
            name=name,
            agent_type=agent_type,
            model_configuration_id=model_configuration_id,
            system_prompt=system_prompt,
            instructions=instructions,
            capabilities=capabilities or [],
            tool_names=tool_names or [],
            user_id=user_id,
            memory_config_id=memory_config_id,
            enable_user_memories=enable_memory,
            **kwargs
        )

        return agent

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """获取Agent"""
        return self.agent_db_manager.get_agent_by_id(agent_id)

    def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Agent]:
        """根据UUID获取Agent"""
        return self.agent_db_manager.get_agent_by_uuid(agent_uuid)

    def list_user_agents(
        self,
        user_id: int,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None,
        limit: int = 50
    ) -> List[Agent]:
        """列出用户的Agent"""
        if agent_type:
            return self.agent_db_manager.get_agents_by_type(agent_type, status)
        else:
            return self.agent_db_manager.get_agents_by_user(user_id, status)

    def update_agent_config(
        self,
        agent_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        model_configuration_id: Optional[int] = None,
        **kwargs
    ) -> Optional[Agent]:
        """更新Agent配置"""
        return self.agent_db_manager.update_agent(
            agent_id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            instructions=instructions,
            capabilities=capabilities,
            tool_names=tool_names,
            **kwargs
        )

    def delete_agent(self, agent_id: int, soft_delete: bool = True) -> bool:
        """删除Agent"""
        return self.agent_db_manager.delete_agent(agent_id, soft_delete)

    def activate_agent(self, agent_id: int) -> bool:
        """激活Agent"""
        return self.agent_db_manager.activate_agent(agent_id)

    def deactivate_agent(self, agent_id: int) -> bool:
        """停用Agent"""
        return self.agent_db_manager.deactivate_agent(agent_id)

    def search_agents(
        self,
        query: str,
        user_id: Optional[int] = None,
        agent_type: Optional[AgentType] = None,
        limit: int = 20
    ) -> List[Agent]:
        """搜索Agent"""
        return self.agent_db_manager.search_agents(
            query=query,
            user_id=user_id,
            agent_type=agent_type,
            limit=limit
        )

    def create_agent_system(self, agent_id: int) -> Optional[Any]:
        """基于数据库配置创建Agent系统实例"""

        # 获取Agent配置
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # 获取模型
        model = self._get_model_by_config_id(agent.model_configuration_id)
        if not model:
            raise ValueError(f"Model configuration {agent.model_configuration_id} not found")

        # 创建Agent配置
        agent_config = AgentConfig(
            name=agent.name,
            model=model,
            agent_id=agent.agent_uuid,
            system_prompt=agent.system_prompt,
            instructions=agent.instructions,
            additional_instructions=agent.additional_instructions,
            enable_user_memories=agent.enable_user_memories,
            enable_agentic_memory=agent.enable_agentic_memory,
            num_history_runs=agent.num_history_runs,
            debug_mode=agent.debug_mode,
            show_tool_calls=agent.show_tool_calls,
            markdown=agent.markdown
        )

        # 获取MCP配置
        mcp_configs = self._get_mcp_configs(agent.mcp_config_ids)

        # 获取记忆配置
        memory_config = None
        if agent.memory_config_id:
            memory_config = self._get_memory_config_by_id(agent.memory_config_id)

        # 创建系统配置
        system_config = AgentSystemConfig(
            system_name=f"agent_system_{agent.id}",
            description=f"Agent system for {agent.name}",
            agent_config=agent_config,
            mcp_configs=mcp_configs,
            memory_config=memory_config,
            use_multi_memory=memory_config is not None,
            response_stream=False
        )

        # 组装Agent系统
        return compose_agent_system(system_config)

    def run_agent(
        self,
        agent_id: int,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Any:
        """运行Agent并记录使用日志"""

        start_time = datetime.now()

        try:
            # 创建Agent系统
            agent_system = self.create_agent_system(agent_id)
            if not agent_system:
                raise ValueError(f"Agent {agent_id} not found or cannot be created")

            # 运行Agent
            response = agent_system.run(message, **kwargs)

            # 计算响应时间
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # 计算响应长度
            response_length = len(str(response)) if response else 0

            # 记录使用日志
            self.agent_db_manager.log_agent_usage(
                agent_id=agent_id,
                input_message=message,
                response_length=response_length,
                response_time_ms=response_time_ms,
                success=True,
                session_id=int(session_id) if session_id and session_id.isdigit() else None,
                user_id=user_id
            )

            return response

        except Exception as e:
            # 记录错误日志
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.agent_db_manager.log_agent_usage(
                agent_id=agent_id,
                input_message=message,
                response_length=0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e),
                session_id=int(session_id) if session_id and session_id.isdigit() else None,
                user_id=user_id
            )

            raise e

    def get_agent_statistics(self, agent_id: int, days: int = 30) -> Dict[str, Any]:
        """获取Agent使用统计"""
        return self.agent_db_manager.get_agent_usage_stats(agent_id, days)

    def clone_agent(
        self,
        agent_id: int,
        new_name: str,
        user_id: Optional[int] = None
    ) -> Optional[Agent]:
        """克隆Agent"""

        # 获取原Agent
        original_agent = self.get_agent(agent_id)
        if not original_agent:
            return None

        # 创建新Agent
        new_agent = self.agent_db_manager.create_agent(
            name=new_name,
            agent_type=AgentType(original_agent.agent_type),
            model_configuration_id=original_agent.model_configuration_id,
            system_prompt=original_agent.system_prompt,
            instructions=original_agent.instructions,
            additional_instructions=original_agent.additional_instructions,
            capabilities=original_agent.capabilities.copy(),
            tool_names=original_agent.tool_names.copy(),
            mcp_config_ids=original_agent.mcp_config_ids.copy(),
            user_id=user_id,
            enable_user_memories=original_agent.enable_user_memories,
            enable_agentic_memory=original_agent.enable_agentic_memory,
            memory_config_id=original_agent.memory_config_id,
            num_history_runs=original_agent.num_history_runs,
            debug_mode=original_agent.debug_mode,
            show_tool_calls=original_agent.show_tool_calls,
            markdown=original_agent.markdown,
            metadata_json=original_agent.metadata_json.copy() if original_agent.metadata_json else None
        )

        return new_agent

    def export_agent_config(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """导出Agent配置"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        return {
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "system_prompt": agent.system_prompt,
            "instructions": agent.instructions,
            "additional_instructions": agent.additional_instructions,
            "capabilities": agent.capabilities,
            "tool_names": agent.tool_names,
            "enable_user_memories": agent.enable_user_memories,
            "enable_agentic_memory": agent.enable_agentic_memory,
            "num_history_runs": agent.num_history_runs,
            "debug_mode": agent.debug_mode,
            "show_tool_calls": agent.show_tool_calls,
            "markdown": agent.markdown,
            "metadata": agent.metadata_json
        }

    def import_agent_config(
        self,
        config_data: Dict[str, Any],
        name: str,
        user_id: Optional[int] = None,
        model_configuration_id: Optional[int] = None
    ) -> Optional[Agent]:
        """导入Agent配置"""

        agent_type = AgentType(config_data.get("agent_type", "custom"))

        return self.create_custom_agent(
            name=name,
            agent_type=agent_type,
            system_prompt=config_data.get("system_prompt"),
            instructions=config_data.get("instructions"),
            additional_instructions=config_data.get("additional_instructions"),
            capabilities=config_data.get("capabilities", []),
            tool_names=config_data.get("tool_names", []),
            user_id=user_id,
            model_configuration_id=model_configuration_id,
            enable_user_memories=config_data.get("enable_user_memories", False),
            enable_agentic_memory=config_data.get("enable_agentic_memory", False),
            num_history_runs=config_data.get("num_history_runs", 3),
            debug_mode=config_data.get("debug_mode", False),
            show_tool_calls=config_data.get("show_tool_calls", False),
            markdown=config_data.get("markdown", False),
            metadata_json=config_data.get("metadata")
        )

    # 私有辅助方法
    def _get_template_by_name(self, template_name: str) -> Optional[AgentConfigTemplate]:
        """根据名称获取配置模板"""
        with Session(self.db_manager.engine) as session:
            stmt = select(AgentConfigTemplate).where(AgentConfigTemplate.name == template_name)
            return session.exec(stmt).first()

    def _get_default_model_config(self) -> Optional[int]:
        """获取默认模型配置ID"""
        from db_mgr import CapabilityAssignment, ModelCapability
        with Session(self.db_manager.engine) as session:
            stmt = select(CapabilityAssignment).where(
                CapabilityAssignment.capability_value == ModelCapability.TEXT.value
            )
            assignment = session.exec(stmt).first()
            return assignment.model_configuration_id if assignment else None

    def _get_memory_config_id(self, config_name: str) -> Optional[int]:
        """根据名称获取记忆配置ID"""
        with Session(self.db_manager.engine) as session:
            stmt = select(DBMemoryConfig).where(DBMemoryConfig.name == config_name)
            config = session.exec(stmt).first()
            return config.id if config else None

    def _get_model_by_config_id(self, config_id: Optional[int]) -> Optional[Any]:
        """根据配置ID获取模型实例"""
        if not config_id:
            return None

        try:
            return self.models_manager.get_model_by_config_id(config_id)
        except Exception:
            return None

    def _get_mcp_configs(self, config_ids: List[int]) -> List[MCPConfig]:
        """获取MCP配置列表"""
        # 这里需要根据实际的MCP配置表来实现
        # 暂时返回空列表
        return []

    def _get_memory_config_by_id(self, config_id: Optional[int]) -> Optional[MemoryConfig]:
        """根据ID获取记忆配置"""
        if not config_id:
            return None

        with Session(self.db_manager.engine) as session:
            stmt = select(DBMemoryConfig).where(DBMemoryConfig.id == config_id)
            db_config = session.exec(stmt).first()

            if not db_config:
                return None

            # 转换为agno_modular的MemoryConfig
            return MemoryConfig(
                model=None,  # 需要传入模型实例
                db=db_config.db_path,
                table_name=db_config.table_name,
                add_memories=db_config.enable_user_memories,
                update_memories=db_config.enable_user_memories
            )

    def list_available_templates(self) -> List[AgentConfigTemplate]:
        """列出可用的配置模板"""
        with Session(self.db_manager.engine) as session:
            stmt = select(AgentConfigTemplate).where(AgentConfigTemplate.is_active == True)
            return session.exec(stmt).all()

    def list_available_memory_configs(self) -> List[DBMemoryConfig]:
        """列出可用的记忆配置"""
        with Session(self.db_manager.engine) as session:
            stmt = select(DBMemoryConfig)
            return session.exec(stmt).all()