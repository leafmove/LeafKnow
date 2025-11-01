# ChatEngine Agent Creation Implementation

## 概述

本文档描述了ChatEngine中`create_new_agent`函数的实现，该函数用于创建AGNO框架的Agent对象。

## 功能特性

### 核心功能

1. **Agent对象创建**: 支持创建完整的AGNO Agent实例
2. **模型集成**: 支持多种模型配置和Provider
3. **Mock Agent**: 当AGNO框架不可用时提供fallback支持
4. **参数验证**: 完整的输入参数验证
5. **数据库集成**: 支持Agent配置的持久化存储

### 支持的配置格式

#### 1. 完整配置示例
```python
agent_config = {
    'agent_id': 'agent_001',
    'name': 'Advanced Agent',
    'type': 'text',
    'model': {
        'name': 'gpt-4',
        'provider': 'openai',
        'kwargs': {
            'temperature': 0.8,
            'max_tokens': 1000,
            'api_key': 'sk-xxx'
        }
    },
    'instructions': '你是一个高级AI助手，专门提供详细和专业的回答。',
    'tools': [
        {'name': 'calculator', 'description': '数学计算'},
        {'name': 'web_search', 'description': '网络搜索'}
    ],
    'knowledge': {
        'type': 'vector_db',
        'source': 'documents'
    },
    'memory': {
        'type': 'conversation',
        'max_messages': 100
    },
    'guardrails': [
        {'type': 'content_filter', 'enabled': True}
    ],
    'metadata': {
        'version': '1.0',
        'description': '高级助手'
    },
    'user_id': 'user_001'
}
```

#### 2. 最小配置示例
```python
agent_config = {
    'agent_id': 'agent_002',
    'name': 'Basic Agent',
    'model': {
        'name': 'gpt-3.5-turbo',
        'provider': 'openai',
        'kwargs': {}
    }
}
```

#### 3. 字符串模型配置
```python
agent_config = {
    'agent_id': 'agent_003',
    'name': 'Simple Agent',
    'model': 'gpt-3.5-turbo'  # 直接使用模型名称
}
```

## 方法签名

```python
def create_new_agent(self, agent_name: str, agent_dict: Dict[str, Any]) -> Optional[Any]:
    """
    根据配置创建智能体

    Args:
        agent_name (str): 智能体名称
        agent_dict (Dict[str, Any]): 智能体配置字典

    Returns:
        Optional[Any]: 创建的Agent实例，失败时返回None
    """
```

## 实现细节

### 1. 参数验证
- `agent_name`: 不能为空字符串
- `agent_dict`: 不能为None或空字典

### 2. 模型创建流程
```python
# 支持三种模型配置格式
if isinstance(model_config, dict):
    model_instance = self.create_model_from_dict(model_config)
elif hasattr(model_config, '__class__'):
    model_instance = model_config  # 已有的Model实例
elif isinstance(model_config, str):
    model_dict = {'name': model_config, 'provider': 'openai', 'kwargs': {}}
    model_instance = self.create_model_from_dict(model_dict)
```

### 3. AGNO Agent创建
```python
# 构建Agent参数
agent_kwargs = {
    'agent_id': agent_id,
    'model': model_instance,
    'name': agent_name,
    'instructions': instructions,
    'debug_mode': False
}

# 添加可选配置
if tools: agent_kwargs['tools'] = tools
if memory: agent_kwargs['memory'] = memory
if knowledge: agent_kwargs['knowledge'] = knowledge
if guardrails: agent_kwargs['guardrails'] = guardrails
if metadata: agent_kwargs['metadata'] = metadata
if self.db: agent_kwargs['db'] = self.db

# 创建Agent实例
agent = AgnoAgent(**agent_kwargs)
```

### 4. Mock Agent实现
当AGNO框架不可用时，创建Mock Agent作为fallback:

```python
class MockAgent:
    def __init__(self, **kwargs):
        self.agent_id = kwargs.get("agent_id")
        self.name = kwargs.get("name")
        self.model = kwargs.get("model")
        self.instructions = kwargs.get("instructions")
        self.user_id = kwargs.get("user_id")
        # ... 其他属性

    def run(self, message, **kwargs):
        return f"Mock response from {self.name}: {message}"
```

