#!/usr/bin/env python3
"""
快速测试聊天功能
"""

import asyncio
import time
from enhanced_chat_app import EnhancedChatApp


async def test_chat_functionality():
    """测试聊天功能"""
    print("=" * 50)
    print("测试聊天功能")
    print("=" * 50)

    app = EnhancedChatApp()

    # 确保Agent已创建
    if not app.current_agent:
        app._create_current_agent()

    if not app.current_agent:
        print("[ERROR] Agent创建失败，无法测试聊天功能")
        return

    print(f"[OK] 使用模型: {app.model_manager.current_model}")
    print(f"[OK] Agent类型: {type(app.current_agent.model).__name__}")

    # 测试非流式聊天
    print("\n1. 测试非流式聊天:")
    test_message = "你好，请简单介绍一下你自己。"
    print(f"用户: {test_message}")
    print("AI: ", end="", flush=True)

    start_time = time.time()
    try:
        response = app.chat_non_streaming(test_message)
        print(response)
        end_time = time.time()
        print(f"[OK] 非流式聊天成功，耗时: {end_time - start_time:.2f}秒")
    except Exception as e:
        print(f"[ERROR] 非流式聊天失败: {str(e)}")

    # 测试流式聊天
    print("\n2. 测试流式聊天:")
    test_message2 = "请用一句话说明AI的优点。"
    print(f"用户: {test_message2}")
    print("AI: ", end="", flush=True)

    start_time = time.time()
    try:
        response_parts = []
        async for chunk in app.chat_streaming(test_message2):
            print(chunk, end="", flush=True)
            response_parts.append(chunk)
        print()  # 换行
        end_time = time.time()
        print(f"[OK] 流式聊天成功，耗时: {end_time - start_time:.2f}秒")
        print(f"[OK] 总回复长度: {len(''.join(response_parts))} 字符")
    except Exception as e:
        print(f"\n[ERROR] 流式聊天失败: {str(e)}")


def test_model_switching():
    """测试模型切换功能"""
    print("\n" + "=" * 50)
    print("测试模型切换")
    print("=" * 50)

    app = EnhancedChatApp()

    # 获取可用模型
    models = app.model_manager.list_models()
    print(f"可用模型数量: {len(models)}")

    for i, model in enumerate(models[:3], 1):  # 只测试前3个模型
        print(f"\n{i}. 测试模型: {model.name}")
        try:
            if app.model_manager.set_current_model(model.name):
                app._create_current_agent()
                print(f"[OK] 成功切换到: {model.name}")
            else:
                print(f"[FAIL] 切换失败: {model.name}")
        except Exception as e:
            print(f"[ERROR] 模型切换异常: {str(e)}")


def test_ollama_integration():
    """测试Ollama集成"""
    print("\n" + "=" * 50)
    print("测试Ollama集成")
    print("=" * 50)

    app = EnhancedChatApp()

    # 测试添加Ollama模型
    from enhanced_chat_app import ModelConfig, OLLAMA_AVAILABLE

    if OLLAMA_AVAILABLE:
        ollama_config = ModelConfig(
            name="Test Ollama",
            model_id="llama3",
            provider="ollama",
            base_url="http://localhost:11434",
            is_local=True
        )

        print("1. 测试添加Ollama模型:")
        if app.model_manager.add_model(ollama_config):
            print("[OK] Ollama模型添加成功")
        else:
            print("[FAIL] Ollama模型添加失败")

        print("2. 测试切换到Ollama模型:")
        if app.model_manager.set_current_model("Test Ollama"):
            try:
                app._create_current_agent()
                if app.current_agent:
                    print("[OK] Ollama Agent创建成功")
                else:
                    print("[FAIL] Ollama Agent创建失败")
            except Exception as e:
                print(f"[ERROR] Ollama Agent创建异常: {str(e)}")
        else:
            print("[FAIL] 切换到Ollama模型失败")
    else:
        print("[WARN] Ollama不可用，跳过测试")


def main():
    """主测试函数"""
    print("聊天功能快速测试")
    print("=" * 60)
    print("注意: 这个测试需要有效的API密钥才能完全成功")

    try:
        # 测试聊天功能
        asyncio.run(test_chat_functionality())

        # 测试模型切换
        test_model_switching()

        # 测试Ollama集成
        test_ollama_integration()

        print("\n" + "=" * 60)
        print("测试完成!")
        print("\n使用说明:")
        print("1. 应用已修复Python 3.8兼容性问题")
        print("2. 支持OpenAI、OpenRouter、Ollama等模型")
        print("3. 支持智能模型切换: '模型名: 消息'")
        print("4. 支持流式和非流式输出")
        print("5. 运行应用: python enhanced_chat_app.py")

    except Exception as e:
        print(f"[ERROR] 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()