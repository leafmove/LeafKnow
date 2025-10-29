#!/usr/bin/env python3
"""
增强版 Chat App 演示脚本
演示多用户、Agent管理、对话历史等功能
"""

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from chat_app_enhanced import (
    DatabaseManager, UserManager, AgentManager,
    ConversationManager, EnhancedChatApp, AgentConfig
)


def demo_multi_user_system():
    """演示多用户系统"""
    print("=" * 60)
    print("多用户系统演示")
    print("=" * 60)

    # 初始化数据库
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    agent_manager = AgentManager(db_manager)
    conversation_manager = ConversationManager(db_manager)

    try:
        # 1. 创建多个用户
        print("\n1. 创建用户...")
        users_data = [
            ("alice", "alice@example.com"),
            ("bob", "bob@example.com"),
            ("charlie", "charlie@example.com")
        ]

        created_users = []
        for username, email in users_data:
            user = user_manager.get_user_by_username(username)
            if not user:
                user = user_manager.create_user(username, email)
                print(f"   [OK] 创建用户: {user.username} ({user.email})")
            else:
                print(f"   [OK] 用户已存在: {user.username}")
            created_users.append(user)

        # 2. 为每个用户创建不同的 Agent
        print("\n2. 为用户创建 Agent...")

        # Alice 的 Agent（OpenAI GPT-4o-mini）
        alice_config = AgentConfig(
            user_id=created_users[0].id,
            name="Alice's GPT-4o Assistant",
            model_id="gpt-4o-mini",
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key=os.getenv("OPENAI_API_KEY") or "demo_key",
            system_prompt="你是一个专业的AI助手，专门帮助Alice处理各种任务。",
            description="Alice的个人AI助手",
            is_default=True
        )

        alice_user_id = created_users[0].id
        print(f"   Alice用户ID: {alice_user_id} (类型: {type(alice_user_id)})")
        alice_agent = agent_manager.get_user_agents(alice_user_id)
        if not alice_agent:
            alice_agent = [agent_manager.create_agent(created_users[0].id, alice_config)]
            print(f"   [OK] 为Alice创建Agent: {alice_agent[0].name}")
        else:
            print(f"   [OK] Alice已有Agent: {len(alice_agent)}个")

        # Bob 的 Agent（Ollama）
        bob_config = AgentConfig(
            user_id=created_users[1].id,
            name="Bob's Local Assistant",
            model_id="llama3.2:latest",
            provider="ollama",
            base_url="http://localhost:11434",
            system_prompt="你是一个本地AI助手，专门帮助Bob进行技术学习和研究。",
            description="Bob的本地技术助手",
            is_local=True,
            is_default=True
        )

        bob_agent = agent_manager.get_user_agents(created_users[1].id)
        if not bob_agent:
            bob_agent = [agent_manager.create_agent(created_users[1].id, bob_config)]
            print(f"   [OK] 为Bob创建Agent: {bob_agent[0].name}")
        else:
            print(f"   [OK] Bob已有Agent: {len(bob_agent)}个")

        # Charlie 的 Agent（OpenRouter）
        charlie_config = AgentConfig(
            user_id=created_users[2].id,
            name="Charlie's Research Assistant",
            model_id="anthropic/claude-3.5-sonnet",
            provider="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY") or "demo_key",
            temperature=0.3,
            system_prompt="你是一个研究助手，专门帮助Charlie进行学术研究和写作。",
            description="Charlie的学术研究助手",
            is_default=True
        )

        charlie_agent = agent_manager.get_user_agents(created_users[2].id)
        if not charlie_agent:
            charlie_agent = [agent_manager.create_agent(created_users[2].id, charlie_config)]
            print(f"   [OK] 为Charlie创建Agent: {charlie_agent[0].name}")
        else:
            print(f"   [OK] Charlie已有Agent: {len(charlie_agent)}个")

        # 3. 演示用户切换
        print("\n3. 用户切换演示...")
        current_user = created_users[0]
        print(f"   当前用户: {current_user.username}")

        # 模拟切换到其他用户
        for user in created_users[1:]:
            print(f"   切换到用户: {user.username}")
            current_user = user

            # 获取用户的Agent
            user_agents = agent_manager.get_user_agents(user.id)
            if user_agents:
                default_agent = agent_manager.get_user_default_agent(user.id) or user_agents[0]
                print(f"   默认Agent: {default_agent.name} ({default_agent.provider})")

        # 4. 演示Agent配置管理
        print("\n4. Agent配置管理演示...")
        for user in created_users:
            user_agents = agent_manager.get_user_agents(user.id)
            print(f"\n   用户 {user.username} 的Agent:")
            for i, agent in enumerate(user_agents, 1):
                default_mark = " [默认]" if agent.is_default else ""
                print(f"   {i}. {agent.name}{default_mark}")
                print(f"      模型: {agent.model_id}")
                print(f"      提供商: {agent.provider}")
                print(f"      系统提示: {agent.system_prompt[:50]}...")

        # 5. 演示对话历史
        print("\n5. 对话历史演示...")
        alice = created_users[0]
        alice_agents = agent_manager.get_user_agents(alice.id)
        if alice_agents:
            # 添加一些示例对话
            conversation_manager.add_message(
                alice.id, alice_agents[0].id, "user",
                "你好，我需要帮助处理一个Python项目"
            )
            conversation_manager.add_message(
                alice.id, alice_agents[0].id, "assistant",
                "你好！我很乐意帮助你处理Python项目。请告诉我你遇到了什么问题？"
            )
            conversation_manager.add_message(
                alice.id, alice_agents[0].id, "user",
                "我想优化我的代码性能"
            )
            conversation_manager.add_message(
                alice.id, alice_agents[0].id, "assistant",
                "代码性能优化有很多方面，让我们逐一分析..."
            )

            history = conversation_manager.get_conversation_history(alice.id, alice_agents[0].id, 10)
            print(f"   {alice.username} 的对话历史:")
            for i, msg in enumerate(history[:4], 1):
                role = "用户" if msg["role"] == "user" else "助手"
                content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                print(f"   {i}. {role}: {content}")

        print("\n[OK] 多用户系统演示完成！")

    except Exception as e:
        print(f"[ERROR] 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db_manager.close()


def demo_database_operations():
    """演示数据库操作"""
    print("\n" + "=" * 60)
    print("数据库操作演示")
    print("=" * 60)

    try:
        # 演示不同数据库类型
        print("\n1. 支持的数据库类型:")
        print("   [OK] SQLite - 默认本地数据库")
        print("   [OK] MySQL - 企业级关系数据库")
        print("   [OK] PostgreSQL - 高级开源数据库")

        # 显示数据库文件信息
        db_path = Path("autobox_id.db")
        if db_path.exists():
            file_size = db_path.stat().st_size
            print(f"\n2. 当前数据库信息:")
            print(f"   文件路径: {db_path.absolute()}")
            print(f"   文件大小: {file_size:,} 字节")
        else:
            print("\n2. 数据库文件将在首次运行时创建")

        print("\n3. 数据库连接示例:")
        print("   SQLite:   DatabaseManager(DatabaseType.SQLITE)")
        print("   MySQL:    DatabaseManager(DatabaseType.MYSQL, host='localhost', user='root', password='pass')")
        print("   PostgreSQL: DatabaseManager(DatabaseType.POSTGRESQL, host='localhost', user='postgres')")

    except Exception as e:
        print(f"[ERROR] 数据库演示错误: {str(e)}")


def main():
    """主演示函数"""
    print("增强版 Chat App 功能演示")
    print("本演示将展示多用户系统、Agent管理和数据库功能")

    try:
        # 检查依赖
        print("\n检查依赖...")
        from chat_app_enhanced import OPENAI_AVAILABLE, OLLAMA_AVAILABLE, OPENROUTER_AVAILABLE, LLAMACPP_AVAILABLE

        print(f"OpenAI 支持: {'可用' if OPENAI_AVAILABLE else '不可用'}")
        print(f"Ollama 支持: {'可用' if OLLAMA_AVAILABLE else '不可用'}")
        print(f"OpenRouter 支持: {'可用' if OPENROUTER_AVAILABLE else '不可用'}")
        print(f"Llama.cpp 支持: {'可用' if LLAMACPP_AVAILABLE else '不可用'}")

        # 运行演示
        demo_database_operations()
        demo_multi_user_system()

        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n下一步操作:")
        print("1. 运行完整应用: python chat_app_enhanced.py")
        print("2. 使用命令行参数指定数据库类型")
        print("3. 查看 README_CHAT_APP.md 了解详细使用方法")
        print("\n提示:")
        print("- 首次运行会自动创建默认用户和Agent")
        print("- 使用 'users' 命令管理用户")
        print("- 使用 'agents' 命令管理Agent")
        print("- 使用 'history' 命令查看对话历史")

    except ImportError as e:
        print(f"[ERROR] 导入错误: {str(e)}")
        print("请确保所有依赖已正确安装")
    except Exception as e:
        print(f"[ERROR] 演示错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()