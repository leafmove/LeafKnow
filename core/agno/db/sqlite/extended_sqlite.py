"""Extended SQLite implementation with configuration and runtime data support."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from core.agno.db.sqlite.sqlite import SqliteDb
from core.agno.db.sqlite.config_data import AgentConfig, ToolConfig, ModelConfig
from core.agno.db.sqlite.runtime_data import RuntimeData, ReasoningStep, ToolCallRecord
from core.agno.utils.log import log_debug, log_error, log_info

try:
    from sqlalchemy import text
except ImportError:
    def text(sql):
        return sql


class ExtendedSqliteDb(SqliteDb):
    """Extended SQLite database implementation with configuration and runtime data support."""

    def __init__(self, *args, **kwargs):
        """Initialize extended SQLite database."""
        super().__init__(*args, **kwargs)

        # Initialize additional tables
        self._initialize_extended_tables()

    def _get_connection(self):
        """Get database connection context manager."""
        return self.Session()

    def _initialize_extended_tables(self):
        """Initialize configuration and runtime data tables."""
        try:
            with self._get_connection() as conn:
                # Create agent config table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS agno_agent_config (
                        agent_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        model_id TEXT,
                        model_provider TEXT,
                        model_kwargs TEXT,
                        instructions TEXT,
                        tools TEXT,
                        knowledge TEXT,
                        memory TEXT,
                        guardrails TEXT,
                        metadata TEXT,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER,
                        user_id TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """))

                # Create tools config table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS agno_tools_config (
                        tool_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        function_definition TEXT NOT NULL,
                        metadata TEXT,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER,
                        agent_id TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """))

                # Create runtime data table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS agno_runtime_data (
                        run_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        agent_id TEXT,
                        user_id TEXT,
                        input_data TEXT NOT NULL,
                        output_data TEXT,
                        reasoning_steps TEXT,
                        tool_calls TEXT,
                        metrics TEXT,
                        status TEXT DEFAULT 'running',
                        error_message TEXT,
                        execution_time REAL,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER
                    )
                """))

                # Create indexes for better performance
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agent_config_agent_id ON agno_agent_config(agent_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agent_config_user_id ON agno_agent_config(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agent_config_status ON agno_agent_config(status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tools_config_tool_id ON agno_tools_config(tool_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tools_config_agent_id ON agno_tools_config(agent_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_data_run_id ON agno_runtime_data(run_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_data_session_id ON agno_runtime_data(session_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_data_agent_id ON agno_runtime_data(agent_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_data_status ON agno_runtime_data(status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_data_created_at ON agno_runtime_data(created_at)"))

                conn.commit()
                log_info("Extended SQLite tables initialized successfully")

        except Exception as e:
            log_error(f"Error initializing extended tables: {e}")
            raise

    # --- Agent Configuration Methods ---

    def upsert_agent_config(self, config: AgentConfig) -> AgentConfig:
        """Insert or update agent configuration."""
        try:
            with self._get_connection() as conn:
                current_time = int(time.time())
                if config.created_at is None:
                    config.created_at = current_time
                config.updated_at = current_time

                conn.execute(text("""
                    INSERT OR REPLACE INTO agno_agent_config (
                        agent_id, name, model_id, model_provider, model_kwargs, instructions,
                        tools, knowledge, memory, guardrails, metadata, created_at, updated_at, user_id, status
                    ) VALUES (
                        :agent_id, :name, :model_id, :model_provider, :model_kwargs, :instructions,
                        :tools, :knowledge, :memory, :guardrails, :metadata, :created_at, :updated_at, :user_id, :status
                    )
                """), {
                    'agent_id': config.agent_id,
                    'name': config.name,
                    'model_id': config.model_id,
                    'model_provider': config.model_provider,
                    'model_kwargs': self._json_dumps(config.model_kwargs),
                    'instructions': config.instructions,
                    'tools': self._json_dumps(config.tools),
                    'knowledge': self._json_dumps(config.knowledge),
                    'memory': self._json_dumps(config.memory),
                    'guardrails': self._json_dumps(config.guardrails),
                    'metadata': self._json_dumps(config.metadata),
                    'created_at': config.created_at,
                    'updated_at': config.updated_at,
                    'user_id': config.user_id,
                    'status': config.status
                })
                conn.commit()
                log_debug(f"Upserted agent config: {config.agent_id}")
                return config

        except Exception as e:
            log_error(f"Error upserting agent config: {e}")
            raise

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    text("SELECT * FROM agno_agent_config WHERE agent_id = ? AND status = 'active'"),
                    (agent_id,)
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                config_dict = dict(row._mapping)
                return AgentConfig.from_dict({
                    "agent_id": config_dict["agent_id"],
                    "name": config_dict["name"],
                    "model_id": config_dict["model_id"],
                    "model_provider": config_dict["model_provider"],
                    "model_kwargs": self._json_loads(config_dict["model_kwargs"]),
                    "instructions": config_dict["instructions"],
                    "tools": self._json_loads(config_dict["tools"]),
                    "knowledge": self._json_loads(config_dict["knowledge"]),
                    "memory": self._json_loads(config_dict["memory"]),
                    "guardrails": self._json_loads(config_dict["guardrails"]),
                    "metadata": self._json_loads(config_dict["metadata"]),
                    "created_at": config_dict["created_at"],
                    "updated_at": config_dict["updated_at"],
                    "user_id": config_dict["user_id"],
                    "status": config_dict["status"]
                })

        except Exception as e:
            log_error(f"Error getting agent config {agent_id}: {e}")
            raise

    def get_agent_configs(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AgentConfig]:
        """Get agent configurations with optional filters."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM agno_agent_config WHERE 1=1"
                params_dict = {}

                if user_id is not None:
                    query += " AND user_id = :user_id"
                    params_dict['user_id'] = user_id

                if status is not None:
                    query += " AND status = :status"
                    params_dict['status'] = status

                query += " ORDER BY updated_at DESC"

                if limit is not None:
                    query += " LIMIT :limit"
                    params_dict['limit'] = limit

                cursor = conn.execute(text(query), params_dict)
                rows = cursor.fetchall()

                configs = []
                for row in rows:
                    config_dict = dict(row._mapping)
                    configs.append(AgentConfig.from_dict({
                        "agent_id": config_dict["agent_id"],
                        "name": config_dict["name"],
                        "model_id": config_dict["model_id"],
                        "model_provider": config_dict["model_provider"],
                        "model_kwargs": self._json_loads(config_dict["model_kwargs"]),
                        "instructions": config_dict["instructions"],
                        "tools": self._json_loads(config_dict["tools"]),
                        "knowledge": self._json_loads(config_dict["knowledge"]),
                        "memory": self._json_loads(config_dict["memory"]),
                        "guardrails": self._json_loads(config_dict["guardrails"]),
                        "metadata": self._json_loads(config_dict["metadata"]),
                        "created_at": config_dict["created_at"],
                        "updated_at": config_dict["updated_at"],
                        "user_id": config_dict["user_id"],
                        "status": config_dict["status"]
                    }))

                return configs

        except Exception as e:
            log_error(f"Error getting agent configs: {e}")
            raise

    def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration by ID (soft delete)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    text("UPDATE agno_agent_config SET status = 'deleted', updated_at = ? WHERE agent_id = ?"),
                    (int(time.time()), agent_id)
                )
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    log_debug(f"Deleted agent config: {agent_id}")
                return success

        except Exception as e:
            log_error(f"Error deleting agent config {agent_id}: {e}")
            raise

    # --- Tool Configuration Methods ---

    def upsert_tool_config(self, config: ToolConfig) -> ToolConfig:
        """Insert or update tool configuration."""
        try:
            with self._get_connection() as conn:
                current_time = int(time.time())
                if config.created_at is None:
                    config.created_at = current_time
                config.updated_at = current_time

                conn.execute(text("""
                    INSERT OR REPLACE INTO agno_tools_config (
                        tool_id, name, function_definition, metadata, created_at, updated_at, agent_id, status
                    ) VALUES (
                        :tool_id, :name, :function_definition, :metadata, :created_at, :updated_at, :agent_id, :status
                    )
                """), {
                    'tool_id': config.tool_id,
                    'name': config.name,
                    'function_definition': self._json_dumps(config.function_definition),
                    'metadata': self._json_dumps(config.metadata),
                    'created_at': config.created_at,
                    'updated_at': config.updated_at,
                    'agent_id': config.agent_id,
                    'status': config.status
                })
                conn.commit()
                log_debug(f"Upserted tool config: {config.tool_id}")
                return config

        except Exception as e:
            log_error(f"Error upserting tool config: {e}")
            raise

    def get_tool_config(self, tool_id: str) -> Optional[ToolConfig]:
        """Get tool configuration by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    text("SELECT * FROM agno_tools_config WHERE tool_id = ? AND status = 'active'"),
                    (tool_id,)
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                config_dict = dict(row._mapping)
                return ToolConfig.from_dict({
                    "tool_id": config_dict["tool_id"],
                    "name": config_dict["name"],
                    "function_definition": self._json_loads(config_dict["function_definition"]),
                    "metadata": self._json_loads(config_dict["metadata"]),
                    "created_at": config_dict["created_at"],
                    "updated_at": config_dict["updated_at"],
                    "agent_id": config_dict["agent_id"],
                    "status": config_dict["status"]
                })

        except Exception as e:
            log_error(f"Error getting tool config {tool_id}: {e}")
            raise

    def get_tool_configs(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ToolConfig]:
        """Get tool configurations with optional filters."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM agno_tools_config WHERE 1=1"
                params_dict = {}

                if agent_id is not None:
                    query += " AND agent_id = :agent_id"
                    params_dict['agent_id'] = agent_id

                if status is not None:
                    query += " AND status = :status"
                    params_dict['status'] = status

                query += " ORDER BY updated_at DESC"

                if limit is not None:
                    query += " LIMIT :limit"
                    params_dict['limit'] = limit

                cursor = conn.execute(text(query), params_dict)
                rows = cursor.fetchall()

                configs = []
                for row in rows:
                    config_dict = dict(row._mapping)
                    configs.append(ToolConfig.from_dict({
                        "tool_id": config_dict["tool_id"],
                        "name": config_dict["name"],
                        "function_definition": self._json_loads(config_dict["function_definition"]),
                        "metadata": self._json_loads(config_dict["metadata"]),
                        "created_at": config_dict["created_at"],
                        "updated_at": config_dict["updated_at"],
                        "agent_id": config_dict["agent_id"],
                        "status": config_dict["status"]
                    }))

                return configs

        except Exception as e:
            log_error(f"Error getting tool configs: {e}")
            raise

    # --- Runtime Data Methods ---

    def upsert_runtime_data(self, data: RuntimeData) -> RuntimeData:
        """Insert or update runtime data."""
        try:
            with self._get_connection() as conn:
                current_time = int(time.time())
                if data.created_at is None:
                    data.created_at = current_time
                data.updated_at = current_time

                conn.execute(text("""
                    INSERT OR REPLACE INTO agno_runtime_data (
                        run_id, session_id, agent_id, user_id, input_data, output_data,
                        reasoning_steps, tool_calls, metrics, status, error_message,
                        execution_time, created_at, updated_at
                    ) VALUES (
                        :run_id, :session_id, :agent_id, :user_id, :input_data, :output_data,
                        :reasoning_steps, :tool_calls, :metrics, :status, :error_message,
                        :execution_time, :created_at, :updated_at
                    )
                """), {
                    'run_id': data.run_id,
                    'session_id': data.session_id,
                    'agent_id': data.agent_id,
                    'user_id': data.user_id,
                    'input_data': self._json_dumps(data.input_data),
                    'output_data': self._json_dumps(data.output_data),
                    'reasoning_steps': self._json_dumps(data.reasoning_steps),
                    'tool_calls': self._json_dumps(data.tool_calls),
                    'metrics': self._json_dumps(data.metrics),
                    'status': data.status,
                    'error_message': data.error_message,
                    'execution_time': data.execution_time,
                    'created_at': data.created_at,
                    'updated_at': data.updated_at
                })
                conn.commit()
                log_debug(f"Upserted runtime data: {data.run_id}")
                return data

        except Exception as e:
            log_error(f"Error upserting runtime data: {e}")
            raise

    def get_runtime_data(self, run_id: str) -> Optional[RuntimeData]:
        """Get runtime data by run ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    text("SELECT * FROM agno_runtime_data WHERE run_id = ?"),
                    (run_id,)
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                data_dict = dict(row._mapping)
                return RuntimeData.from_dict({
                    "run_id": data_dict["run_id"],
                    "session_id": data_dict["session_id"],
                    "agent_id": data_dict["agent_id"],
                    "user_id": data_dict["user_id"],
                    "input_data": self._json_loads(data_dict["input_data"]),
                    "output_data": self._json_loads(data_dict["output_data"]),
                    "reasoning_steps": self._json_loads(data_dict["reasoning_steps"]),
                    "tool_calls": self._json_loads(data_dict["tool_calls"]),
                    "metrics": self._json_loads(data_dict["metrics"]),
                    "status": data_dict["status"],
                    "error_message": data_dict["error_message"],
                    "execution_time": data_dict["execution_time"],
                    "created_at": data_dict["created_at"],
                    "updated_at": data_dict["updated_at"]
                })

        except Exception as e:
            log_error(f"Error getting runtime data {run_id}: {e}")
            raise

    def get_runtime_data_list(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[RuntimeData]:
        """Get runtime data list with optional filters."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM agno_runtime_data WHERE 1=1"
                params_dict = {}

                if session_id is not None:
                    query += " AND session_id = :session_id"
                    params_dict['session_id'] = session_id

                if agent_id is not None:
                    query += " AND agent_id = :agent_id"
                    params_dict['agent_id'] = agent_id

                if user_id is not None:
                    query += " AND user_id = :user_id"
                    params_dict['user_id'] = user_id

                if status is not None:
                    query += " AND status = :status"
                    params_dict['status'] = status

                query += " ORDER BY created_at DESC"

                if limit is not None:
                    query += " LIMIT :limit"
                    params_dict['limit'] = limit

                cursor = conn.execute(text(query), params_dict)
                rows = cursor.fetchall()

                data_list = []
                for row in rows:
                    data_dict = dict(row._mapping)
                    data_list.append(RuntimeData.from_dict({
                        "run_id": data_dict["run_id"],
                        "session_id": data_dict["session_id"],
                        "agent_id": data_dict["agent_id"],
                        "user_id": data_dict["user_id"],
                        "input_data": self._json_loads(data_dict["input_data"]),
                        "output_data": self._json_loads(data_dict["output_data"]),
                        "reasoning_steps": self._json_loads(data_dict["reasoning_steps"]),
                        "tool_calls": self._json_loads(data_dict["tool_calls"]),
                        "metrics": self._json_loads(data_dict["metrics"]),
                        "status": data_dict["status"],
                        "error_message": data_dict["error_message"],
                        "execution_time": data_dict["execution_time"],
                        "created_at": data_dict["created_at"],
                        "updated_at": data_dict["updated_at"]
                    }))

                return data_list

        except Exception as e:
            log_error(f"Error getting runtime data list: {e}")
            raise

    def update_runtime_data_status(self, run_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update runtime data status."""
        try:
            with self._get_connection() as conn:
                update_fields = ["status = ?", "updated_at = ?"]
                params = [status, int(time.time())]

                if error_message is not None:
                    update_fields.append("error_message = ?")
                    params.append(error_message)

                set_clauses = []
                update_dict = {}

                for field in update_fields:
                    if field == "status = ?":
                        set_clauses.append("status = :status")
                        update_dict['status'] = params[0]
                    elif field == "updated_at = ?":
                        set_clauses.append("updated_at = :updated_at")
                        update_dict['updated_at'] = params[1]
                    elif field == "error_message = ?":
                        set_clauses.append("error_message = :error_message")
                        update_dict['error_message'] = params[2]

                update_dict['run_id'] = run_id
                query = f"UPDATE agno_runtime_data SET {', '.join(set_clauses)} WHERE run_id = :run_id"

                cursor = conn.execute(text(query), update_dict)
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    log_debug(f"Updated runtime data status: {run_id} -> {status}")
                return success

        except Exception as e:
            log_error(f"Error updating runtime data status {run_id}: {e}")
            raise

    # --- Utility Methods ---

    def _json_dumps(self, data: Any) -> Optional[str]:
        """Convert data to JSON string."""
        if data is None:
            return None
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    def _json_loads(self, data: str) -> Any:
        """Parse JSON string."""
        if data is None or data == "":
            return None
        return json.loads(data)

    # --- Statistics Methods ---

    def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for a specific agent."""
        try:
            with self._get_connection() as conn:
                stats = {}

                # Get runtime data statistics
                cursor = conn.execute(
                    text("""
                    SELECT
                        COUNT(*) as total_runs,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_runs,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
                        AVG(execution_time) as avg_execution_time
                    FROM agno_runtime_data
                    WHERE agent_id = ?
                    """),
                    (agent_id,)
                )
                runtime_stats = cursor.fetchone()
                if runtime_stats:
                    stats.update({
                        "total_runs": runtime_stats[0],
                        "completed_runs": runtime_stats[1],
                        "failed_runs": runtime_stats[2],
                        "success_rate": runtime_stats[1] / runtime_stats[0] if runtime_stats[0] > 0 else 0,
                        "avg_execution_time": runtime_stats[3] or 0
                    })

                # Get session statistics
                cursor = conn.execute(
                    text("""
                    SELECT COUNT(*) as total_sessions
                    FROM agno_sessions
                    WHERE agent_id = ?
                    """),
                    (agent_id,)
                )
                session_stats = cursor.fetchone()
                if session_stats:
                    stats["total_sessions"] = session_stats[0]

                return stats

        except Exception as e:
            log_error(f"Error getting agent statistics for {agent_id}: {e}")
            return {}

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}

                # Count records in each table
                tables = [
                    ("agno_agent_config", "agent_configs"),
                    ("agno_tools_config", "tool_configs"),
                    ("agno_runtime_data", "runtime_data"),
                    (self.session_table_name, "sessions"),
                    (self.memory_table_name, "memories"),
                    (self.knowledge_table_name, "knowledge"),
                    (self.eval_table_name, "evaluations"),
                    (self.culture_table_name, "cultural_knowledge")
                ]

                for table_name, stats_key in tables:
                    try:
                        cursor = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = cursor.fetchone()[0]
                        stats[stats_key] = count
                    except Exception:
                        stats[stats_key] = 0

                return stats

        except Exception as e:
            log_error(f"Error getting database statistics: {e}")
            return {}