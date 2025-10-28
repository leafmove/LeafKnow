# Agno模块化组件使用指南

## 概述

本指南将帮助您使用Agno模块化组件库，该库将agno框架的agent、MCP工具和记忆模块拆分为独立的函数，支持灵活组合以应对不同的使用场景。

## 快速开始

### 1. 环境准备

```bash
# 确保Python版本 >= 3.10
python --version

# 安装agno框架（可选，如果需要完整功能）
pip install agno

# 将agno_modular目录添加到您的项目中
```

### 2. 基础使用

#### 创建简单的问答Agent

```python
from agno_modular import create_qa_agent
from agno.models.openai import OpenAIChat

# 创建模型
model = OpenAIChat(id="gpt-4")

# 创建问答Agent
agent = create_qa_agent(
    model=model,
    system_prompt="你是一个专业的编程助手",
    debug_mode=True
)

# 运行Agent
response = agent.run("如何在Python中创建类？")
print(response)
```

#### 配置记忆管理

```python
from agno_modular import create_conversation_memory, MemoryConfig

# 创建记忆配置
memory_config = MemoryConfig(
    model=model,
    memory_capture_instructions="记录对话中的重要信息",
    retrieval_method="last_n",
    retrieval_limit=10
)

# 创建记忆管理器
memory_manager = create_conversation_memory(
    model=model,
    db=your_database  # 可选
)
```

#### 添加MCP工具

```python
from agno_modular import create_filesystem_mcp, create_web_search_mcp

# 创建文件系统工具
fs_tools = create_filesystem_mcp(
    base_path="/tmp",
    name="file_manager"
)

# 创建网络搜索工具
web_tools = create_web_search_mcp(
    api_key="your_api_key",
    search_engine="brave"
)

# 在Agent中使用
agent = create_task_agent(
    model=model,
    task_description="文件处理和信息搜索",
    tools=[fs_tools, web_tools]
)
```

## 核心组件详解

### 1. Agent工厂

Agent工厂提供了多种预配置的Agent类型：

```python
from agno_modular import (
    create_agent, create_qa_agent, create_task_agent,
    create_research_agent, create_creative_agent, create_custom_agent
)

# 通用Agent
agent = create_agent(agent_config)

# 问答Agent
qa_agent = create_qa_agent(model, system_prompt="...")

# 任务Agent
task_agent = create_task_agent(model, task_description="...")

# 研究Agent
research_agent = create_research_agent(model, research_domain="...")

# 创意Agent
creative_agent = create_creative_agent(model, creative_domain="...")

# 自定义Agent
custom_agent = create_custom_agent(
    model=model,
    role="专家角色",
    capabilities=["能力1", "能力2"],
    constraints=["约束1"]
)
```

### 2. MCP工具工厂

MCP工具工厂支持创建各种类型的外部工具：

```python
from agno_modular import (
    create_filesystem_mcp, create_database_mcp, create_web_search_mcp,
    create_github_mcp, create_multi_mcp_tools
)

# 文件系统工具
fs_mcp = create_filesystem_mcp("/path/to/directory")

# 数据库工具
db_mcp = create_database_mcp(
    connection_string="postgresql://...",
    db_type="postgresql"
)

# 网络搜索工具
web_mcp = create_web_search_mcp(
    api_key="your_key",
    search_engine="brave"
)

# 多工具组合
multi_mcp = create_multi_mcp_tools([fs_mcp, web_mcp])
```

### 3. 记忆管理工厂

记忆管理工厂提供了不同类型的记忆策略：

```python
from agno_modular import (
    create_conversation_memory, create_personal_memory,
    create_task_memory, create_multi_memory_system
)

# 对话记忆
conv_memory = create_conversation_memory(model=model)

# 个人信息记忆
personal_memory = create_personal_memory(model=model)

# 任务记忆
task_memory = create_task_memory(model=model)

# 多记忆系统
multi_memory = create_multi_memory_system(
    model=model,
    memory_types=["conversation", "personal", "task"]
)
```

### 4. 系统组合器

系统组合器用于创建完整的Agent系统：

```python
from agno_modular import (
    create_qa_system, create_task_system, create_personal_assistant_system,
    compose_agent_system, AgentSystemConfig
)

# 预配置系统
qa_system = create_qa_system(
    model=model,
    system_prompt="专业问答助手",
    memory_config=memory_config
)

# 自定义系统组合
system_config = AgentSystemConfig(
    system_name="my_system",
    agent_config=agent_config,
    mcp_configs=[mcp_config],
    memory_config=memory_config
)

system = compose_agent_system(system_config)
```

## 使用场景示例

### 1. 客户服务系统

```python
from agno_modular import AgentSystemConfig, compose_agent_system

# 配置客户服务Agent
agent_config = AgentConfig(
    name="customer_service",
    model=model,
    system_prompt="你是专业的客服代表",
    instructions="提供友好、专业的服务",
    enable_user_memories=True
)

# 配置记忆管理
memory_config = MemoryConfig(
    memory_capture_instructions="记录客户信息和历史问题",
    retrieval_method="agentic"
)

# 创建系统
system = compose_agent_system(AgentSystemConfig(
    system_name="customer_service_system",
    agent_config=agent_config,
    memory_config=memory_config
))

# 运行系统
response = system.run("帮我查询订单状态")
```

