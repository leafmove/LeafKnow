# Agent 管理模块集成指南

本指南介绍如何将 agno_modular 中的 Agent 管理功能集成到现有的 LeafKnow 应用中。

## 集成步骤

### 1. 数据库初始化

在 `main.py` 中添加 Agent 表的初始化：

```python
# 在现有的数据库初始化代码中添加
from agno_modular.agent_models import init_agent_tables

# 在 DBManager.init_db() 方法中调用
def init_db(self) -> bool:
    # ... 现有的初始化代码 ...

    # 初始化 Agent 相关表
    init_agent_tables(self)

    return True
```

### 2. 依赖注入配置

在应用启动时配置 Agent 管理器：

```python
# 在 main.py 中添加
from agno_modular.agent_manager import AgentCRUDManager
from agno_modular.agent_api import init_agent_api

# 创建全局实例
agent_manager = AgentCRUDManager(db_manager, models_manager)

# 注册 API 路由
app.include_router(init_agent_api(db_manager, models_manager))
```

### 3. 模型管理器扩展

扩展 `ModelsManager` 以支持 Agent 模型配置：

```python
# 在 models_mgr.py 中添加方法
class ModelsManager:
    # ... 现有方法 ...

    def get_model_by_config_id(self, config_id: int) -> Optional[Any]:
        """根据配置ID获取模型实例"""
        with Session(self.engine) as session:
            stmt = select(ModelConfiguration).where(ModelConfiguration.id == config_id)
            config = session.exec(stmt).first()

            if not config:
                return None

            # 根据配置创建模型实例
            return self.create_model_from_config(config)

    def create_model_from_config(self, config: ModelConfiguration) -> Any:
        """根据配置创建模型实例"""
        # 实现模型创建逻辑
        provider = self.get_provider_by_id(config.provider_id)
        if not provider:
            return None

        # 根据provider类型创建对应的模型
        # ... 实现细节 ...
        pass
```

### 4. 会话管理集成

将 Agent 功能集成到现有的聊天会话系统：

```python
# 在 chatsession_mgr.py 中添加 Agent 支持
from agno_modular.agent_manager import AgentCRUDManager

class ChatSessionManager:
    def __init__(self, db_manager: DBManager, models_manager: ModelsManager):
        # ... 现有初始化 ...
        self.agent_manager = AgentCRUDManager(db_manager, models_manager)

    async def process_message_with_agent(
        self,
        session_id: int,
        agent_id: int,
        message: str,
        user_id: int
    ) -> str:
        """使用指定Agent处理消息"""
        try:
            response = self.agent_manager.run_agent(
                agent_id=agent_id,
                message=message,
                session_id=str(session_id),
                user_id=user_id
            )

            # 保存聊天记录
            await self.save_message(session_id, "user", message)
            await self.save_message(session_id, "assistant", response)

            return response
        except Exception as e:
            raise e
```

### 5. 前端集成

为前端添加 Agent 管理接口：

```typescript
// 在前端添加 Agent 相关的 API 调用
interface Agent {
  id: number;
  name: string;
  description?: string;
  agent_type: string;
  status: string;
  capabilities: string[];
  // ... 其他字段
}

class AgentAPI {
  private baseURL = '/api/agents';

  async createAgent(data: any): Promise<Agent> {
    const response = await fetch(`${this.baseURL}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${this.baseURL}/`);
    return response.json();
  }

  async runAgent(agentId: number, message: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/${agentId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return response.json();
  }

  // ... 其他方法
}
```

## 配置文件更新

### 1. 环境变量

在 `.env` 文件中添加 Agent 相关配置：

```env
# Agent 配置
AGENT_MAX_MEMORY_ENTRIES=1000
AGENT_DEFAULT_RETENTION_DAYS=30
AGENT_DEBUG_MODE=false
AGENT_ENABLE_LOGGING=true

# 记忆配置
AGENT_MEMORY_DB_PATH=./data/agent_memory.db
AGENT_MEMORY_TABLE_PREFIX=agent_
```

### 2. 配置文件

在 `config.py` 中添加 Agent 配置：

```python
# Agent 配置
AGENT_CONFIG = {
    "max_memory_entries": 1000,
    "default_retention_days": 30,
    "debug_mode": False,
    "enable_logging": True,
    "memory_config": {
        "db_path": "./data/agent_memory.db",
        "table_prefix": "agent_"
    }
}
```

## 权限和安全

### 1. 用户权限

确保每个用户只能访问自己的 Agent：

```python
# 在 agent_api.py 中添加权限检查
from fastapi import HTTPException
import jwt

def get_current_user_id(request: Request) -> int:
    """从请求中获取当前用户ID"""
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# 在API端点中使用
@router.post("/")
async def create_agent(
    request: AgentCreateRequest,
    user_id: int = Depends(get_current_user_id),
    manager: AgentCRUDManager = Depends(get_agent_manager)
):
    # 使用用户ID创建Agent
    return await create_agent(request, user_id, manager)
```

