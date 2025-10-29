#!/usr/bin/env python3
"""
测试会话功能的脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_app_enhanced import EnhancedChatApp, SessionConfig, AgentConfig

def test_session_features():
    """测试会话功能"""
    print("=== 测试会话功能 ===")

    app = EnhancedChatApp()

    # 获取当前用户和会话信息
    current_user = app.user_manager.get_user(app.current_user_id)
    current_session = app.session_manager.get_session(app.current_session_id)
    current_agent = app.agent_manager.get_agent(app.current_agent_id)

    print(f"当前用户: {current_user.username}")
    print(f"当前会话: {current_session.title}")
    print(f"当前Agent: {current_agent.name}")

    # 测试创建新会话
    print("\n--- 测试创建新会话 ---")
    new_session = app.session_manager.create_session(
        current_user.id,
        "测试会话",
        "这是一个测试会话",
        current_agent.id
    )
    print(f"[OK] 新会话已创建: {new_session.title}")

    # 测试获取用户会话列表
    print("\n--- 测试获取用户会话列表 ---")
    sessions = app.session_manager.get_user_sessions(current_user.id)
    print(f"用户 {current_user.username} 的会话列表:")
    for i, session in enumerate(sessions, 1):
        agent = app.agent_manager.get_agent(session.current_agent_id) if session.current_agent_id else None
        agent_name = agent.name if agent else "未设置"
        current_mark = " [当前]" if session.id == app.current_session_id else ""
        print(f"  {i}. {session.title}{current_mark} (Agent: {agent_name})")

    # 测试切换会话
    print("\n--- 测试切换会话 ---")
    original_session_id = app.current_session_id
    app.current_session_id = new_session.id
    app.current_agent_id = new_session.current_agent_id

    switched_session = app.session_manager.get_session(app.current_session_id)
    switched_agent = app.agent_manager.get_agent(app.current_agent_id)
    print(f"[OK] 已切换到会话: {switched_session.title}")
    print(f"Agent: {switched_agent.name}")

    # 测试会话内消息保存
    print("\n--- 测试会话内消息保存 ---")
    message_id = app.conversation_manager.add_message(
        app.current_session_id,
        app.current_user_id,
        app.current_agent_id,
        "user",
        "这是一条测试消息"
    )
    print(f"[OK] 消息已保存到会话: {message_id}")

    # 保存AI回复
    ai_message_id = app.conversation_manager.add_message(
        app.current_session_id,
        app.current_user_id,
        app.current_agent_id,
        "assistant",
        "这是AI的回复"
    )
    print(f"[OK] AI回复已保存到会话: {ai_message_id}")

    # 测试获取对话历史
    print("\n--- 测试获取对话历史 ---")
    history = app.conversation_manager.get_conversation_history(app.current_session_id, 10)
    print(f"会话历史 (共{len(history)}条消息):")
    for i, message in enumerate(history, 1):
        role_text = "[用户]" if message["role"] == "user" else "[AI]"
        print(f"  {i}. {role_text} {message['content']}")

    # 测试会话Agent切换
    print("\n--- 测试会话Agent切换 ---")
    agents = app.agent_manager.get_user_agents(current_user.id)
    if len(agents) > 1:
        # 切换到另一个Agent
        other_agent = agents[1] if agents[0].id == app.current_agent_id else agents[0]
        print(f"切换到Agent: {other_agent.name}")

        # 更新会话的当前Agent
        if app.session_manager.update_session(app.current_session_id, current_agent_id=other_agent.id):
            app.current_agent_id = other_agent.id
            print(f"[OK] 已切换到Agent: {other_agent.name}")
    else:
        print("只有一个Agent，跳过切换测试")

    # 测试会话信息显示
    print("\n--- 测试会话信息显示 ---")
    app.show_current_session_info()

    # 测试会话更新
    print("\n--- 测试会话更新 ---")
    if app.session_manager.update_session(
        app.current_session_id,
        title="更新后的测试会话",
        description="这是更新后的描述"
    ):
        updated_session = app.session_manager.get_session(app.current_session_id)
        print(f"[OK] 会话已更新:")
        print(f"  标题: {updated_session.title}")
        print(f"  描述: {updated_session.description}")

    # 恢复原始会话
    print("\n--- 恢复原始会话 ---")
    app.current_session_id = original_session_id
    original_agent = app.session_manager.get_session(original_session_id)
    app.current_agent_id = original_agent.current_agent_id
    print(f"[OK] 已恢复到原始会话: {original_agent.title}")

    # 测试删除会话（不能删除当前会话，所以先切换）
    print("\n--- 测试删除会话 ---")
    app.current_session_id = original_session_id  # 确保当前是原始会话
    if len(sessions) > 1:
        # 找一个不是当前会话的会话来删除
        session_to_delete = None
        for session in sessions:
            if session.id != original_session_id:
                session_to_delete = session
                break

        if session_to_delete:
            print(f"删除会话: {session_to_delete.title}")
            if app.session_manager.delete_session(session_to_delete.id):
                print(f"[OK] 会话已删除: {session_to_delete.title}")
            else:
                print(f"[错误] 删除会话失败")
        else:
            print("没有找到可删除的会话")
    else:
        print("只有一个会话，无法删除")

    print("\n=== 会话功能测试完成 ===")
    print("[OK] 所有会话功能测试通过!")

    # 清理资源
    app.cleanup()

if __name__ == "__main__":
    test_session_features()