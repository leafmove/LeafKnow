#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Multi-Provider Model Creation

调试ChatEngine的create_model_from_dict功能
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def debug_multi_provider_models():
    """调试多Provider模型创建"""
    print("=" * 80)
    print("Debug Multi-Provider Model Creation")
    print("=" * 80)

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

        # 测试各种Provider
        providers = [
            {
                'name': 'gpt-4',
                'provider': 'openai',
                'description': 'OpenAI GPT-4'
            },
            {
                'name': 'llama3.1',
                'provider': 'ollama',
                'description': 'Ollama Llama 3.1'
            },
            {
                'name': 'deepseek-chat',
                'provider': 'deepseek',
                'description': 'DeepSeek Chat'
            },
            {
                'name': 'Qwen/QwQ-32B',
                'provider': 'siliconflow',
                'description': 'SiliconFlow Qwen/QwQ-32B'
            },
            {
                'name': 'gpt-4o',
                'provider': 'openrouter',
                'description': 'OpenRouter GPT-4o'
            }
        ]

        for provider_config in providers:
            print(f"\n--- 测试 {provider_config['description']} ---")

            # 构建模型配置
            model_config = {
                'name': provider_config['name'],
                'provider': provider_config['provider'],
                'kwargs': {
                    'api_key': f'sk-test-{provider_config["provider"]}',
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            }

            print(f"配置: {model_config}")

            # 创建模型
            model = engine.create_model_from_dict(model_config)

            if model:
                print(f"[SUCCESS] 模型创建成功: {model}")
                print(f"  - 模型ID: {model.id}")
                print(f"  - 模型名称: {model.name}")
                print(f"  - Provider: {model.provider}")
            else:
                print("[ERROR] 模型创建失败，返回None")

        # 测试不支持的Provider
        print(f"\n--- 测试不支持的Provider ---")
        unsupported_config = {
            'name': 'test-model',
            'provider': 'unsupported-provider',
            'kwargs': {'api_key': 'test-key'}
        }

        print(f"配置: {unsupported_config}")
        mock_model = engine.create_model_from_dict(unsupported_config)

        if mock_model:
            print(f"[SUCCESS] Mock模型创建成功: {mock_model}")
        else:
            print("[ERROR] Mock模型创建失败")

        # 测试错误处理
        print(f"\n--- 测试错误处理 ---")

        # 测试None
        result1 = engine.create_model_from_dict(None)
        print(f"None输入: {result1}")

        # 测试空字典
        result2 = engine.create_model_from_dict({})
        print(f"空字典输入: {result2}")

        # 测试缺少name
        result3 = engine.create_model_from_dict({'provider': 'openai'})
        print(f"缺少name字段: {result3}")

        # 测试最小配置
        print(f"\n--- 测试最小配置 ---")
        minimal_config = {'name': 'gpt-3.5-turbo'}
        minimal_model = engine.create_model_from_dict(minimal_config)

        if minimal_model:
            print(f"[SUCCESS] 最小配置模型创建成功: {minimal_model}")
        else:
            print("[ERROR] 最小配置模型创建失败")

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

    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)

if __name__ == '__main__':
    debug_multi_provider_models()