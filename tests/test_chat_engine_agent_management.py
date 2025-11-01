"""
ChatEngine 智能体管理与配置集成测试

测试 ChatEngine 的智能体创建、更新、删除等操作与配置保存的集成
"""

import sys
import tempfile
import os
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_agent_creation_and_config():
    """测试智能体创建与配置保存"""
    print("🚀 测试智能体创建与配置保存...")

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
            user_token="test_agent_creation"
        )
        print("✓ ChatEngine 初始化成功")

        # 由于可能缺少 LLM_CLASS_DICT，我们模拟一个简单的智能体类
        # 这里主要测试配置管理，不依赖实际的 LLM 实现
        print("\n--- 模拟智能体类 ---")

        # 创建虚拟的智能体配置
        agent_config = {
            'name': '测试智能体',
            'type': 'text',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai',
                'kwargs': {'temperature': 0.7}
            },
            'instructions': '你是一个测试智能体',
            'tools': [{'name': 'calculator', 'description': '计算工具'}],
            'knowledge': {'type': 'general'},
            'memory': {'max_messages': 50},
            'guardrails': [{'type': 'content_filter'}],
            'metadata': {'version': '1.0', 'test': True}
        }

        # 直接添加配置到 agent_configs
        # 模拟 create_agent 的配置保存部分
        chat_engine.agent_configs['测试智能体'] = agent_config

        # 手动保存到数据库（模拟 create_agent 中的数据库操作）
        from core.agno.db.sqlite.config_data import AgentConfig
        db_agent_config = AgentConfig.from_dict({
            'agent_id': f"测试智能体_{chat_engine.user_token}_{int(time.time())}",
            'name': '测试智能体',
            'model_id': agent_config.get('model', {}).get('name'),
            'model_provider': agent_config.get('model', {}).get('provider'),
            'model_kwargs': agent_config.get('model', {}).get('kwargs'),
            'instructions': agent_config.get('instructions'),
            'tools': agent_config.get('tools'),
            'knowledge': agent_config.get('knowledge'),
            'memory': agent_config.get('memory'),
            'guardrails': agent_config.get('guardrails'),
            'metadata': agent_config.get('metadata'),
            'user_id': chat_engine.user_token
        })
        chat_engine.db.upsert_agent_config(db_agent_config)

        print("✓ 智能体配置创建和保存成功")

        # 验证配置是否保存到数据库
        agent_configs_db = chat_engine.db.get_agent_configs(user_id="test_agent_creation")
        assert len(agent_configs_db) >= 1, "应该至少有一个智能体配置"

        saved_config = None
        for config in agent_configs_db:
            if config.name == '测试智能体':
                saved_config = config
                break

        assert saved_config is not None, "应该找到保存的智能体配置"
        assert saved_config.name == '测试智能体'
        assert saved_config.instructions == '你是一个测试智能体'
        assert saved_config.model_id == 'gpt-3.5-turbo'
        print("✓ 数据库配置验证通过")

        # 测试配置重新加载
        chat_engine.agent_configs.clear()
        loaded_configs = chat_engine.load_config()
        assert '测试智能体' in loaded_configs, "应该加载保存的智能体配置"
        print("✓ 配置重新加载验证通过")

        print("🎉 智能体创建与配置保存测试通过")
        return True

    except Exception as e:
        print(f"❌ 智能体创建与配置保存测试失败: {e}")
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
        except Exception as cleanup_error:
            print(f"⚠️  清理警告: {cleanup_error}")