### 2. 教育辅导系统

```python
# 创建多记忆教育系统
system_config = AgentSystemConfig(
    system_name="education_tutor",
    agent_config=AgentConfig(
        name="tutor",
        model=model,
        system_prompt="你是专业的学习辅导老师"
    ),
    use_multi_memory=True,
    memory_types=["learning", "personal", "conversation"]
)

system = compose_agent_system(system_config)
```

### 3. 数据分析系统

```python
# 配置数据分析工具
mcp_configs = [
    create_database_mcp("postgresql://...", "postgresql"),
    create_filesystem_mcp("/data", name="data_files")
]

# 创建系统
system = compose_agent_system(AgentSystemConfig(
    system_name="data_analysis",
    agent_config=AgentConfig(
        name="analyst",
        model=model,
        show_tool_calls=True
    ),
    mcp_configs=mcp_configs
))
```

## 配置详解

### AgentConfig参数

```python
@dataclass
class AgentConfig:
    name: str = "agent"                    # Agent名称
    model: Optional[Model] = None          # AI模型
    system_prompt: Optional[str] = None    # 系统提示词
    instructions: Optional[str] = None     # 指令
    tools: List[Tool] = []                 # 工具列表
    enable_user_memories: bool = False     # 启用用户记忆
    debug_mode: bool = False               # 调试模式
    # ... 更多参数
```

### MCPConfig参数

```python
@dataclass
class MCPConfig:
    name: str = "mcp_tools"               # 工具名称
    server_command: Optional[str] = None  # 服务器命令
    server_args: List[str] = []           # 命令参数
    server_env: Dict[str, str] = {}       # 环境变量
    timeout: int = 30                     # 超时时间
    # ... 更多参数
```

### MemoryConfig参数

```python
@dataclass
class MemoryConfig:
    model: Optional[Model] = None         # AI模型
    memory_capture_instructions: str = ""  # 记忆捕获指令
    retrieval_method: str = "last_n"       # 检索方法
    retrieval_limit: int = 10              # 检索限制
    add_memories: bool = True              # 添加记忆
    update_memories: bool = True           # 更新记忆
    # ... 更多参数
```

## 最佳实践

### 1. 配置管理

```python
# 使用配置文件管理Agent设置
import yaml

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

config = load_config('agent_config.yaml')
agent = create_agent(AgentConfig(**config['agent']))
```

### 2. 错误处理

```python
try:
    response = system.run(user_message)
except Exception as e:
    logger.error(f"Agent运行错误: {e}")
    # 处理错误
```

### 3. 性能优化

```python
# 重用Agent实例
agent = create_qa_agent(model=model)

# 批量处理
for message in messages:
    response = agent.run(message)
```

### 4. 调试模式

```python
# 启用调试获取详细信息
agent_config = AgentConfig(
    name="debug_agent",
    model=model,
    debug_mode=True,
    show_tool_calls=True
)
```

## 测试

运行测试套件：

```bash
# 运行配置测试
python test_config.py

# 运行工厂函数测试
python test_factories.py

# 运行独立测试
python test_standalone.py

# 运行演示
python standalone_demo.py
```

## 故障排除

### 常见问题

1. **导入错误**
   ```python
   # 确保路径正确
   import sys
   sys.path.append('/path/to/agno_modular')
   ```

2. **模型配置错误**
   ```python
   # 检查模型配置
   print(model.id)
   print(model.provider)
   ```

3. **MCP工具连接失败**
   ```python
   # 检查工具配置
   mcp_config = MCPConfig(
       name="test",
       server_command="test_command",
       debug_mode=True  # 启用调试
   )
   ```

## 扩展开发

### 添加新的Agent类型

```python
def create_expert_agent(model: Model, domain: str, **kwargs):
    """创建专家Agent"""
    system_prompt = f"你是{domain}领域的专家"
    return create_agent(AgentConfig(
        name=f"{domain}_expert",
        model=model,
        system_prompt=system_prompt,
        **kwargs
    ))
```

### 添加新的MCP工具

```python
def create_custom_mcp(api_key: str, **kwargs):
    """创建自定义MCP工具"""
    return create_mcp_tools(MCPConfig(
        name="custom_tool",
        server_command="custom_server",
        server_env={"API_KEY": api_key},
        **kwargs
    ))
```

## 总结

Agno模块化组件库提供了：

1. **模块化设计**: 独立组件，职责清晰
2. **灵活组合**: 支持各种使用场景
3. **易于使用**: 预配置模板和工厂函数
4. **完整测试**: 全面的测试覆盖
5. **详细文档**: 清晰的使用指南

通过这套模块化组件，您可以快速构建各种类型的AI Agent系统，灵活组合不同的工具和记忆管理，提高开发效率和代码质量。

## 获取帮助

- 查看 `README.md` 获取详细文档
- 查看 `examples.py` 获取更多示例
- 运行测试了解功能
- 查看源代码了解实现细节