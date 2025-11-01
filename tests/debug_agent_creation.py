#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug ChatEngine Agent Creation

调试ChatEngine的create_new_agent功能
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def debug_agent_creation():
    """调试Agent创建过程"""
    print("=" * 60)
    print("Debug ChatEngine Agent Creation")
    print("=" * 60)

    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name

    try:
        # 导入ChatEngine
        from chat_engine import ChatEngine
        print("[SUCCESS] ChatEngine导入成功")

        # 创建ChatEngine实例
        engine = ChatEngine(config_path=db_path, user_id="debug_user")
        print("[SUCCESS] ChatEngine实例创建成功")

        # 测试最小配置
        print("\n--- 测试最小配置 ---")
        agent_config = {
            'agent_id': 'debug_agent_001',
            'name': 'Debug Agent',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai',
                'kwargs': {}
            }
        }

        print(f"配置: {agent_config}")

        # 调用create_new_agent
        agent = engine.create_new_agent('Debug Agent', agent_config)

        if agent:
            print(f"[SUCCESS] Agent创建成功: {agent}")
            print(f"  - agent_id: {agent.agent_id}")
            print(f"  - name: {agent.name}")
            print(f"  - type: {type(agent)}")

            # 测试属性
            if hasattr(agent, 'instructions'):
                print(f"  - instructions: {agent.instructions}")
            if hasattr(agent, 'user_id'):
                print(f"  - user_id: {agent.user_id}")
            if hasattr(agent, 'model'):
                print(f"  - model: {agent.model}")
        else:
            print("[ERROR] Agent创建失败，返回None")

        # 测试Mock Agent
        print("\n--- 测试Mock Agent ---")
        mock_config = {
            'agent_id': 'mock_debug_001',
            'name': 'Mock Debug Agent',
            'model': 'nonexistent-model',  # 这应该触发Mock Agent
            'instructions': '这是一个调试用的Mock Agent'
        }

        print(f"Mock配置: {mock_config}")

        mock_agent = engine.create_new_agent('Mock Debug Agent', mock_config)

        if mock_agent:
            print(f"[SUCCESS] Mock Agent创建成功: {mock_agent}")
            print(f"  - agent_id: {mock_agent.agent_id}")
            print(f"  - name: {mock_agent.name}")
            print(f"  - type: {type(mock_agent)}")

            # 测试run方法
            if hasattr(mock_agent, 'run'):
                response = mock_agent.run("Hello, test!")
                print(f"  - run() response: {response}")
        else:
            print("[ERROR] Mock Agent创建失败，返回None")

        # 测试错误处理
        print("\n--- 测试错误处理 ---")
        try:
            # 测试空的agent_name
            invalid_agent = engine.create_new_agent('', {'agent_id': 'test'})
            print("[ERROR] 应该抛出ValueError (agent_name)")
        except ValueError as e:
            print(f"[SUCCESS] 正确捕获ValueError (agent_name): {e}")
        except Exception as e:
            print(f"[ERROR] 捕获了意外的异常 (agent_name): {e}")

        try:
            # 测试空的agent_dict
            invalid_agent = engine.create_new_agent('Test Agent', None)
            print("[ERROR] 应该抛出ValueError (agent_dict)")
        except ValueError as e:
            print(f"[SUCCESS] 正确捕获ValueError (agent_dict): {e}")
        except Exception as e:
            print(f"[ERROR] 捕获了意外的异常 (agent_dict): {e}")

    except Exception as e:
        print(f"[ERROR] 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理临时文件
        try:
            os.unlink(db_path)
        except:
            pass

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == '__main__':
    debug_agent_creation()