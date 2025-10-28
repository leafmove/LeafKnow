#!/usr/bin/env python3
"""
测试修复后的聊天应用
"""

import asyncio
from enhanced_chat_app import ModelManager, ModelConfig, EnhancedChatApp


def test_ollama_model_creation():
    """测试Ollama模型创建"""
    print("=" * 50)
    print("测试Ollama模型创建")
    print("=" * 50)

    manager = ModelManager()

    # 测试添加Ollama模型
    print("1. 手动添加Ollama模型...")
    ollama_config = ModelConfig(
        name="Ollama deepseek-r1:1.5b",
        model_id="deepseek-r1:1.5b",
        provider="ollama",
        base_url="http://localhost:11434",
        is_local=True,
        description="本地DeepSeek R1 1.5B模型"
    )

    success = manager.add_model(ollama_config)
    print(f"   添加Ollama模型: {'成功' if success else '失败'}")

    # 测试创建模型实例
    print("2. 创建Ollama模型实例...")
    model_instance = manager.create_model_instance(ollama_config)
    print(f"   模型实例创建: {'成功' if model_instance else '失败'}")

    if model_instance:
        print(f"   模型类型: {type(model_instance).__name__}")
        print(f"   模型ID: {getattr(model_instance, 'id', 'N/A')}")
    else:
        print("   [INFO] 这可能是因为ollama库未安装")

    # 测试设置当前模型
    print("3. 设置为当前模型...")
    if manager.set_current_model("Ollama deepseek-r1:1.5b"):
        print(f"   [OK] 已设置为当前模型")
        current = manager.get_current_model()
        if current:
            print(f"   当前模型: {current.name}")
    else:
        print(f"   [FAIL] 设置失败")


def test_model_parsing():
    """测试模型名称解析"""
    print("\n" + "=" * 50)
    print("测试模型名称解析")
    print("=" * 50)

    app = EnhancedChatApp()

    # 测试用例
    test_cases = [
        "Ollama deepseek-r1:1.5b: 你好",
        "deepseek-r1:1.5b: hello",
        "ollama llama3: tell me a joke",
        "llama3:2b: 你好吗",
        "OpenAI GPT-4o: what is ai",
        "普通的聊天消息，没有冒号",
        "https://example.com: some url",  # 应该被忽略
    ]

    print("测试用户输入解析:")
    for test_input in test_cases:
        print(f"\n输入: {test_input}")

        if ":" in test_input and not test_input.startswith(("http://", "https://", "ftp://")):
            potential_model, message = test_input.split(":", 1)
            potential_model = potential_model.strip()
            message = message.strip()
            print(f"   识别的模型: '{potential_model}'")
            print(f"   识别的消息: '{message}'")

            # 检查是否匹配现有模型
            found_model = None
            for model in app.model_manager.list_models():
                if (potential_model.lower() in model.name.lower() or
                    potential_model.lower() in model.model_id.lower() or
                    model.name.lower() in potential_model.lower() or
                    model.model_id.lower() in potential_model.lower()):
                    found_model = model
                    break

            if found_model:
                print(f"   [OK] 找到匹配模型: {found_model.name}")
            else:
                print(f"   [WARN] 未找到匹配模型")

                # 检查是否可能是Ollama模型
                if ("ollama" in potential_model.lower() or
                    any(keyword in potential_model.lower() for keyword in ["deepseek", "llama", "qwen", "mistral", "codellama"])):
                    print(f"   [INFO] 可能是Ollama模型，将尝试动态添加")
        else:
            print("   [INFO] 普通聊天消息")


def test_agent_creation():
    """测试Agent创建"""
    print("\n" + "=" * 50)
    print("测试Agent创建")
    print("=" * 50)

    app = EnhancedChatApp()

    # 添加测试用的Ollama模型
    ollama_config = ModelConfig(
        name="Test Ollama Model",
        model_id="deepseek-r1:1.5b",
        provider="ollama",
        base_url="http://localhost:11434",
        is_local=True
    )
    app.model_manager.add_model(ollama_config)

    # 设置为当前模型
    app.model_manager.set_current_model("Test Ollama Model")

    # 尝试创建Agent
    print("1. 创建Agent...")
    app._create_current_agent()

    if app.current_agent:
        print("   [OK] Agent创建成功")
        print(f"   Agent模型: {type(app.current_agent.model).__name__}")
    else:
        print("   [FAIL] Agent创建失败")


def main():
    """主测试函数"""
    print("修复验证测试")
    print("=" * 60)
    print("测试enhanced_chat_app.py的修复功能")

    try:
        test_ollama_model_creation()
        test_model_parsing()
        test_agent_creation()

        print("\n" + "=" * 60)
        print("测试完成!")
        print("\n使用说明:")
        print("1. 现在支持直接在聊天中输入 '模型名: 消息' 来切换模型")
        print("2. 支持格式: 'Ollama deepseek-r1:1.5b: 你好'")
        print("3. 支持格式: 'deepseek-r1:1.5b: hello'")
        print("4. 应用会自动识别并添加Ollama模型")
        print("5. 使用 'models' 命令管理模型配置")

    except Exception as e:
        print(f"[ERROR] 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()