# 增强版Agno AI聊天应用

这是一个功能丰富的AI聊天应用，基于agno框架构建，支持多种模型提供商、模型管理、配置保存和加载等功能。

## 功能特点

### 🚀 核心功能
- **多模型支持**: 支持OpenAI、Claude、Groq、OpenRouter、Ollama等多种AI模型
- **模型管理**: 添加、删除、切换不同的AI模型
- **配置持久化**: 自动保存和加载模型配置
- **流式/非流式输出**: 支持两种输出模式切换
- **本地模型支持**: 自动检测和管理Ollama本地模型
- **交互式界面**: 友好的命令行交互界面

### 🎯 支持的模型提供商
- **OpenAI**: GPT-4o, GPT-4o-mini等
- **Anthropic**: Claude 3.5 Sonnet等 (需要`pip install anthropic`)
- **Groq**: Llama 3.1等 (需要`pip install groq`)
- **OpenRouter**: 多种第三方模型 (需要`pip install openai`)
- **Ollama**: 本地模型 (需要`pip install ollama`并安装Ollama)

## 安装和使用

### 1. 基础安装
```bash
# 安装agno库 (必须)
pip install agno

# 安装OpenAI支持 (必须)
pip install openai

# 可选：安装其他模型提供商支持
pip install anthropic  # Claude模型
pip install groq        # Groq模型
pip install ollama      # 本地Ollama模型
```

### 2. 环境变量设置 (可选)
```bash
# OpenAI API密钥
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic API密钥
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Groq API密钥
export GROQ_API_KEY="your-groq-api-key"

# OpenRouter API密钥
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### 3. 运行应用
```bash
# 启动交互式聊天应用
python enhanced_chat_app.py
```

## 使用指南

### 启动应用
运行应用后，会显示可用的模型列表和当前选择的模型。

### 聊天命令
- **直接输入问题**: 开始与AI对话
- `models` - 进入模型管理菜单
- `stream` - 切换流式/非流式输出模式
- `system` - 修改系统提示词
- `quit` 或 `exit` - 退出应用

### 模型管理功能
在模型管理菜单中，您可以：

1. **选择模型**: 切换到不同的AI模型
2. **刷新Ollama模型**: 自动检测本地Ollama模型
3. **添加自定义模型**: 添加新的模型配置
4. **删除模型**: 移除不需要的模型配置
5. **保存配置**: 保存当前模型配置到文件
6. **查看当前配置**: 显示当前模型的详细配置

### 添加自定义模型示例
```
模型名称: My Custom Model
模型ID: gpt-3.5-turbo
选择提供商: 1 (openai)
Base URL: https://api.openai.com/v1
API Key: your-api-key
Temperature: 0.7
Max Tokens: 2000
模型描述: 我的自定义GPT模型
```

## Ollama本地模型支持

### 安装Ollama
1. 下载并安装Ollama: https://ollama.ai
2. 启动Ollama服务: `ollama serve`
3. 下载模型: `ollama pull llama3.1:8b`

### 使用本地模型
- 应用会自动检测已安装的Ollama模型
- 在模型管理菜单中选择"刷新Ollama模型"
- 选择本地模型进行对话

## 配置文件

应用会自动创建`model_configs.json`文件来保存模型配置：

```json
{
  "models": {
    "OpenAI GPT-4o-mini": {
      "name": "OpenAI GPT-4o-mini",
      "model_id": "gpt-4o-mini",
      "provider": "openai",
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-...",
      "temperature": 0.7,
      "max_tokens": 2000,
      "description": "OpenAI的GPT-4o mini模型",
      "is_local": false
    }
  },
  "current_model": "OpenAI GPT-4o-mini"
}
```

## 错误处理

### 常见错误和解决方案

1. **API密钥错误**
   ```
   [错误] 聊天失败: Incorrect API key provided
   ```
   解决方案: 检查环境变量或模型配置中的API密钥

2. **模型库未安装**
   ```
   [警告] anthropic库未安装，Claude模型功能不可用
   ```
   解决方案: 运行 `pip install anthropic`

3. **Ollama连接失败**
   ```
   [警告] 无法获取Ollama模型列表
   ```
   解决方案: 确保Ollama已安装并运行

4. **网络连接问题**
   ```
   [错误] 聊天失败: Connection error
   ```
   解决方案: 检查网络连接和API端点

## 高级用法

### 编程方式使用
```python
from enhanced_chat_app import EnhancedChatApp, ModelManager, ModelConfig

# 创建模型管理器
manager = ModelManager()

# 添加自定义模型
config = ModelConfig(
    name="Custom Model",
    model_id="gpt-4",
    provider="openai",
    api_key="your-api-key",
    temperature=0.7
)
manager.add_model(config)

# 创建聊天应用
app = EnhancedChatApp()
app.model_manager = manager
app._create_current_agent()

# 进行对话
response = app.chat_non_streaming("你好！")
print(response)
```

### 批量添加模型
```python
# 添加多个OpenRouter模型
models = [
    ("OpenRouter Mistral", "mistralai/mistral-7b-instruct"),
    ("OpenRouter Llama", "meta-llama/llama-3.1-8b-instruct"),
]

for name, model_id in models:
    config = ModelConfig(
        name=name,
        model_id=model_id,
        provider="openrouter",
        api_key="your-openrouter-key"
    )
    manager.add_model(config)
```

## 故障排除

### 性能优化
- 对于本地模型，确保有足够的内存和计算资源
- 使用流式输出以获得更好的用户体验
- 调整temperature参数以平衡创造性和准确性

### 调试模式
应用提供了详细的错误信息，帮助您诊断问题：
- `[OK]` - 操作成功
- `[警告]` - 非致命问题，应用可继续运行
- `[错误]` - 严重问题，需要处理

## 许可证

此项目仅供学习和参考使用。