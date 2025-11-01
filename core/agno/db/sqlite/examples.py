"""SQLite integration examples for agno."""

from pathlib import Path
from typing import List, Optional

from core.agno.db.sqlite.extended_sqlite import ExtendedSqliteDb
from core.agno.db.sqlite.config_data import AgentConfig, ToolConfig
from core.agno.db.sqlite.runtime_data import RuntimeData
from core.agno.session import AgentSession
from core.agno.db.schemas.memory import UserMemory


def create_sqlite_database(db_path: str = "agno.db") -> ExtendedSqliteDb:
    """Create and initialize SQLite database."""
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create database instance
    db = ExtendedSqliteDb(db_file=db_path)

    print(f"✅ SQLite database created: {db_path}")
    return db


def example_agent_config_usage(db: ExtendedSqliteDb):
    """Example: Agent configuration management."""
    print("\n=== Agent Configuration Example ===")

    # Create agent configuration
    agent_config = AgentConfig(
        agent_id="agent-001",
        name="Customer Service Agent",
        model_id="gpt-4",
        model_provider="openai",
        model_kwargs={"temperature": 0.7, "max_tokens": 2000},
        instructions="You are a helpful customer service agent. Be polite and efficient.",
        tools=[
            {"name": "search_knowledge", "description": "Search knowledge base"},
            {"name": "create_ticket", "description": "Create support ticket"}
        ],
        knowledge={"sources": ["faq", "product_docs"]},
        memory={"type": "summary", "window": 10},
        user_id="user-123"
    )

    # Save configuration
    saved_config = db.upsert_agent_config(agent_config)
    print(f"✅ Saved agent config: {saved_config.agent_id}")

    # Retrieve configuration
    retrieved_config = db.get_agent_config("agent-001")
    if retrieved_config:
        print(f"✅ Retrieved agent: {retrieved_config.name}")
        print(f"   Model: {retrieved_config.model_provider}:{retrieved_config.model_id}")
        print(f"   Tools: {len(retrieved_config.tools or [])}")

    # List all agent configs
    configs = db.get_agent_configs(user_id="user-123")
    print(f"✅ Found {len(configs)} agent configurations")

    return saved_config


def example_runtime_data_usage(db: ExtendedSqliteDb):
    """Example: Runtime data tracking."""
    print("\n=== Runtime Data Example ===")

    # Create runtime data
    runtime_data = RuntimeData(
        run_id="run-001",
        session_id="session-001",
        agent_id="agent-001",
        user_id="user-123",
        input_data={"query": "How do I reset my password?", "language": "en"},
        reasoning_steps=[
            {"step": 1, "type": "understand", "content": "User wants to reset password"},
            {"step": 2, "type": "search", "content": "Search for password reset instructions"},
            {"step": 3, "type": "respond", "content": "Provide reset instructions"}
        ],
        tool_calls=[
            {"tool": "search_knowledge", "args": {"query": "password reset"}, "result": "Found instructions"},
            {"tool": "create_ticket", "args": {"topic": "password reset"}, "result": "Ticket created"}
        ],
        metrics={
            "input_tokens": 45,
            "output_tokens": 120,
            "total_tokens": 165,
            "response_time": 2.3
        },
        status="completed",
        execution_time=2.5
    )

    # Save runtime data
    saved_data = db.upsert_runtime_data(runtime_data)
    print(f"✅ Saved runtime data: {saved_data.run_id}")

    # Retrieve runtime data
    retrieved_data = db.get_runtime_data("run-001")
    if retrieved_data:
        print(f"✅ Retrieved runtime data: {retrieved_data.status}")
        print(f"   Execution time: {retrieved_data.execution_time}s")
        print(f"   Reasoning steps: {len(retrieved_data.reasoning_steps or [])}")
        print(f"   Tool calls: {len(retrieved_data.tool_calls or [])}")

    # List runtime data for agent
    runtime_list = db.get_runtime_data_list(agent_id="agent-001", limit=10)
    print(f"✅ Found {len(runtime_list)} runtime records")

    return saved_data


