# Multi-Provider Model Support Implementation

## 概述

本文档描述了ChatEngine中`create_model_from_dict`函数的实现，该函数支持从配置字典创建多种Provider的AI模型实例。

## 支持的Provider

### 1. OpenAI
- **类**: `core.agno.models.openai.chat.OpenAIChat`
- **默认模型**: `gpt-4`
- **主要特性**: 支持结构化输出、流式响应、工具调用

### 2. Ollama
- **类**: `core.agno.models.ollama.chat.Ollama`
- **默认模型**: `llama3.1`
- **主要特性**: 本地模型支持、多模态输入、流式响应

### 3. DeepSeek
- **类**: `core.agno.models.deepseek.deepseek.DeepSeek`
- **默认模型**: `deepseek-chat`
- **主要特性**: 高性价比、API兼容OpenAI

### 4. SiliconFlow
- **类**: `core.agno.models.siliconflow.siliconflow.Siliconflow`
- **默认模型**: `Qwen/QwQ-32B`
- **主要特性**: 国产模型服务、API兼容OpenAI

### 5. OpenRouter
- **类**: `core.agno.models.openrouter.openrouter.OpenRouter`
- **默认模型**: `gpt-4o`
- **主要特性**: 模型路由、fallback机制、多模型支持

## 核心功能

### create_model_from_dict方法

```python
def create_model_from_dict(self, model_dict):
    """
    根据字典创建model实例

    支持OpenAI、Ollama、DeepSeek、SiliconFlow、OpenRouter等Provider

    Args:
        model_dict: 包含model配置的字典，必须包含:
            - name: 模型名称
            - provider: Provider名称 (openai, ollama, deepseek, siliconflow, openrouter)
            - kwargs: 模型参数字典 (可选)

    Returns:
        model实例或None (创建失败时)
    """
```

### 配置格式

#### 通用配置格式
```python
model_config = {
    'name': 'model-name',           # 必需：模型名称
    'provider': 'provider-name',    # 可选：Provider名称，默认'openai'
    'kwargs': {                     # 可选：模型参数
        'api_key': 'your-api-key',
        'temperature': 0.7,
        'max_tokens': 1000,
        # 其他Provider特定参数
    }
}
```

#### Provider特定配置示例

**OpenAI配置**
```python
openai_config = {
    'name': 'gpt-4',
    'provider': 'openai',
    'kwargs': {
        'api_key': 'sk-xxx',
        'organization': 'org-xxx',
        'temperature': 0.7,
        'max_tokens': 1000,
        'max_completion_tokens': 1500,
        'top_p': 0.9,
        'frequency_penalty': 0.1,
        'presence_penalty': 0.1,
        'seed': 42,
        'base_url': 'https://api.openai.com/v1',
        'timeout': 30,
        'max_retries': 3
    }
}
```

**Ollama配置**
```python
ollama_config = {
    'name': 'llama3.1',
    'provider': 'ollama',
    'kwargs': {
        'host': 'http://localhost:11434',
        'timeout': 60,
        'api_key': 'ollama-api-key',  # 可选，用于Ollama Cloud
        'format': 'json',            # 结构化输出格式
        'options': {
            'temperature': 0.8,
            'top_p': 0.9,
            'num_ctx': 2048
        },
        'keep_alive': '5m'
    }
}
```

**DeepSeek配置**
```python
deepseek_config = {
    'name': 'deepseek-chat',
    'provider': 'deepseek',
    'kwargs': {
        'api_key': 'sk-xxx',
        'base_url': 'https://api.deepseek.com',
        'temperature': 0.6,
        'max_tokens': 2000,
        'top_p': 0.95
    }
}
```

**SiliconFlow配置**
```python
siliconflow_config = {
    'name': 'Qwen/QwQ-32B',
    'provider': 'siliconflow',
    'kwargs': {
        'api_key': 'sk-xxx',
        'base_url': 'https://api.siliconflow.com/v1',
        'temperature': 0.5,
        'max_tokens': 1500
    }
}
```

**OpenRouter配置**
```python
openrouter_config = {
    'name': 'gpt-4o',
    'provider': 'openrouter',
    'kwargs': {
        'api_key': 'sk-or-xxx',
        'max_tokens': 1024,
        'models': [  # fallback模型列表
            'anthropic/claude-sonnet-4',
            'deepseek/deepseek-r1'
        ]
    }
}
```

## 实现架构

### 方法结构
```
create_model_from_dict()
├── 参数验证
├── Provider路由
│   ├── _create_openai_model()
│   ├── _create_ollama_model()
│   ├── _create_deepseek_model()
│   ├── _create_siliconflow_model()
│   ├── _create_openrouter_model()
│   └── _create_mock_model() (fallback)
└── 错误处理和日志记录
```

### 关键特性

1. **智能路由**: 根据provider参数自动选择对应的创建方法
2. **参数映射**: 将通用参数映射到Provider特定的参数
3. **空值过滤**: 自动过滤None值，避免传递无效参数
4. **降级机制**: 当Provider库不可用时，自动降级到Mock模型
5. **错误处理**: 完整的错误处理和日志记录

### Mock模型支持

当对应的Provider库不可用时，系统会自动创建Mock模型：

