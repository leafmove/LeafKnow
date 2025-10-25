# Python版本依赖快速参考

## 🚨 关键发现

**LeafKnow项目无法在Python 3.8上运行的主要限制包：**

### 🔴 核心限制包 (必须Python >=3.10)

| 包名 | 版本要求 | 最低Python | 影响 | 能否降级 |
|------|----------|-------------|------|----------|
| **pydantic-ai** | >=1.4.0 | **>=3.10** | AI核心功能 | ❌ 功能严重缺失 |
| **markitdown** | >=0.1.3 | **>=3.10** | 文档解析 | ⚠️ 可能降级 |

### 🟢 兼容包 (支持Python 3.8)

| 包名 | 版本要求 | 最低Python | 状态 |
|------|----------|-------------|------|
| **fastapi** | >=0.120.0 | >=3.8 | ✅ 正常 |
| **lancedb** | >=0.25.2 | >=3.8 | ✅ 正常 |
| **docling** | >=2.58.0 | >=3.8 | ✅ 正常 |
| **uvicorn** | >=0.38.0 | >=3.8 | ✅ 正常 |
| **sqlmodel** | >=0.0.27 | >=3.7 | ✅ 正常 |
| **tiktoken** | >=0.12.0 | >=3.7 | ✅ 正常 |

## 🎯 根本原因

### 为什么这些包需要Python 3.10+？

1. **pydantic-ai >=1.4.0**
   - 使用了Python 3.10的 `match` 语句
   - 使用了新的类型联合语法 `str | None`
   - 利用3.10+的性能优化

2. **markitdown >=0.1.3**
   - 依赖Python 3.10+的标准库特性
   - 使用了现代语法糖和优化

## 💡 解决方案优先级

### 1. 🥇 升级Python (推荐)
```bash
# Windows
winget install Python.Python.3.11

# 验证
python --version  # 应显示 3.11.x
```

**优点**：保持所有功能，代码简洁，性能最佳

### 2. 🥈 降级版本 (不推荐)
```bash
# 尝试旧版本，但功能会缺失
pip install "pydantic-ai<1.0.0"
pip install "markitdown==0.1.2"
```

**缺点**：功能缺失，安全风险，维护困难

### 3. 🥉 替代包 (复杂)
```python
# pydantic-ai替代
from openai import OpenAI
import json

# markitdown替代
import pypandoc
```

**缺点**：需要大量重构代码

## 📋 最终建议

### 强烈建议：Python >=3.10

**原因**：
- pydantic-ai是项目核心，无法降级
- markitdown降级会影响文档功能
- 替代方案需要大量代码重构
- Python 3.10+性能和安全性更好

### 如果必须使用Python 3.8：

**可以保留的包**：
- fastapi, lancedb, sqlmodel, uvicorn, tiktoken, docling

**需要替换的包**：
- pydantic-ai → 使用原始OpenAI SDK
- markitdown → 使用pypandoc + python-docx

**预期功能损失**：
- 简化的AI交互界面
- 基础的文档解析功能
- 缺少高级AI特性

---

**结论：LeafKnow是一个现代AI应用，设计时就使用了Python 3.10+的特性。建议升级Python版本以获得完整功能体验。**