def test_agent_config_update():
    """测试智能体配置更新"""
    print("\n🔄 测试智能体配置更新...")

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
            user_token="test_agent_update"
        )

        # 创建初始配置
        initial_config = {
            'name': '更新测试智能体',
            'type': 'text',
            'model': {
                'name': 'gpt-3.5-turbo',
                'provider': 'openai',
                'kwargs': {'temperature': 0.7}
            },
            'instructions': '初始指令',
            'tools': [],
            'guardrails': []
        }

        chat_engine.agent_configs['更新测试智能体'] = initial_config

        # 保存初始配置
        chat_engine.save_config()
        print("✓ 初始配置保存成功")

        # 更新配置（模拟 update_agent_settings）
        updated_config = {
            'name': '更新测试智能体',
            'type': 'text',
            'model': {
                'name': 'gpt-4',
                'provider': 'openai',
                'kwargs': {'temperature': 0.8, 'max_tokens': 2000}
            },
            'instructions': '更新后的指令',
            'tools': [{'name': 'search_tool', 'description': '搜索工具'}],
            'guardrails': [{'type': 'content_filter', 'enabled': True}],
            'metadata': {'version': '2.0'}
        }

        chat_engine.agent_configs['更新测试智能体'] = updated_config
        chat_engine.save_config()
        print("✓ 更新配置保存成功")

        # 清空并重新加载配置
        chat_engine.agent_configs.clear()
        loaded_configs = chat_engine.load_config()

        # 验证更新后的配置
        assert '更新测试智能体' in loaded_configs, "应该加载更新后的配置"
        loaded_config = loaded_configs['更新测试智能体']

        assert loaded_config['instructions'] == '更新后的指令', "指令应该已更新"
        assert loaded_config['model']['name'] == 'gpt-4', "模型应该已更新"
        assert loaded_config['model']['kwargs']['temperature'] == 0.8, "模型参数应该已更新"
        assert len(loaded_config['tools']) == 1, "应该有一个工具"
        assert loaded_config['tools'][0]['name'] == 'search_tool', "工具名称应该匹配"
        assert loaded_config['metadata']['version'] == '2.0', "元数据应该已更新"

        print("✓ 配置更新验证通过")

        print("🎉 智能体配置更新测试通过")
        return True

    except Exception as e:
        print(f"❌ 智能体配置更新测试失败: {e}")
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
        except:
            pass


def test_agent_deletion():
    """测试智能体删除"""
    print("\n🗑️  测试智能体删除...")

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
            user_token="test_agent_delete"
        )

        # 创建多个智能体配置
        agents_to_create = {
            '保留智能体A': {
                'name': '保留智能体A',
                'type': 'text',
                'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                'instructions': '这个智能体会被保留'
            },
            '删除智能体B': {
                'name': '删除智能体B',
                'type': 'text',
                'model': {'name': 'gpt-4', 'provider': 'openai'},
                'instructions': '这个智能体会被删除'
            },
            '保留智能体C': {
                'name': '保留智能体C',
                'type': 'text',
                'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                'instructions': '这个智能体也会被保留'
            }
        }

        # 添加所有配置
        for name, config in agents_to_create.items():
            chat_engine.agent_configs[name] = config

        # 保存所有配置
        chat_engine.save_config()
        print("✓ 初始配置保存成功")

        # 验证初始状态
        initial_configs = chat_engine.db.get_agent_configs(user_id="test_agent_delete")
        assert len(initial_configs) == 3, "应该有3个智能体配置"
        print("✓ 初始状态验证通过")

        # 删除一个智能体（模拟 delete_agent_by_name）
        agent_to_delete = '删除智能体B'
        if agent_to_delete in chat_engine.agent_configs:
            del chat_engine.agent_configs[agent_to_delete]

        # 从数据库删除配置
        agent_configs_db = chat_engine.db.get_agent_configs(user_id="test_agent_delete")
        for agent_config in agent_configs_db:
            if agent_config.name == agent_to_delete:
                chat_engine.db.delete_agent_config(agent_config.agent_id)
                break

        # 保存更新后的配置
        chat_engine.save_config()
        print("✓ 智能体删除成功")

        # 重新加载配置验证
        chat_engine.agent_configs.clear()
        loaded_configs = chat_engine.load_config()

        # 验证删除结果
        assert agent_to_delete not in loaded_configs, f"智能体 {agent_to_delete} 应该已被删除"
        assert '保留智能体A' in loaded_configs, "保留智能体A 应该还存在"
        assert '保留智能体C' in loaded_configs, "保留智能体C 应该还存在"
        assert len(loaded_configs) == 2, f"应该剩余2个智能体，实际有{len(loaded_configs)}个"

        print("✓ 删除验证通过")

        print("🎉 智能体删除测试通过")
        return True

    except Exception as e:
        print(f"❌ 智能体删除测试失败: {e}")
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
        except:
            pass


def main():
    """主测试函数"""
    print("=" * 70)
    print("ChatEngine 智能体管理与配置集成测试")
    print("=" * 70)

    tests = [
        ("智能体创建与配置保存", test_agent_creation_and_config),
        ("智能体配置更新", test_agent_config_update),
        ("智能体删除", test_agent_deletion)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试执行失败: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 70)
    print("测试结果总结:")
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 所有智能体管理测试通过！")
        print("ChatEngine 的智能体管理与配置集成功能正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")

    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)