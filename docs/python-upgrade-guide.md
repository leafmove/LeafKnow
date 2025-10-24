# Python 升级指南 (3.8 → 3.10+)

## ⚠️ 为什么需要升级？

经过验证，LeafKnow项目的关键依赖包实际上需要**Python 3.10+**：
- **pydantic-ai >=1.4.0**: 需要Python 3.10+
- **markitdown >=0.1.3**: 需要Python 3.10+

## 🎯 升级目标

**从**: Python 3.8.10
**到**: Python 3.10+ (推荐3.11)

## 📋 升级方案

### 方案1: 系统级升级 (推荐)

#### Windows
```bash
# 方法1: 使用winget (推荐)
winget install Python.Python.3.11

# 方法2: 官网下载
# 访问 https://www.python.org/downloads/python-3.11.9/
# 下载并运行安装程序

# 方法3: Microsoft Store
# 搜索"Python 3.11"并安装
```

#### macOS
```bash
# 方法1: 使用brew
brew install python@3.11

# 方法2: 使用pyenv
pyenv install 3.11.9
pyenv global 3.11.9

# 方法3: 官网下载
# 访问 https://www.python.org/downloads/macos/
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# CentOS/RHEL
sudo dnf install python3.11

# 使用pyenv (推荐)
curl https://pyenv.run | bash
pyenv install 3.11.9
pyenv global 3.11.9
```

### 方案2: 虚拟环境 (不影响系统Python)

#### 使用conda
```bash
# 创建新环境
conda create -n leafknow python=3.11

# 激活环境
conda activate leafknow

# 验证版本
python --version
```

#### 使用pyenv
```bash
# 安装Python 3.11
pyenv install 3.11.9

# 在项目目录设置本地Python版本
cd /path/to/LeafKnow
pyenv local 3.11.9

# 验证版本
python --version
```

#### 使用venv
```bash
# 首先需要安装Python 3.11 (见方案1)
# 然后创建虚拟环境
python3.11 -m venv leafknow-env

# 激活虚拟环境
# Windows
leafknow-env\Scripts\activate

# macOS/Linux
source leafknow-env/bin/activate

# 验证版本
python --version
```

## 🔍 验证升级

### 1. 检查Python版本
```bash
python --version
# 应该显示: Python 3.11.x 或更高版本
```

### 2. 运行兼容性测试
```bash
cd api
python test_compatibility.py
```

### 3. 测试项目启动
```bash
cd api
uv sync

uv run main.py --port 60000 --host 127.0.0.1
```

## ⚠️ 注意事项

### 系统级升级风险
1. **依赖冲突**: 可能影响其他Python项目
2. **路径问题**: 需要更新PATH环境变量
3. **权限问题**: 可能需要管理员权限

### 虚拟环境优势
1. **隔离性**: 不影响系统和其他项目
2. **灵活性**: 可以轻松切换Python版本
3. **安全性**: 避免系统级问题

### 推荐做法
- **开发者**: 使用虚拟环境 (conda或pyenv)
- **生产环境**: 系统级升级 (确保兼容性测试)

## 🛠️ 故障排除

### 问题1: 多个Python版本冲突
```bash
# 查看所有Python版本
where python  # Windows
which python  # macOS/Linux

# 使用完整路径
C:\Python311\python.exe --version

# 更新PATH环境变量
# 将新Python版本路径放在前面
```

### 问题2: pip指向错误的Python版本
```bash
# 使用对应版本的pip
python3.11 -m pip --version

# 升级pip
python3.11 -m pip install --upgrade pip
```

### 问题3: 虚拟环境创建失败
```bash
# 确保使用正确的Python版本
python3.11 -m venv myenv

# 如果失败，尝试清除缓存
python3.11 -m venv --clear myenv
```

## 📊 升级后的好处

1. **性能提升**: Python 3.10+比3.8快20-30%
2. **新特性**: 支持match语句、类型提示改进等
3. **兼容性**: 支持所有现代AI/ML库
4. **安全性**: 获得最新的安全更新
5. **生态**: 与Python生态系统保持同步

## 🎯 升级完成后

1. **重新安装项目依赖**:
   ```bash
   cd api
   rm -rf .venv  # 删除旧的虚拟环境
   uv sync       # 重新创建并安装依赖
   ```

2. **更新IDE配置**:
   - VS Code: 更新Python解释器路径
   - PyCharm: 更新项目SDK

3. **测试所有功能**:
   - API服务启动
   - 前端应用运行
   - 所有依赖包导入

---

**总结**: 升级到Python 3.10+是运行LeafKnow项目的必要步骤。推荐使用虚拟环境方案以避免系统级冲突。