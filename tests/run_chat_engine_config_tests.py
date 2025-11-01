#!/usr/bin/env python3
"""
ChatEngine 配置功能测试运行器

运行所有与 ChatEngine 配置保存和加载相关的测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test(test_name, test_module):
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"运行 {test_name}")
    print(f"{'='*60}")

    try:
        # 动态导入测试模块
        if isinstance(test_module, str):
            test_module = __import__(test_module, fromlist=['main'])

        # 运行测试
        if hasattr(test_module, 'main'):
            result = test_module.main()
        else:
            print(f"❌ 测试模块 {test_name} 没有 main() 函数")
            result = False

        return result

    except ImportError as e:
        print(f"❌ 导入 {test_name} 失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 运行 {test_name} 时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试运行器"""
    print("🚀 ChatEngine 配置功能测试套件")
    print("测试 ChatEngine 的配置保存、加载和智能体管理功能")

    # 定义要运行的测试
    tests = [
        ("基本配置功能", "simple_chat_engine_config_test"),
        ("智能体管理集成", "test_chat_engine_agent_management"),
        ("完整配置测试", "test_chat_engine_config")
    ]

    results = []

    for test_name, test_module_name in tests:
        print(f"\n📋 准备运行: {test_name}")

        try:
            # 检查测试文件是否存在
            test_file = project_root / "tests" / f"{test_module_name}.py"
            if not test_file.exists():
                print(f"⚠️  测试文件不存在: {test_file}")
                results.append((test_name, False, "测试文件不存在"))
                continue

            # 运行测试
            success = run_test(test_name, test_module_name)
            results.append((test_name, success, "通过" if success else "失败"))

        except Exception as e:
            print(f"❌ 运行 {test_name} 时发生异常: {e}")
            results.append((test_name, False, f"异常: {e}"))

    # 输出测试结果总结
    print(f"\n{'='*80}")
    print("测试结果总结")
    print(f"{'='*80}")

    passed_count = 0
    total_count = len(results)

    for test_name, success, status in results:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name:<30} {status}")
        if success:
            passed_count += 1

    print(f"\n统计: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("\n🎉 所有 ChatEngine 配置测试通过！")
        print("✅ 配置保存功能正常")
        print("✅ 配置加载功能正常")
        print("✅ 配置持久性正常")
        print("✅ 智能体管理集成正常")
        print("\nChatEngine 的配置系统工作正常，可以安全使用。")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        print("请检查上述错误信息并修复相关问题。")
        return False


def run_quick_test():
    """运行快速测试（仅基本功能）"""
    print("🚀 运行 ChatEngine 配置快速测试...")

    try:
        # 只运行基本配置测试
        success = run_test("基本配置功能", "simple_chat_engine_config_test")

        if success:
            print("\n🎉 快速测试通过！")
            print("ChatEngine 基本配置功能正常。")
        else:
            print("\n❌ 快速测试失败，请检查配置功能。")

        return success

    except Exception as e:
        print(f"❌ 快速测试执行失败: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChatEngine 配置功能测试运行器")
    parser.add_argument("--quick", action="store_true", help="仅运行快速测试")
    parser.add_argument("--test", type=str, help="运行指定的测试模块")

    args = parser.parse_args()

    if args.quick:
        success = run_quick_test()
    elif args.test:
        # 运行指定的测试
        test_module = args.test
        if not test_module.endswith('.py'):
            test_module += '.py'

        test_name = test_module.replace('.py', '').replace('_', ' ').title()
        success = run_test(test_name, test_module)

        if success:
            print(f"\n🎉 {test_name} 测试通过！")
        else:
            print(f"\n❌ {test_name} 测试失败。")
    else:
        # 运行所有测试
        success = main()

    sys.exit(0 if success else 1)