```python
class MockModel:
    def __init__(self, model_id: str, provider: str, **model_kwargs):
        self.id = model_id
        self.name = f"Mock{provider.capitalize()}Model"
        self.provider = provider.capitalize()
        self.kwargs = model_kwargs

    def invoke(self, *args, **kwargs):
        return MockModelResponse(f"Mock response from {self.provider} model {self.id}")

    async def ainvoke(self, *args, **kwargs):
        return MockModelResponse(f"Mock async response from {self.provider} model {self.id}")
```

## 使用示例

### 基本使用
```python
from chat_engine import ChatEngine

# 创建ChatEngine实例
engine = ChatEngine(config_path="test.db", user_id="test_user")

# 创建OpenAI模型
openai_model = engine.create_model_from_dict({
    'name': 'gpt-4',
    'provider': 'openai',
    'kwargs': {
        'api_key': 'sk-xxx',
        'temperature': 0.7
    }
})

# 创建Agent
agent_config = {
    'agent_id': 'my_agent',
    'name': 'My Agent',
    'model': {
        'name': 'gpt-4',
        'provider': 'openai',
        'kwargs': {'api_key': 'sk-xxx'}
    },
    'instructions': '你是一个有用的AI助手。'
}

agent = engine.create_new_agent('My Agent', agent_config)
```

### 多Provider切换
```python
providers = [
    {'name': 'gpt-4', 'provider': 'openai', 'kwargs': {'api_key': 'sk-openai'}},
    {'name': 'llama3.1', 'provider': 'ollama', 'kwargs': {'host': 'http://localhost:11434'}},
    {'name': 'deepseek-chat', 'provider': 'deepseek', 'kwargs': {'api_key': 'sk-deepseek'}},
    {'name': 'Qwen/QwQ-32B', 'provider': 'siliconflow', 'kwargs': {'api_key': 'sk-siliconflow'}},
    {'name': 'gpt-4o', 'provider': 'openrouter', 'kwargs': {'api_key': 'sk-openrouter'}}
]

for model_config in providers:
    model = engine.create_model_from_dict(model_config)
    print(f"Created model: {model.name} ({model.provider})")

    # 创建对应的Agent
    agent_config = {
        'agent_id': f"agent_{model_config['provider']}",
        'name': f"Agent {model_config['provider'].title()}",
        'model': model_config,
        'instructions': f'You are an AI assistant using {model_config["provider"].title()}.'
    }

    agent = engine.create_new_agent(agent_config['name'], agent_config)
```

## 错误处理

### 常见错误类型

1. **参数验证错误**
   - `model_dict`为None或空字典
   - 缺少必需的`name`字段
   - 不支持的provider类型

2. **导入错误**
   - Provider库未安装
   - 模块导入失败
   - 自动降级到Mock模型

3. **创建错误**
   - API密钥无效
   - 模型参数错误
   - 网络连接问题

### 错误处理策略

```python
try:
    model = engine.create_model_from_dict(model_config)
    if model:
        # 使用模型
        pass
    else:
        # 处理创建失败
        print("模型创建失败")
except Exception as e:
    # 处理异常
    print(f"模型创建异常: {e}")
```

## 测试

### 测试覆盖
- ✅ 所有Provider的模型创建
- ✅ 参数验证和错误处理
- ✅ Mock模型降级机制
- ✅ 最小配置支持
- ✅ Agent集成测试

### 运行测试
```bash
# 运行完整测试套件
python tests/test_multi_provider_models.py

# 运行调试脚本
python tests/debug_multi_provider_models.py
```

## 性能考虑

1. **懒加载**: 只在需要时导入Provider库
2. **参数过滤**: 避免传递无效参数
3. **错误缓存**: 避免重复的错误尝试
4. **内存管理**: Mock模型占用更少内存

## 扩展性

### 添加新Provider

1. 在`create_model_from_dict`中添加新的provider分支
2. 实现`_create_newprovider_model`方法
3. 添加对应的测试用例

```python
elif provider == 'newprovider':
    return self._create_newprovider_model(name, kwargs)

def _create_newprovider_model(self, name: str, kwargs: dict):
    """创建NewProvider模型实例"""
    try:
        from core.agno.models.newprovider.chat import NewProviderModel

        newprovider_params = {
            'id': name,
            'name': kwargs.get('name', 'NewProvider'),
            'api_key': kwargs.get('api_key'),
            # 其他参数映射
        }

        model = NewProviderModel(**newprovider_params)
        log_debug(f"Created NewProvider model: {name}")
        return model

    except ImportError:
        log_warning("NewProvider库未安装，创建Mock模型")
        return self._create_mock_model(name, 'newprovider', kwargs)
```

## 最佳实践

1. **配置管理**: 使用环境变量存储API密钥
2. **错误处理**: 始终检查模型创建结果
3. **资源清理**: 及时释放模型资源
4. **日志记录**: 启用详细日志用于调试
5. **测试覆盖**: 为新的配置编写测试

## 故障排除

### 常见问题

1. **导入错误**
   - 确保安装了对应的Provider库
   - 检查Python路径设置
   - 查看错误日志获取详细信息

2. **API密钥错误**
   - 验证API密钥有效性
   - 检查环境变量设置
   - 确认API访问权限

3. **模型参数错误**
   - 查看Provider文档了解支持的参数
   - 检查参数类型和范围
   - 使用最小配置进行测试

4. **网络连接问题**
   - 检查网络连接
   - 验证API端点URL
   - 配置代理设置（如需要）

---

*最后更新: 2025年11月*