"""
简化的 ChatEngine 配置功能测试

专门测试 ChatEngine 的 save_config 和 load_config 方法
避免复杂的依赖，专注核心功能验证
"""

import sys
import tempfile
import os
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def simple_config_test():
    """简单的配置功能测试"""
    print("🚀 开始 ChatEngine 配置功能测试...")

    temp_db = None
    chat_engine = None

    try:
        # 1. 创建临时数据库
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        db_path = temp_db.name
        print(f"✓ 创建临时数据库: {db_path}")

        # 2. 初始化 ChatEngine
        from chat_engine import ChatEngine
        chat_engine = ChatEngine(
            config_path=db_path,
            user_token="test_user_simple"
        )
        print("✓ ChatEngine 初始化成功")

        # 3. 测试保存配置
        print("\n--- 测试配置保存 ---")
        test_agent_name = "简单测试智能体"
        test_config = {
            'agent_id': 'simple_test_agent',
            'name': test_agent_name,
            'type': 'text',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai'
            },
            'instructions': '这是一个简单的测试智能体',
            'tools': [],
            'guardrails': []
        }

        # 添加配置并保存
        chat_engine.agent_configs[test_agent_name] = test_config
        chat_engine.save_config()
        print("✓ 配置保存成功")

        # 验证配置是否保存到数据库
        agent_configs_db = chat_engine.db.get_agent_configs(user_id="test_user_simple")
        saved_config = None
        for config in agent_configs_db:
            if config.name == test_agent_name:
                saved_config = config
                break

        assert saved_config is not None, "配置应该已保存到数据库"
        assert saved_config.name == test_agent_name
        print("✓ 数据库保存验证通过")

        # 4. 测试加载配置
        print("\n--- 测试配置加载 ---")
        # 清空内存中的配置
        chat_engine.agent_configs.clear()

        # 重新加载配置
        loaded_configs = chat_engine.load_config()
        print("✓ 配置加载成功")

        # 验证加载的配置
        assert test_agent_name in loaded_configs, "应该加载保存的配置"
        loaded_config = loaded_configs[test_agent_name]
        assert loaded_config['name'] == test_agent_name
        assert loaded_config['instructions'] == '这是一个简单的测试智能体'
        print("✓ 加载配置验证通过")

        # 5. 测试配置持久性
        print("\n--- 测试配置持久性 ---")
        # 关闭当前 ChatEngine
        if hasattr(chat_engine, 'db'):
            if hasattr(chat_engine.db, 'Session'):
                chat_engine.db.Session.remove()
            if hasattr(chat_engine.db, 'db_engine'):
                chat_engine.db.db_engine.dispose()

        # 创建新的 ChatEngine 实例
        new_chat_engine = ChatEngine(
            config_path=db_path,
            user_token="test_user_simple"
        )

        # 验证新实例是否自动加载了配置
        # ChatEngine 在初始化时会自动调用 load_config
        assert test_agent_name in new_chat_engine.agent_configs, "新实例应该自动加载保存的配置"
        auto_loaded_config = new_chat_engine.agent_configs[test_agent_name]
        assert auto_loaded_config['name'] == test_agent_name
        print("✓ 配置持久性验证通过")

        # 清理第二个实例
        if hasattr(new_chat_engine, 'db'):
            if hasattr(new_chat_engine.db, 'Session'):
                new_chat_engine.db.Session.remove()
            if hasattr(new_chat_engine.db, 'db_engine'):
                new_chat_engine.db.db_engine.dispose()

        print("\n🎉 简单配置功能测试全部通过！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        try:
            if chat_engine:
                if hasattr(chat_engine, 'executor'):
                    chat_engine.executor.shutdown(wait=True)
                if hasattr(chat_engine, 'db'):
                    if hasattr(chat_engine.db, 'Session'):
                        chat_engine.db.Session.remove()
                    if hasattr(chat_engine.db, 'db_engine'):
                        chat_engine.db.db_engine.dispose()

            if temp_db and os.path.exists(temp_db.name):
                time.sleep(0.1)
                os.unlink(temp_db.name)
                print("✓ 资源清理完成")
        except Exception as cleanup_error:
            print(f"⚠️  清理警告: {cleanup_error}")


def test_multi_agent_config():
    """测试多智能体配置管理"""
    print("\n🔄 开始多智能体配置测试...")

    temp_db = None
    chat_engine = None

    try:
        # 创建临时数据库和 ChatEngine
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        db_path = temp_db.name

        from chat_engine import ChatEngine
        chat_engine = ChatEngine(
            config_path=db_path,
            user_token="test_user_multi"
        )

        # 创建多个智能体配置
        agents = {
            "助手智能体": {
                'agent_id': 'assistant_agent',
                'name': "助手智能体",
                'type': 'text',
                'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                'instructions': '你是一个有用的助手',
                'tools': [],
                'guardrails': []
            },
            "分析智能体": {
                'agent_id': 'analyst_agent',
                'name': "分析智能体",
                'type': 'text',
                'model': {'name': 'gpt-4', 'provider': 'openai'},
                'instructions': '你是一个数据分析师',
                'tools': [{'name': 'data_analyzer'}],
                'guardrails': []
            },
            "创意智能体": {
                'agent_id': 'creative_agent',
                'name': "创意智能体",
                'type': 'text',
                'model': {'name': 'gpt-4', 'provider': 'openai'},
                'instructions': '你是一个创意专家',
                'tools': [],
                'guardrails': [{'type': 'content_filter'}]
            }
        }

        # 添加所有配置
        for name, config in agents.items():
            chat_engine.agent_configs[name] = config

        # 保存配置
        chat_engine.save_config()
        print("✓ 多智能体配置保存成功")

        # 清空并重新加载
        chat_engine.agent_configs.clear()
        loaded_configs = chat_engine.load_config()

        # 验证所有配置都被加载
        assert len(loaded_configs) == 3, f"应该加载3个配置，实际加载了{len(loaded_configs)}个"
        for name in agents.keys():
            assert name in loaded_configs, f"应该加载配置: {name}"

        print("✓ 多智能体配置验证通过")

        # 清理
        if hasattr(chat_engine, 'db'):
            if hasattr(chat_engine.db, 'Session'):
                chat_engine.db.Session.remove()
            if hasattr(chat_engine.db, 'db_engine'):
                chat_engine.db.db_engine.dispose()

        return True

    except Exception as e:
        print(f"❌ 多智能体配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            if chat_engine and hasattr(chat_engine, 'executor'):
                chat_engine.executor.shutdown(wait=True)
            if temp_db and os.path.exists(temp_db.name):
                time.sleep(0.1)
                os.unlink(temp_db.name)
        except:
            pass


def main():
    """主测试函数"""
    print("=" * 60)
    print("ChatEngine 配置功能测试")
    print("=" * 60)

    # 运行测试
    test1_result = simple_config_test()
    test2_result = test_multi_agent_config()

    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"  基本配置功能: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  多智能体配置: {'✅ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print("\n🎉 所有测试通过！")
        print("ChatEngine 的配置保存和加载功能正常工作。")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)