def example_session_usage(db: ExtendedSqliteDb):
    """Example: Session management."""
    print("\n=== Session Management Example ===")

    # Create agent session
    session = AgentSession(
        session_id="session-001",
        agent_id="agent-001",
        user_id="user-123",
        session_data={"session_name": "Password Reset Help", "language": "en"},
        runs=[
            {
                "run_id": "run-001",
                "input": "How do I reset my password?",
                "output": "I can help you reset your password...",
                "timestamp": 1700000000
            }
        ],
        created_at=1700000000,
        updated_at=1700000005
    )

    # Save session
    saved_session = db.upsert_session(session)
    print(f"✅ Saved session: {saved_session.session_id}")

    # Retrieve session
    retrieved_session = db.get_session(
        session_id="session-001",
        session_type="agent",
        user_id="user-123"
    )
    if retrieved_session:
        print(f"✅ Retrieved session: {retrieved_session.session_id}")
        print(f"   Runs: {len(retrieved_session.runs or [])}")

    return saved_session


def example_memory_usage(db: ExtendedSqliteDb):
    """Example: Memory management."""
    print("\n=== Memory Management Example ===")

    # Create user memory
    memory = UserMemory(
        memory_id="memory-001",
        agent_id="agent-001",
        user_id="user-123",
        memory={
            "type": "preference",
            "content": "User prefers detailed explanations with examples",
            "category": "communication_style"
        },
        input="User asked for detailed explanation with examples",
        topics=["preferences", "communication", "style"],
        updated_at=1700000010
    )

    # Save memory
    saved_memory = db.upsert_user_memory(memory)
    print(f"✅ Saved memory: {saved_memory.memory_id}")

    # Retrieve memory
    retrieved_memory = db.get_user_memory("memory-001", user_id="user-123")
    if retrieved_memory:
        print(f"✅ Retrieved memory: {retrieved_memory.memory_id}")
        print(f"   Topics: {retrieved_memory.topics}")

    # List memories for user
    memories = db.get_user_memories(user_id="user-123", limit=10)
    print(f"✅ Found {len(memories)} memories")

    return saved_memory


def example_statistics_usage(db: ExtendedSqliteDb):
    """Example: Statistics and analytics."""
    print("\n=== Statistics Example ===")

    # Get agent statistics
    agent_stats = db.get_agent_statistics("agent-001")
    print(f"✅ Agent statistics for agent-001:")
    print(f"   Total runs: {agent_stats.get('total_runs', 0)}")
    print(f"   Success rate: {agent_stats.get('success_rate', 0):.2%}")
    print(f"   Avg execution time: {agent_stats.get('avg_execution_time', 0):.2f}s")

    # Get database statistics
    db_stats = db.get_database_statistics()
    print(f"✅ Database statistics:")
    print(f"   Agent configs: {db_stats.get('agent_configs', 0)}")
    print(f"   Runtime data: {db_stats.get('runtime_data', 0)}")
    print(f"   Sessions: {db_stats.get('sessions', 0)}")
    print(f"   Memories: {db_stats.get('memories', 0)}")
    print(f"   Knowledge items: {db_stats.get('knowledge', 0)}")


def complete_example():
    """Complete example of SQLite integration with agno."""
    print("🚀 Starting agno SQLite integration example...")

    # Create database
    db = create_sqlite_database("./examples/agno_example.db")

    try:
        # Run examples
        agent_config = example_agent_config_usage(db)
        runtime_data = example_runtime_data_usage(db)
        session = example_session_usage(db)
        memory = example_memory_usage(db)
        example_statistics_usage(db)

        print("\n✅ All examples completed successfully!")
        print(f"📁 Database file: {db.db_path}")

        return {
            "database": db,
            "agent_config": agent_config,
            "runtime_data": runtime_data,
            "session": session,
            "memory": memory
        }

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        raise


def backup_database(db: ExtendedSqliteDb, backup_path: str):
    """Create a backup of the SQLite database."""
    import shutil

    try:
        shutil.copy2(db.db_file, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
    except Exception as e:
        print(f"❌ Error backing up database: {e}")
        raise


def cleanup_database(db: ExtendedSqliteDb):
    """Clean up database resources."""
    try:
        # Close any open connections
        if hasattr(db, 'Session'):
            db.Session.remove()
        print("✅ Database cleanup completed")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


if __name__ == "__main__":
    # Run the complete example
    result = complete_example()

    # Cleanup
    cleanup_database(result["database"])

    print("\n🎉 agno SQLite integration example completed!")