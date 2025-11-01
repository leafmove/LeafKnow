# agno SQLite Integration

This module provides complete SQLite database support for the agno AI Agent framework, covering all aspects of agent data persistence.

## Features

### 📊 Complete Data Coverage

1. **配置数据 (Configuration Data)**
   - Agent configurations: models, instructions, tools, knowledge
   - Tool configurations: function definitions, metadata
   - Model configurations: providers, parameters, capabilities

2. **运行数据 (Runtime Data)**
   - Execution traces and reasoning steps
   - Tool calls and their results
   - Performance metrics and timing
   - Error tracking and debugging info

3. **会话数据 (Session Data)**
   - Agent, team, and workflow sessions
   - Conversation history and context
   - Session metadata and statistics

4. **记忆数据 (Memory Data)**
   - User preferences and learning
   - Long-term agent memories
   - Topic-based memory organization

5. **评估数据 (Evaluation Data)**
   - Performance metrics and scores
   - Test results and comparisons
   - Quality assessments

6. **知识数据 (Knowledge Data)**
   - Document storage and retrieval
   - Knowledge base management
   - Content metadata and indexing

## Quick Start

### Basic Usage

```python
from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb

# Create database
db = ExtendedSqliteDb(db_file="./my_agno.db")

# Save agent configuration
from core.agno.db.sqlite.config_data import AgentConfig
config = AgentConfig(
    agent_id="agent-001",
    name="My Agent",
    model_id="gpt-4",
    model_provider="openai",
    instructions="You are a helpful assistant"
)
db.upsert_agent_config(config)

# Save runtime data
from core.agno.db.sqlite.runtime_data import RuntimeData
runtime = RuntimeData(
    run_id="run-001",
    agent_id="agent-001",
    input_data={"query": "Hello"},
    status="completed"
)
db.upsert_runtime_data(runtime)
```

### Advanced Usage

```python
# Get agent statistics
stats = db.get_agent_statistics("agent-001")
print(f"Success rate: {stats['success_rate']:.2%}")

# Get database overview
db_stats = db.get_database_statistics()
print(f"Total records: {db_stats}")

# Query runtime data
runtime_list = db.get_runtime_data_list(
    agent_id="agent-001",
    status="completed",
    limit=100
)
```

## Data Models

### AgentConfig

```python
@dataclass
class AgentConfig:
    agent_id: str
    name: str
    model_id: Optional[str] = None
    model_provider: Optional[str] = None
    model_kwargs: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    knowledge: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    guardrails: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    user_id: Optional[str] = None
    status: str = "active"
```

### RuntimeData

```python
@dataclass
class RuntimeData:
    run_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    status: str = "running"
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
```

## Database Schema

### Core Tables

| Table Name | Description | Key Fields |
|------------|-------------|------------|
| `agno_sessions` | Agent/team/workflow sessions | session_id, session_type, agent_id |
| `agno_memories` | User memories | memory_id, agent_id, user_id |
| `agno_eval_runs` | Evaluation data | run_id, eval_type, agent_id |
| `agno_knowledge` | Knowledge base | id, name, content |
| `agno_culture` | Cultural knowledge | id, name, content |
| `agno_metrics` | Usage metrics | date, metrics_data |

### Extended Tables

| Table Name | Description | Key Fields |
|------------|-------------|------------|
| `agno_agent_config` | Agent configurations | agent_id, name, model_id |
| `agno_tools_config` | Tool configurations | tool_id, name, function_definition |
| `agno_runtime_data` | Runtime execution data | run_id, agent_id, status |

## API Reference

### Configuration Methods

```python
# Agent Configuration
db.upsert_agent_config(config: AgentConfig) -> AgentConfig
db.get_agent_config(agent_id: str) -> Optional[AgentConfig]
db.get_agent_configs(user_id: str, status: str, limit: int) -> List[AgentConfig]
db.delete_agent_config(agent_id: str) -> bool

# Tool Configuration
db.upsert_tool_config(config: ToolConfig) -> ToolConfig
db.get_tool_config(tool_id: str) -> Optional[ToolConfig]
db.get_tool_configs(agent_id: str, status: str, limit: int) -> List[ToolConfig]
```

### Runtime Data Methods

