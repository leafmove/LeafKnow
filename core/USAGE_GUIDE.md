# 增强版聊天应用使用指南

## 问题修复

✅ **已修复**: Ollama模型支持和模型切换问题

- 修复了Ollama模型创建参数错误
- 修复了流式聊天API调用问题
- 添加了智能模型切换功能

## 主要功能

### 1. 智能模型切换

现在可以直接在聊天中输入 `模型名: 消息` 来切换模型：

```bash
# 支持的格式示例
用户 [当前模型]: Ollama deepseek-r1:1.5b: 你好
用户 [当前模型]: deepseek-r1:1.5b: hello
用户 [当前模型]: ollama llama3: tell me a joke
用户 [当前模型]: llama3:2b: 你好吗
```

### 2. 自动模型识别

应用会智能识别：
- **已存在的模型**: 直接切换
- **Ollama模型**: 自动添加并切换
- **常见模型名称**: 支持deepseek、llama、qwen、mistral等

### 3. 完整的模型管理

```bash
# 启动应用
python enhanced_chat_app.py

# 聊天命令
models          # 进入模型管理菜单
stream          # 切换流式/非流式模式
system          # 修改系统提示词
quit            # 退出应用
```

## Ollama本地模型使用

### 1. 安装Ollama
```bash
# 下载安装: https://ollama.ai

# 启动服务
ollama serve

# 下载模型
ollama pull deepseek-r1:1.5b
ollama pull llama3
ollama pull qwen
```

### 2. 在应用中使用
```bash
# 方式1: 直接切换
用户: deepseek-r1:1.5b: 你好

# 方式2: 通过模型管理
models -> 选择"刷新Ollama模型" -> 选择模型
```

## 错误解决

### 常见错误和解决方案

1. **"No auth credentials found"**
   - 检查API密钥设置
   - 对于Ollama，确保本地服务运行

2. **"ollama库未安装"**
   ```bash
   pip install ollama
   ```

3. **"无法获取Ollama模型列表"**
   - 确保Ollama服务运行: `ollama serve`
   - 检查模型是否已安装: `ollama list`

4. **"模型创建失败"**
   - 检查网络连接
   - 验证API地址和密钥

## 配置示例

### OpenAI模型
```json
{
  "name": "OpenAI GPT-4o-mini",
  "model_id": "gpt-4o-mini",
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Ollama本地模型
```json
{
  "name": "Ollama deepseek-r1:1.5b",
  "model_id": "deepseek-r1:1.5b",
  "provider": "ollama",
  "base_url": "http://localhost:11434",
  "is_local": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

## 快速测试

```bash
# 运行测试
python test_fix.py

# 运行演示
python demo_enhanced_app.py

# 启动应用
python enhanced_chat_app.py
```

## 技术改进

1. **模型参数适配**: 正确处理不同模型的参数差异
2. **智能解析**: 支持多种模型名称格式
3. **错误处理**: 完善的错误提示和恢复机制
4. **自动发现**: 动态添加和配置Ollama模型

现在您可以：
- ✅ 直接输入 `Ollama deepseek-r1:1.5b: 你好` 使用本地模型
- ✅ 应用会自动识别并添加Ollama模型
- ✅ 流式和非流式输出都正常工作
- ✅ 配置自动保存和加载