## 错误处理

### 验证错误
- `ValueError("agent_name不能为空")`: 当agent_name为空时
- `ValueError("agent_dict不能为空")`: 当agent_dict为None或空时

### 创建错误
- 模型创建失败时返回None
- AGNO Agent创建失败时自动降级到Mock Agent
- 所有错误都会记录到日志中

## 回调支持

Agent创建成功后会触发以下回调:
```python
self._trigger_callback('agent_switch', {
    'from_agent': self.current_agent_name,
    'to_agent': agent_name,
    'session_id': self.current_session_id,
    'switch_reason': 'agent_creation',
    'agent_id': agent_id
})
```

## 使用示例

### 基本使用
```python
from chat_engine import ChatEngine

# 创建ChatEngine实例
engine = ChatEngine(config_path="test.db", user_id="test_user")

# 创建Agent
agent_config = {
    'agent_id': 'my_agent',
    'name': 'My Assistant',
    'model': {
        'name': 'gpt-4',
        'provider': 'openai',
        'kwargs': {'temperature': 0.7}
    },
    'instructions': '你是一个有用的AI助手。'
}

agent = engine.create_new_agent('My Assistant', agent_config)

if agent:
    print(f"Agent创建成功: {agent.name}")
    # 使用Agent
    response = agent.run("Hello!")
    print(response)
```

### 高级配置
```python
# 包含工具和知识库的Agent
advanced_config = {
    'agent_id': 'advanced_agent',
    'name': 'Advanced Assistant',
    'model': 'gpt-4',
    'instructions': '你是一个具有多种工具的高级AI助手。',
    'tools': ['calculator', 'web_search', 'file_reader'],
    'knowledge': {
        'type': 'vector_db',
        'collection': 'my_documents'
    },
    'memory': {
        'type': 'conversation',
        'max_messages': 50
    }
}

agent = engine.create_new_agent('Advanced Assistant', advanced_config)
```

## 测试

项目包含完整的测试套件:

1. **单元测试**: `tests/test_chat_engine_agent_creation.py`
2. **调试脚本**: `tests/debug_agent_creation.py`

### 运行测试
```bash
# 运行完整测试套件
python tests/test_chat_engine_agent_creation.py

# 运行调试脚本
python tests/debug_agent_creation.py
```

## 依赖关系

### 必需依赖
- Python 3.8+
- SQLite3
- 核心AGNO框架组件（可选，用于完整功能）

### 可选依赖
- AGNO Agent框架: `core.agno.agent.agent`
- AGNO Models: `core.agno.models.base`
- OpenAI API (用于OpenAI模型): `openai`

## 性能考虑

1. **内存使用**: Mock Agent占用内存较少，适合测试环境
2. **创建时间**: AGNO Agent创建时间取决于模型初始化复杂度
3. **数据库连接**: Agent配置可选择性地持久化到数据库
4. **并发支持**: 支持创建多个Agent实例

## 故障排除

### 常见问题

1. **ImportError: 无法导入AGNO框架**
   - 解决方案: 自动降级到Mock Agent模式

2. **模型创建失败**
   - 检查模型配置是否正确
   - 验证API密钥是否设置
   - 确认网络连接

3. **Agent ID冲突**
   - 系统会自动生成唯一ID
   - 建议使用有意义的agent_id前缀

### 调试技巧

1. 启用详细日志: 查看`log_debug`输出
2. 使用调试脚本: `tests/debug_agent_creation.py`
3. 检查Agent属性: 确认所有必需属性已设置
4. 验证模型配置: 确保模型provider和名称正确

## 版本历史

- **v1.0**: 初始实现
  - 支持基本Agent创建
  - Mock Agent fallback
  - 参数验证
  - 错误处理

## 贡献指南

如需扩展此功能，请考虑:

1. **新的模型Provider**: 在`create_model_from_dict`中添加支持
2. **额外的Agent类型**: 扩展Mock Agent功能
3. **配置验证**: 添加更严格的配置验证
4. **性能优化**: 优化Agent创建流程

---

*最后更新: 2025年11月*