```python
# Runtime Data
db.upsert_runtime_data(data: RuntimeData) -> RuntimeData
db.get_runtime_data(run_id: str) -> Optional[RuntimeData]
db.get_runtime_data_list(session_id, agent_id, user_id, status, limit) -> List[RuntimeData]
db.update_runtime_data_status(run_id, status, error_message) -> bool
```

### Statistics Methods

```python
# Analytics
db.get_agent_statistics(agent_id: str) -> Dict[str, Any]
db.get_database_statistics() -> Dict[str, Any]
```

## Performance Optimizations

### Indexes

The database automatically creates indexes for optimal query performance:

```sql
-- Agent configuration indexes
CREATE INDEX idx_agent_config_agent_id ON agno_agent_config(agent_id);
CREATE INDEX idx_agent_config_user_id ON agno_agent_config(user_id);
CREATE INDEX idx_agent_config_status ON agno_agent_config(status);

-- Runtime data indexes
CREATE INDEX idx_runtime_data_run_id ON agno_runtime_data(run_id);
CREATE INDEX idx_runtime_data_session_id ON agno_runtime_data(session_id);
CREATE INDEX idx_runtime_data_agent_id ON agno_runtime_data(agent_id);
CREATE INDEX idx_runtime_data_status ON agno_runtime_data(status);
CREATE INDEX idx_runtime_data_created_at ON agno_runtime_data(created_at);
```

### Bulk Operations

```python
# Bulk upsert sessions
sessions = [session1, session2, session3]
results = db.upsert_sessions(sessions, deserialize=True)

# Bulk upsert memories
memories = [memory1, memory2, memory3]
results = db.upsert_memories(memories, deserialize=True)
```

## Integration Examples

See `examples.py` for complete usage examples:

```bash
python -m core.agno.db.sqlite.examples
```

### Complete Workflow Example

```python
from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb
from core.agno.db.sqlite.config_data import AgentConfig
from core.agno.db.sqlite.runtime_data import RuntimeData

# 1. Initialize database
db = ExtendedSqliteDb(db_file="./production.db")

# 2. Configure agent
config = AgentConfig(
    agent_id="customer-service",
    name="Customer Service Bot",
    model_id="gpt-4",
    model_provider="openai",
    instructions="Help customers with their inquiries"
)
db.upsert_agent_config(config)

# 3. Track execution
runtime = RuntimeData(
    run_id="run-123",
    agent_id="customer-service",
    input_data={"user_query": "How do I return an item?"},
    reasoning_steps=[...],
    tool_calls=[...],
    metrics={"response_time": 2.3, "tokens": 150},
    status="completed"
)
db.upsert_runtime_data(runtime)

# 4. Analyze performance
stats = db.get_agent_statistics("customer-service")
print(f"Agent success rate: {stats['success_rate']:.2%}")
```

## Migration from Other Databases

```python
# From PostgreSQL to SQLite
from core.agno.db.sqlite.sqlite import SqliteDb

sqlite_db = SqliteDb(db_file="./migrated.db")

# Migrate sessions (if needed)
sqlite_db.migrate_table_from_v1_to_v2(
    v1_db_schema="public",
    v1_table_name="agent_sessions",
    v1_table_type="agent_sessions"
)
```

## Backup and Recovery

```python
import shutil
from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb

# Create backup
db = ExtendedSqliteDb(db_file="./production.db")
shutil.copy2(db.db_file, "./backup/agno_backup.db")

# Recovery is simply copying the backup file back
shutil.copy2("./backup/agno_backup.db", "./recovered.db")
```

## Best Practices

1. **Connection Management**: Use a single database instance per application
2. **Bulk Operations**: Use bulk upsert methods for better performance
3. **Indexing**: The database automatically creates necessary indexes
4. **Error Handling**: Always wrap database operations in try-catch blocks
5. **Backup Strategy**: Regular backups of the SQLite file

## Troubleshooting

### Database Lock Issues

```python
# Handle database locks gracefully
from contextlib import contextmanager

@contextmanager
def safe_db_operation(db):
    try:
        yield db
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            time.sleep(0.1)  # Brief delay
            yield db
        else:
            raise
```

### Performance Issues

```python
# Use WAL mode for better concurrency
db = ExtendedSqliteDb(db_file="./production.db")
with db._get_connection() as conn:
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
```

## License

This SQLite integration is part of the agno framework and follows the same licensing terms.