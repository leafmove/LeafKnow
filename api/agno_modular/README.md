# Agno模块化组件库

这个库将agno框架的agent、MCP工具和记忆模块拆分为独立的函数，支持灵活组合以应对不同的使用场景。

## 特性

- **模块化设计**: 独立的Agent、MCP工具和记忆管理器工厂函数
- **灵活组合**: 支持动态组合不同类型的组件
- **预配置模板**: 提供常用场景的预配置方案
- **类型安全**: 完整的类型提示支持
- **易于扩展**: 简单的接口设计，易于添加新组件

## 安装

```bash
# 确保已安装agno框架
pip install agno

# 将此模块添加到你的项目中
# 或将agno_modular目录复制到你的项目
```

## 快速开始

### 基础问答Agent

```python
from agno.models.openai import OpenAIChat
from agno_modular import create_qa_agent

# 创建模型
model = OpenAIChat(id="gpt-4")

# 创建问答Agent
agent = create_qa_agent(
    model=model,
    system_prompt="你是一个专业的Python编程助手",
    debug_mode=True
)

# 运行Agent
response = agent.run("如何在Python中创建一个类？")
print(response)
```

### 带MCP工具的任务Agent

```python
from agno_modular import create_task_agent, create_filesystem_mcp

# 创建文件系统MCP工具
fs_tools = create_filesystem_mcp(
    base_path="/tmp",
    name="file_manager"
)

# 创建任务Agent
agent = create_task_agent(
    model=model,
    task_description="文件管理任务",
    tools=[fs_tools]
)

# 运行Agent
response = agent.run("在/tmp目录下创建一个test.txt文件")
```

### 完整的Agent系统

```python
from agno_modular import create_qa_system, MCPConfig, MemoryConfig

# 创建Web搜索MCP配置
web_mcp = MCPConfig(
    name="web_search",
    server_command="npx",
    server_args=["-y", "@modelcontextprotocol/server-brave-search"],
    server_env={"BRAVE_API_KEY": "your_api_key"}
)

# 创建记忆配置
memory_config = MemoryConfig(
    model=model,
    add_memories=True,
    update_memories=True
)

# 创建问答系统
qa_system = create_qa_system(
    model=model,
    system_prompt="你是一个智能问答助手",
    mcp_configs=[web_mcp],
    memory_config=memory_config,
    user_id="user123"
)

# 运行系统
response = qa_system.run("最新的AI发展趋势是什么？")
```

## 核心组件

### Agent工厂

`agent_factory.py` 提供了多种Agent创建函数：

- `create_agent(config)`: 创建通用Agent
- `create_qa_agent()`: 创建问答Agent
- `create_task_agent()`: 创建任务执行Agent
- `create_research_agent()`: 创建研究Agent
- `create_creative_agent()`: 创建创意Agent
- `create_custom_agent()`: 创建自定义Agent

### MCP工具工厂

`mcp_factory.py` 提供了各种MCP工具创建函数：

- `create_mcp_tools(config)`: 创建基础MCP工具
- `create_filesystem_mcp()`: 创建文件系统工具
- `create_database_mcp()`: 创建数据库工具
- `create_web_search_mcp()`: 创建网络搜索工具
- `create_github_mcp()`: 创建GitHub工具
- `create_multi_mcp_tools()`: 创建多MCP工具组合

### 记忆管理工厂

`memory_factory.py` 提供了各种记忆管理器创建函数：

- `create_memory_manager(config)`: 创建通用记忆管理器
- `create_conversation_memory()`: 创建对话记忆管理器
- `create_personal_memory()`: 创建个人信息记忆管理器
- `create_task_memory()`: 创建任务记忆管理器
- `create_learning_memory()`: 创建学习记忆管理器
- `create_multi_memory_system()`: 创建多记忆系统

### 系统组合器

`composer.py` 提供了系统组合功能：

- `compose_agent_system(config)`: 组合完整的Agent系统
- `create_qa_system()`: 创建问答系统
- `create_task_system()`: 创建任务系统
- `create_research_system()`: 创建研究系统
- `create_personal_assistant_system()`: 创建个人助理系统
- `create_dynamic_system()`: 创建动态系统

## 配置类

### AgentConfig

```python
@dataclass
class AgentConfig:
    name: str = "agent"
    model: Optional[Model] = None
    system_prompt: Optional[str] = None
    tools: List[Union[Toolkit, Callable]] = field(default_factory=list)
    memory_manager: Optional[MemoryManager] = None
    enable_user_memories: bool = False
    debug_mode: bool = False
    # ... 更多配置选项
```

### MCPConfig

```python
@dataclass
class MCPConfig:
    name: str = "mcp_tools"
    server_url: Optional[str] = None
    server_command: Optional[str] = None
    server_args: List[str] = field(default_factory=list)
    include_tools: Optional[List[str]] = None
    exclude_tools: Optional[List[str]] = None
    timeout: int = 30
    # ... 更多配置选项
```

### MemoryConfig

```python
@dataclass
class MemoryConfig:
    model: Optional[Model] = None
    system_message: Optional[str] = None
    memory_capture_instructions: Optional[str] = None
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None
    delete_memories: bool = False
    update_memories: bool = True
    add_memories: bool = True
    # ... 更多配置选项
```

## 高级用法

### 多记忆系统

```python
from agno_modular import AgentSystemConfig, compose_agent_system

# 创建多记忆系统配置
system_config = AgentSystemConfig(
    system_name="multi_memory_agent",
    agent_config=AgentConfig(
        name="intelligent_agent",
        model=model,
        system_prompt="使用多记忆系统的智能助手"
    ),
    use_multi_memory=True,
    memory_types=["personal", "task", "preference", "context"],
    user_id="user123"
)

# 创建系统
system = compose_agent_system(system_config)
```

### 动态系统配置

```python
from agno_modular import create_dynamic_system

# 动态创建系统
system = create_dynamic_system(
    model=model,
    system_prompt="灵活使用各种工具的助手",
    tools=[
        create_filesystem_mcp("/tmp"),
        create_web_search_mcp("your_api_key"),
        # 可以添加更多工具
    ]
)

response = system.run("帮我搜索最新技术新闻并保存到文件")
```

### 自定义Agent

```python
from agno_modular import create_custom_agent

# 创建自定义Agent
agent = create_custom_agent(
    model=model,
    role="数据分析师",
    capabilities=[
        "数据清洗和预处理",
        "统计分析",
        "数据可视化"
    ],
    constraints=[
        "确保数据隐私",
        "使用科学方法"
    ]
)
```

## 测试

运行测试套件：

```python
from agno_modular.tests import run_tests

success = run_tests()
if success:
    print("所有测试通过！")
```

或使用命令行：

```bash
python -m agno_modular.tests
```

## 示例

查看 `examples.py` 文件获取更多使用示例：

```python
from agno_modular.examples import run_all_examples

# 运行所有示例
run_all_examples()
```

## 架构设计

```
agno_modular/
├── __init__.py          # 模块入口
├── agent_factory.py     # Agent工厂
├── mcp_factory.py       # MCP工具工厂
├── memory_factory.py    # 记忆管理工厂
├── composer.py          # 系统组合器
├── examples.py          # 使用示例
├── tests.py            # 测试套件
└── README.md           # 文档
```

## 贡献

欢迎提交问题和改进建议！

## 许可证

本项目遵循MIT许可证。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持Agent、MCP工具和记忆模块的模块化创建
- 提供多种预配置模板
- 完整的类型提示支持
- 包含测试套件和使用示例