### 2. 数据验证

添加严格的输入验证：

```python
from pydantic import validator

class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        # 禁止特殊字符
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5_\-\s]+$', v):
            raise ValueError('名称包含无效字符')
        return v

    @validator('system_prompt')
    def validate_prompt(cls, v):
        if v and len(v) > 10000:
            raise ValueError('系统提示词过长')
        return v
```

## 监控和日志

### 1. 日志配置

配置 Agent 操作的日志记录：

```python
import logging

# 配置日志
agent_logger = logging.getLogger('agent_manager')
agent_logger.setLevel(logging.INFO)

# 添加文件处理器
handler = logging.FileHandler('logs/agent_operations.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
agent_logger.addHandler(handler)

# 在关键操作中记录日志
def create_agent(self, **kwargs):
    agent_logger.info(f"Creating agent: {kwargs.get('name')}")
    # ... 创建逻辑 ...
    agent_logger.info(f"Agent created successfully: {agent.id}")
```

### 2. 性能监控

添加性能监控指标：

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            agent_logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            agent_logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

# 应用到关键方法
@monitor_performance
async def run_agent(self, agent_id: int, message: str, **kwargs):
    # ... 运行逻辑 ...
```

## 测试策略

### 1. 单元测试

```python
import pytest
from agno_modular.agent_manager import AgentCRUDManager

class TestAgentManager:
    def setup_method(self):
        # 设置测试环境
        self.test_db = create_test_database()
        self.agent_manager = AgentCRUDManager(self.test_db, MockModelsManager())

    def test_create_agent(self):
        agent = self.agent_manager.create_custom_agent(
            name="Test Agent",
            agent_type=AgentType.QA,
            user_id=1
        )
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.QA.value

    def test_run_agent(self):
        # 创建测试Agent
        agent = self.agent_manager.create_custom_agent(
            name="Test Agent",
            agent_type=AgentType.QA,
            user_id=1
        )

        # 运行Agent
        response = self.agent_manager.run_agent(
            agent_id=agent.id,
            message="Hello",
            user_id=1
        )

        assert response is not None
```

### 2. 集成测试

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_agent_api():
    # 测试创建Agent
    response = client.post("/api/agents/", json={
        "name": "Test API Agent",
        "agent_type": "qa"
    })
    assert response.status_code == 201

    agent_data = response.json()
    agent_id = agent_data["id"]

    # 测试运行Agent
    response = client.post(f"/api/agents/{agent_id}/run", json={
        "message": "Hello"
    })
    assert response.status_code == 200

    # 测试获取Agent
    response = client.get(f"/api/agents/{agent_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test API Agent"
```

## 部署注意事项

### 1. 数据库迁移

```python
# 创建数据库迁移脚本
def migrate_agent_tables():
    """迁移Agent相关表结构"""
    inspector = inspect(engine)

    with Session(engine) as session:
        # 检查并创建新表
        if not inspector.has_table("t_agents"):
            Agent.__table__.create(engine)
            print("Created t_agents table")

        # 添加新字段（如果需要）
        try:
            session.execute(text("ALTER TABLE t_agents ADD COLUMN metadata_json TEXT"))
            session.commit()
        except Exception as e:
            print(f"Column already exists: {e}")
```

### 2. 性能优化

```python
# 数据库连接池配置
def create_optimized_db_engine():
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        echo=False
    )

    # 设置SQLite优化参数
    if database_url.startswith("sqlite"):
        setup_sqlite_optimization(engine)

    return engine

def setup_sqlite_optimization(engine):
    """设置SQLite优化参数"""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-65536")
        cursor.close()
```

### 3. 错误处理

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    agent_logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """值错误处理"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## 维护和升级

### 1. 版本管理

```python
# 在数据库中添加版本表
class AgentSystemVersion(SQLModel, table=True):
    __tablename__ = "t_agent_system_version"

    id: int = Field(default=None, primary_key=True)
    version: str = Field(unique=True)
    migration_date: datetime = Field(default_factory=datetime.now)
    description: str

def check_and_migrate():
    """检查版本并执行迁移"""
    current_version = get_current_version()
    latest_version = "1.0.0"

    if current_version != latest_version:
        migrate_to_latest()
        update_version(latest_version)
```

### 2. 备份策略

```python
def backup_agent_data():
    """备份Agent数据"""
    backup_dir = f"backups/agent_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 备份配置数据
    with Session(engine) as session:
        agents = session.exec(select(Agent)).all()
        backup_data = {
            "agents": [agent.dict() for agent in agents],
            "templates": [template.dict() for template in session.exec(select(AgentConfigTemplate)).all()],
            "backup_time": datetime.now().isoformat()
        }

    # 保存到文件
    with open(f"{backup_dir}/agent_data.json", "w") as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"Agent data backed up to {backup_dir}")
```

通过以上集成步骤，可以将 Agent 管理功能完全集成到现有的 LeafKnow 应用中，提供完整的 Agent 创建、管理和使用能力。