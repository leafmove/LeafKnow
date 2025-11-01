"""
ChatEngine 配置保存和加载功能测试

测试目标：
1. 测试 ChatEngine.save_config() 方法
2. 测试 ChatEngine.load_config() 方法
3. 测试配置的持久性
4. 测试智能体配置的管理
"""

import sys
import tempfile
import os
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestChatEngineConfig:
    """ChatEngine 配置功能测试类"""

    def __init__(self):
        self.temp_db = None
        self.db_path = None
        self.chat_engine = None
        self.test_user_token = "test_user_config"

    def setup(self):
        """测试前准备"""
        # 创建临时数据库文件
        self.db_path = r"D:\Workspace\LeafKnow\autobox_id.db"

        # 初始化 ChatEngine
        from chat_engine import ChatEngine
        self.chat_engine = ChatEngine(
            config_path=self.db_path,
            user_token=self.test_user_token
        )

        print(f"[OK] 测试环境准备完成，数据库路径: {self.db_path}")

    def teardown(self):
        """测试后清理"""
        try:
            # 清理 ChatEngine 资源
            if self.chat_engine:
                if hasattr(self.chat_engine, 'executor'):
                    self.chat_engine.executor.shutdown(wait=True)
                if hasattr(self.chat_engine, 'db'):
                    if hasattr(self.chat_engine.db, 'Session'):
                        self.chat_engine.db.Session.remove()
                    if hasattr(self.chat_engine.db, 'db_engine'):
                        self.chat_engine.db.db_engine.dispose()

            # 删除临时数据库文件
            time.sleep(0.1)
            print("[OK] 资源清理完成")
        except Exception as e:
            print(f"[WARN]  清理资源时出现警告: {e}")

    def test_save_config_basic(self):
        """测试基本配置保存功能"""
        print("\n=== 测试基本配置保存功能 ===")

        try:
            # 创建测试智能体配置
            test_agent_config = {
                'agent_id': 'test_agent_001',
                'name': '测试智能体',
                'type': 'text',
                'model': {
                    'name': 'gpt-3.5-turbo',
                    'provider': 'openai',
                    'kwargs': {'temperature': 0.7}
                },
                'instructions': '你是一个有用的AI助手',
                'tools': [{'name': 'calculator', 'description': '计算工具'}],
                'knowledge': {'type': 'general'},
                'memory': {'max_messages': 50},
                'guardrails': [{'type': 'content_filter'}],
                'metadata': {'version': '1.0'}
            }

            # 添加配置到 ChatEngine
            self.chat_engine.agent_configs['测试智能体'] = test_agent_config

            # 保存配置
            self.chat_engine.save_config()

            # 验证配置是否保存到数据库
            agent_configs_db = self.chat_engine.db.get_agent_configs(user_id=self.test_user_token)
            saved_config = None
            for config in agent_configs_db:
                if config.name == '测试智能体':
                    saved_config = config
                    break

            assert saved_config is not None, "配置应该已保存到数据库"
            assert saved_config.name == '测试智能体', "智能体名称应该匹配"
            assert saved_config.model_id == 'gpt-3.5-turbo', "模型ID应该匹配"
            assert saved_config.model_provider == 'openai', "模型提供商应该匹配"

            print("[OK] 基本配置保存功能测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 基本配置保存功能测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_load_config_basic(self):
        """测试基本配置加载功能"""
        print("\n=== 测试基本配置加载功能 ===")

        try:
            # 先保存一些配置到数据库
            test_agent_config = {
                'agent_id': 'test_agent_load',
                'name': '加载测试智能体',
                'type': 'text',
                'model': {
                    'name': 'gpt-4',
                    'provider': 'openai',
                    'kwargs': {'temperature': 0.8}
                },
                'instructions': '用于测试加载功能的智能体',
                'tools': [],
                'knowledge': None,
                'memory': None,
                'guardrails': [],
                'metadata': {'test': True}
            }

            # 直接保存到数据库
            from core.agno.db.sqlite.config_data import AgentConfig
            agent_config_obj = AgentConfig.from_dict({
                **test_agent_config,
                'user_id': self.test_user_token
            })
            self.chat_engine.db.upsert_agent_config(agent_config_obj)

            # 调用 load_config 加载配置
            loaded_configs = self.chat_engine.load_config()

            # 验证加载的配置
            assert '加载测试智能体' in loaded_configs, "应该加载出保存的智能体配置"
            loaded_config = loaded_configs['加载测试智能体']
            assert loaded_config['name'] == '加载测试智能体', "智能体名称应该匹配"
            assert loaded_config['model']['name'] == 'gpt-4', "模型名称应该匹配"
            assert loaded_config['instructions'] == '用于测试加载功能的智能体', "指令应该匹配"

            print("[OK] 基本配置加载功能测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 基本配置加载功能测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_config_persistence(self):
        """测试配置持久性"""
        print("\n=== 测试配置持久性 ===")

        try:
            # 创建第一个 ChatEngine 实例并保存配置
            agent_config = {
                'agent_id': 'persistence_test_agent',
                'name': '持久性测试智能体',
                'type': 'text',
                'model': {
                    'name': 'gpt-3.5-turbo',
                    'provider': 'openai'
                },
                'instructions': '测试配置持久性',
                'tools': [],
                'guardrails': []
            }

            self.chat_engine.agent_configs['持久性测试智能体'] = agent_config
            self.chat_engine.save_config()

            # 关闭第一个实例
            if hasattr(self.chat_engine, 'db'):
                if hasattr(self.chat_engine.db, 'Session'):
                    self.chat_engine.db.Session.remove()
                if hasattr(self.chat_engine.db, 'db_engine'):
                    self.chat_engine.db.db_engine.dispose()

            # 创建新的 ChatEngine 实例
            from chat_engine import ChatEngine
            new_chat_engine = ChatEngine(
                config_path=self.db_path,
                user_token=self.test_user_token
            )

            # 验证新实例是否加载了之前保存的配置
            assert '持久性测试智能体' in new_chat_engine.agent_configs, "新实例应该加载保存的配置"
            loaded_config = new_chat_engine.agent_configs['持久性测试智能体']
            assert loaded_config['name'] == '持久性测试智能体', "智能体名称应该匹配"
            assert loaded_config['instructions'] == '测试配置持久性', "指令应该匹配"

            # 清理
            if hasattr(new_chat_engine, 'db'):
                if hasattr(new_chat_engine.db, 'Session'):
                    new_chat_engine.db.Session.remove()
                if hasattr(new_chat_engine.db, 'db_engine'):
                    new_chat_engine.db.db_engine.dispose()

            print("[OK] 配置持久性测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 配置持久性测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_multiple_agents_config(self):
        """测试多个智能体配置管理"""
        print("\n=== 测试多个智能体配置管理 ===")

        try:
            # 创建多个智能体配置
            agent_configs = {
                '智能体A': {
                    'agent_id': 'agent_a',
                    'name': '智能体A',
                    'type': 'text',
                    'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                    'instructions': '你是智能体A',
                    'tools': [],
                    'guardrails': []
                },
                '智能体B': {
                    'agent_id': 'agent_b',
                    'name': '智能体B',
                    'type': 'text',
                    'model': {'name': 'gpt-4', 'provider': 'openai'},
                    'instructions': '你是智能体B',
                    'tools': [{'name': 'search'}],
                    'guardrails': []
                },
                '智能体C': {
                    'agent_id': 'agent_c',
                    'name': '智能体C',
                    'type': 'image_analysis',
                    'model': {'name': 'gpt-4-vision', 'provider': 'openai'},
                    'instructions': '你是智能体C，专门分析图像',
                    'tools': [],
                    'guardrails': [{'type': 'safety_filter'}]
                }
            }

            # 添加配置到 ChatEngine
            for name, config in agent_configs.items():
                self.chat_engine.agent_configs[name] = config

            # 保存所有配置
            self.chat_engine.save_config()

            # 清空内存中的配置
            self.chat_engine.agent_configs.clear()

            # 重新加载配置
            loaded_configs = self.chat_engine.load_config()

            # 验证所有配置都被正确加载
            assert len(loaded_configs) == 3, f"应该加载3个配置，实际加载了{len(loaded_configs)}个"

            for name, original_config in agent_configs.items():
                assert name in loaded_configs, f"应该加载配置: {name}"
                loaded_config = loaded_configs[name]
                assert loaded_config['name'] == original_config['name'], "名称应该匹配"
                assert loaded_config['instructions'] == original_config['instructions'], "指令应该匹配"
                assert loaded_config['model']['name'] == original_config['model']['name'], "模型应该匹配"

            print("[OK] 多个智能体配置管理测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 多个智能体配置管理测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_config_update_and_reload(self):
        """测试配置更新和重新加载"""
        print("\n=== 测试配置更新和重新加载 ===")

        try:
            # 创建初始配置
            initial_config = {
                'agent_id': 'update_test_agent',
                'name': '更新测试智能体',
                'type': 'text',
                'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                'instructions': '初始指令',
                'tools': [],
                'guardrails': []
            }

            self.chat_engine.agent_configs['更新测试智能体'] = initial_config
            self.chat_engine.save_config()

            # 更新配置
            updated_config = {
                'agent_id': 'update_test_agent',
                'name': '更新测试智能体',
                'type': 'text',
                'model': {'name': 'gpt-4', 'provider': 'openai'},
                'instructions': '更新后的指令',
                'tools': [{'name': 'new_tool'}],
                'guardrails': [{'type': 'content_filter'}]
            }

            self.chat_engine.agent_configs['更新测试智能体'] = updated_config
            self.chat_engine.save_config()

            # 清空内存并重新加载
            self.chat_engine.agent_configs.clear()
            loaded_configs = self.chat_engine.load_config()

            # 验证更新后的配置
            assert '更新测试智能体' in loaded_configs, "应该加载更新后的配置"
            loaded_config = loaded_configs['更新测试智能体']
            assert loaded_config['instructions'] == '更新后的指令', "应该加载更新后的指令"
            assert loaded_config['model']['name'] == 'gpt-4', "应该加载更新后的模型"
            assert len(loaded_config['tools']) == 1, "应该加载更新后的工具"
            assert loaded_config['tools'][0]['name'] == 'new_tool', "工具名称应该匹配"

            print("[OK] 配置更新和重新加载测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 配置更新和重新加载测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_config_with_edge_cases(self):
        """测试配置的边界情况"""
        print("\n=== 测试配置的边界情况 ===")

        try:
            # 测试空配置
            self.chat_engine.agent_configs.clear()
            self.chat_engine.save_config()

            self.chat_engine.agent_configs.clear()
            loaded_configs = self.chat_engine.load_config()
            assert len(loaded_configs) == 0, "空配置加载后应该为空"

            # 测试包含特殊字符的配置
            special_config = {
                'agent_id': 'special_agent',
                'name': '特殊字符测试智能体!@#$%^&*()',
                'type': 'text',
                'model': {'name': 'gpt-3.5-turbo', 'provider': 'openai'},
                'instructions': '包含特殊字符的指令：中文、English、123、!@#',
                'tools': [],
                'guardrails': []
            }

            self.chat_engine.agent_configs['特殊字符测试智能体!@#$%^&*()'] = special_config
            self.chat_engine.save_config()

            self.chat_engine.agent_configs.clear()
            loaded_configs = self.chat_engine.load_config()

            assert '特殊字符测试智能体!@#$%^&*()' in loaded_configs, "应该加载包含特殊字符的配置"
            loaded_config = loaded_configs['特殊字符测试智能体!@#$%^&*()']
            assert loaded_config['instructions'] == special_config['instructions'], "特殊字符指令应该匹配"

            print("[OK] 配置边界情况测试通过")
            return True

        except Exception as e:
            print(f"[FAIL] 配置边界情况测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_chat_engine_config_tests():
    """运行所有 ChatEngine 配置测试"""
    print("=" * 70)
    print("ChatEngine 配置保存和加载功能测试")
    print("=" * 70)

    test_instance = TestChatEngineConfig()

    tests = [
        ("基本配置保存", test_instance.test_save_config_basic),
        ("基本配置加载", test_instance.test_load_config_basic),
        ("配置持久性", test_instance.test_config_persistence),
        ("多智能体配置管理", test_instance.test_multiple_agents_config),
        ("配置更新和重新加载", test_instance.test_config_update_and_reload),
        ("配置边界情况", test_instance.test_config_with_edge_cases)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            test_instance.setup()
            result = test_func()
            results.append((test_name, result))
            test_instance.teardown()
        except Exception as e:
            print(f"[FAIL] {test_name}测试执行失败: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 70)
    print("测试结果总结:")
    all_passed = True
    for test_name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] 所有 ChatEngine 配置测试通过！")
        print("配置保存和加载功能工作正常。")
    else:
        print("\n[WARN]  部分测试失败，请检查上述错误信息。")

    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_chat_engine_config_tests()
    sys.exit(0 if success else 1)