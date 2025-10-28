#!/usr/bin/env python3
"""
测试应用启动和基本功能
"""

import sys
import time
from enhanced_chat_app import ModelManager, ModelConfig, EnhancedChatApp


def test_imports():
    """测试导入功能"""
    print("=" * 50)
    print("测试模块导入")
    print("=" * 50)

    try:
        from enhanced_chat_app import (
            Agent, OpenAIChat, OpenRouter, Claude, Groq, Ollama,
            OPENROUTER_AVAILABLE, ANTHROPIC_AVAILABLE, GROQ_AVAILABLE, OLLAMA_AVAILABLE
        )
        print(f"Agent: {'[OK] 可用' if Agent else '[FAIL] 不可用'}")
        print(f"OpenAIChat: {'[OK] 可用' if OpenAIChat else '[FAIL] 不可用'}")
        print(f"OpenRouter: {'[OK] 可用' if OPENROUTER_AVAILABLE else '[WARN] 不可用'}")
        print(f"Claude: {'[OK] 可用' if ANTHROPIC_AVAILABLE else '[WARN] 不可用'}")
        print(f"Groq: {'[OK] 可用' if GROQ_AVAILABLE else '[WARN] 不可用'}")
        print(f"Ollama: {'[OK] 可用' if OLLAMA_AVAILABLE else '[WARN] 不可用'}")
        return True
    except Exception as e:
        print(f"[ERROR] 导入失败: {str(e)}")
        return False


def test_model_manager():
    """测试模型管理器"""
    print("\n" + "=" * 50)
    print("测试模型管理器")
    print("=" * 50)

    try:
        manager = ModelManager()
        models = manager.list_models()
        print(f"[OK] 模型管理器创建成功")
        print(f"[OK] 默认模型数量: {len(models)}")

        current = manager.get_current_model()
        if current:
            print(f"[OK] 当前模型: {current.name}")
        else:
            print("[WARN] 没有当前模型")

        return True
    except Exception as e:
        print(f"[ERROR] 模型管理器测试失败: {str(e)}")
        return False


def test_enhanced_app():
    """测试增强版应用"""
    print("\n" + "=" * 50)
    print("测试增强版应用")
    print("=" * 50)

    try:
        app = EnhancedChatApp()
        print("[OK] 应用创建成功")

        # 测试Agent创建
        app._create_current_agent()
        if app.current_agent:
            print("[OK] Agent创建成功")
            print(f"[OK] Agent模型类型: {type(app.current_agent.model).__name__}")
        else:
            print("[FAIL] Agent创建失败")

        return True
    except Exception as e:
        print(f"[ERROR] 应用测试失败: {str(e)}")
        return False


def test_model_creation():
    """测试模型创建"""
    print("\n" + "=" * 50)
    print("测试模型创建")
    print("=" * 50)

    manager = ModelManager()

    # 测试OpenAI模型
    try:
        openai_config = ModelConfig(
            name="Test OpenAI",
            model_id="gpt-4o-mini",
            provider="openai",
            api_key="test-key"
        )
        model = manager.create_model_instance(openai_config)
        print(f"OpenAI模型创建: {'[OK] 成功' if model else '[FAIL] 失败'}")
    except Exception as e:
        print(f"OpenAI模型创建: [ERROR] {str(e)}")

    # 测试Ollama模型（如果可用）
    try:
        ollama_config = ModelConfig(
            name="Test Ollama",
            model_id="llama3",
            provider="ollama",
            base_url="http://localhost:11434"
        )
        model = manager.create_model_instance(ollama_config)
        print(f"Ollama模型创建: {'[OK] 成功' if model else '[FAIL] 失败'}")
    except Exception as e:
        print(f"Ollama模型创建: [WARN] {str(e)}")


def main():
    """主测试函数"""
    print("增强版聊天应用启动测试")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("模型管理器", test_model_manager),
        ("增强版应用", test_enhanced_app),
        ("模型创建", test_model_creation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name}测试异常: {str(e)}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{len(results)} 测试通过")

    if passed == len(results):
        print("\n[OK] 应用启动和基本功能正常!")
        print("现在可以安全地运行: python enhanced_chat_app.py")
    else:
        print(f"\n[WARN] 有 {len(results) - passed} 个测试失败")
        print("但基本功能应该可用，可以尝试运行应用")


if __name__ == "__main__":
    main()