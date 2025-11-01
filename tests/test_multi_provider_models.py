#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Provider Model Creation Test

测试ChatEngine的create_model_from_dict功能
验证支持OpenAI、Ollama、DeepSeek、SiliconFlow、OpenRouter等Provider
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestMultiProviderModels(unittest.TestCase):
    """测试多Provider模型创建功能"""

    def setUp(self):
        """测试设置"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # 延迟导入ChatEngine，避免在模块级别导入错误
        try:
            from chat_engine import ChatEngine
            self.ChatEngine = ChatEngine
        except ImportError as e:
            self.skipTest(f"无法导入ChatEngine: {e}")

    def tearDown(self):
        """测试清理"""
        # 删除临时数据库文件
        try:
            os.unlink(self.db_path)
        except:
            pass

    def test_create_openai_model(self):
        """测试创建OpenAI模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # OpenAI模型配置
        openai_config = {
            'name': 'gpt-4',
            'provider': 'openai',
            'kwargs': {
                'api_key': 'sk-test-key',
                'temperature': 0.7,
                'max_tokens': 1000,
                'organization': 'test-org'
            }
        }

        model = engine.create_model_from_dict(openai_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'gpt-4')
        self.assertIn('OpenAI', str(model))

        print(f"✓ OpenAI模型创建成功: {model}")

    def test_create_ollama_model(self):
        """测试创建Ollama模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # Ollama模型配置
        ollama_config = {
            'name': 'llama3.1',
            'provider': 'ollama',
            'kwargs': {
                'host': 'http://localhost:11434',
                'temperature': 0.8,
                'timeout': 30
            }
        }

        model = engine.create_model_from_dict(ollama_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'llama3.1')
        self.assertIn('Ollama', str(model))

        print(f"✓ Ollama模型创建成功: {model}")

    def test_create_deepseek_model(self):
        """测试创建DeepSeek模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # DeepSeek模型配置
        deepseek_config = {
            'name': 'deepseek-chat',
            'provider': 'deepseek',
            'kwargs': {
                'api_key': 'sk-deepseek-key',
                'temperature': 0.6,
                'max_tokens': 2000
            }
        }

        model = engine.create_model_from_dict(deepseek_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'deepseek-chat')
        self.assertIn('DeepSeek', str(model))

        print(f"✓ DeepSeek模型创建成功: {model}")

    def test_create_siliconflow_model(self):
        """测试创建SiliconFlow模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # SiliconFlow模型配置
        siliconflow_config = {
            'name': 'Qwen/QwQ-32B',
            'provider': 'siliconflow',
            'kwargs': {
                'api_key': 'sk-siliconflow-key',
                'temperature': 0.5,
                'max_tokens': 1500
            }
        }

        model = engine.create_model_from_dict(siliconflow_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'Qwen/QwQ-32B')
        self.assertIn('Siliconflow', str(model))

        print(f"✓ SiliconFlow模型创建成功: {model}")

    def test_create_openrouter_model(self):
        """测试创建OpenRouter模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # OpenRouter模型配置
        openrouter_config = {
            'name': 'gpt-4o',
            'provider': 'openrouter',
            'kwargs': {
                'api_key': 'sk-openrouter-key',
                'max_tokens': 1024,
                'models': ['anthropic/claude-sonnet-4', 'deepseek/deepseek-r1']  # fallback models
            }
        }

        model = engine.create_model_from_dict(openrouter_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'gpt-4o')
        self.assertIn('OpenRouter', str(model))

        print(f"✓ OpenRouter模型创建成功: {model}")

    def test_create_unsupported_provider_model(self):
        """测试创建不支持的Provider模型（应该创建Mock模型）"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 不支持的Provider配置
        unsupported_config = {
            'name': 'test-model',
            'provider': 'unsupported-provider',
            'kwargs': {
                'api_key': 'test-key',
                'temperature': 0.7
            }
        }

        model = engine.create_model_from_dict(unsupported_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'test-model')
        self.assertIn('Mock', str(model))

        print(f"✓ 不支持Provider的Mock模型创建成功: {model}")

    def test_create_model_with_minimal_config(self):
        """测试使用最小配置创建模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 最小配置（只有name，默认使用openai）
        minimal_config = {
            'name': 'gpt-3.5-turbo'
        }

        model = engine.create_model_from_dict(minimal_config)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'gpt-3.5-turbo')

        print(f"✓ 最小配置模型创建成功: {model}")

    def test_create_model_with_invalid_config(self):
        """测试使用无效配置创建模型"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 测试空配置
        model1 = engine.create_model_from_dict(None)
        self.assertIsNone(model1)

        # 测试空字典
        model2 = engine.create_model_from_dict({})
        self.assertIsNone(model2)

        # 测试缺少name字段
        model3 = engine.create_model_from_dict({'provider': 'openai'})
        self.assertIsNone(model3)

        print("✓ 无效配置测试通过")

    def test_agent_creation_with_multi_provider_models(self):
        """测试使用多Provider模型创建Agent"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 测试所有Provider的Agent创建
        provider_configs = [
            {
                'name': 'gpt-4',
                'provider': 'openai',
                'kwargs': {'api_key': 'sk-test', 'temperature': 0.7}
            },
            {
                'name': 'llama3.1',
                'provider': 'ollama',
                'kwargs': {'host': 'http://localhost:11434'}
            },
            {
                'name': 'deepseek-chat',
                'provider': 'deepseek',
                'kwargs': {'api_key': 'sk-test', 'temperature': 0.6}
            },
            {
                'name': 'Qwen/QwQ-32B',
                'provider': 'siliconflow',
                'kwargs': {'api_key': 'sk-test', 'temperature': 0.5}
            },
            {
                'name': 'gpt-4o',
                'provider': 'openrouter',
                'kwargs': {'api_key': 'sk-test', 'max_tokens': 1024}
            }
        ]

        for i, model_config in enumerate(provider_configs):
            agent_config = {
                'agent_id': f'test_agent_{i}',
                'name': f'Test Agent {model_config["provider"].title()}',
                'model': model_config,
                'instructions': f'You are a test agent using {model_config["provider"].title()} model.'
            }

            agent = engine.create_new_agent(f'Test Agent {model_config["provider"].title()}', agent_config)

            self.assertIsNotNone(agent)
            self.assertEqual(agent.name, f'Test Agent {model_config["provider"].title()}')
            print(f"✓ Agent创建成功 ({model_config['provider']}): {agent.name}")

    def test_model_parameter_filtering(self):
        """测试模型参数过滤功能"""
        engine = self.ChatEngine(config_path=self.db_path, user_id="test_user")

        # 包含None值的配置
        config_with_none = {
            'name': 'gpt-4',
            'provider': 'openai',
            'kwargs': {
                'api_key': 'sk-test',
                'temperature': 0.7,
                'max_tokens': None,  # 这个应该被过滤掉
                'organization': None,  # 这个应该被过滤掉
                'timeout': 30  # 这个应该保留
            }
        }

        model = engine.create_model_from_dict(config_with_none)

        self.assertIsNotNone(model)
        self.assertEqual(model.id, 'gpt-4')

        # 检查参数是否正确过滤
        if hasattr(model, 'kwargs'):
            self.assertNotIn('max_tokens', model.kwargs)
            self.assertNotIn('organization', model.kwargs)
            self.assertEqual(model.kwargs.get('timeout'), 30)

        print(f"✓ 模型参数过滤测试通过: {model}")

def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("Multi-Provider Model Creation Test")
    print("=" * 80)

    # 运行测试
    unittest.main(verbosity=2, exit=False)

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    run_tests()