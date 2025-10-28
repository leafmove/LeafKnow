#!/usr/bin/env python3
"""
测试运行器
用于运行所有 agno_modular 和 MCP 相关的测试
"""

import sys
import os
import unittest
import time
from io import StringIO

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestResult:
    """测试结果类"""
    def __init__(self):
        self.tests_run = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0
        self.success_rate = 0.0
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
        self.modules = {}


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.result = TestResult()

    def run_module_tests(self, module_name, test_file_path):
        """运行单个模块的测试"""
        print(f"\n{'='*60}")
        print(f"Running {module_name} tests")
        print(f"{'='*60}")

        # 动态导入测试模块
        spec = None
        module = None

        try:
            # 获取测试文件的目录名并添加到路径
            test_dir = os.path.dirname(test_file_path)
            if test_dir not in sys.path:
                sys.path.insert(0, test_dir)

            # 对于 agno_modular 测试，需要添加 agno_modular 目录到路径
            if 'agno_modular' in test_file_path:
                agno_modular_dir = os.path.join(os.getcwd(), 'agno_modular')
                if agno_modular_dir not in sys.path:
                    sys.path.insert(0, agno_modular_dir)

            # 导入测试模块
            module_name = os.path.basename(test_file_path)[:-3]  # 移除 .py 后缀
            spec = __import__(module_name)
            module = sys.modules[module_name]

        except Exception as e:
            print(f"[ERROR] Cannot import test module {module_name}: {e}")
            return False

        # 创建测试套件
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)

        # 创建测试运行器
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2,
            buffer=True
        )

        # 运行测试
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()

        # 解析结果
        output = stream.getvalue()
        print(output)

        # 更新结果
        module_result = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'duration': end_time - start_time,
            'success': result.wasSuccessful()
        }

        self.result.modules[module_name] = module_result

        # 更新总体结果
        self.result.tests_run += module_result['tests_run']
        self.result.failures += module_result['failures']
        self.result.errors += module_result['errors']
        self.result.skipped += module_result['skipped']

        return module_result['success']

    def run_all_tests(self):
        """运行所有测试"""
        print("[START] 开始运行 agno_modular 测试套件")
        print(f"Python 版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")

        self.result.start_time = time.time()

        # 测试文件列表
        test_files = [
            ("AgentSystemConfig 测试", "tests/agno_modular/test_agent_system_config.py"),
            ("Composer 模块测试", "tests/agno_modular/test_composer.py"),
            ("MCP Factory 测试", "tests/agno_modular/test_mcp_factory.py"),
            ("MCP Python 3.8 兼容性测试", "tests/mcp/test_mcp_py38.py"),
            ("MCP 工具导入测试", "tests/mcp/test_mcp_tools_import.py"),
        ]

        success_count = 0
        total_count = len(test_files)

        for test_name, test_file in test_files:
            if os.path.exists(test_file):
                try:
                    if self.run_module_tests(test_name, test_file):
                        success_count += 1
                        print(f"[SUCCESS] {test_name} - 通过")
                    else:
                        print(f"[ERROR] {test_name} - 失败")
                except Exception as e:
                    print(f"[ERROR] {test_name} - 运行异常: {e}")
            else:
                print(f"[WARNING]  {test_name} - 文件不存在: {test_file}")

        self.result.end_time = time.time()
        self.result.duration = self.result.end_time - self.result.start_time

        # 计算成功率
        if self.result.tests_run > 0:
            successful_tests = self.result.tests_run - self.result.failures - self.result.errors
            self.result.success_rate = (successful_tests / self.result.tests_run) * 100

        return self.print_summary(success_count, total_count)

    def print_summary(self, success_count, total_count):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("[SUMMARY] 测试总结")
        print(f"{'='*60}")

        print(f"模块成功率: {success_count}/{total_count} ({(success_count/total_count)*100:.1f}%)")
        print(f"总测试数: {self.result.tests_run}")
        print(f"成功: {self.result.tests_run - self.result.failures - self.result.errors}")
        print(f"失败: {self.result.failures}")
        print(f"错误: {self.result.errors}")
        print(f"跳过: {self.result.skipped}")
        print(f"成功率: {self.result.success_rate:.1f}%")
        print(f"总耗时: {self.result.duration:.2f} 秒")

        # 模块详情
        print(f"\n[DETAILS] 模块详情:")
        for module_name, module_result in self.result.modules.items():
            status = "[SUCCESS] 通过" if module_result['success'] else "[ERROR] 失败"
            print(f"  {module_name}: {status} "
                  f"({module_result['tests_run']} 测试, "
                  f"{module_result['duration']:.2f}s)")

        # 整体状态
        if self.result.failures == 0 and self.result.errors == 0:
            print(f"\n[ALL_PASS] 所有测试通过！")
            return True
        else:
            print(f"\n[WARNING]  存在失败的测试")
            return False


def run_specific_test(test_pattern):
    """运行特定的测试模式"""
    print(f"[SEARCH] 运行匹配模式: {test_pattern}")

    # 这里可以添加特定测试的逻辑
    if test_pattern == "mcp":
        # 只运行 MCP 相关测试
        test_files = [
            ("MCP Python 3.8 兼容性测试", "tests/mcp/test_mcp_py38.py"),
            ("MCP 工具导入测试", "tests/mcp/test_mcp_tools_import.py"),
        ]
    elif test_pattern == "agno_modular":
        # 只运行 agno_modular 相关测试
        test_files = [
            ("AgentSystemConfig 测试", "tests/agno_modular/test_agent_system_config.py"),
            ("Composer 模块测试", "tests/agno_modular/test_composer.py"),
            ("MCP Factory 测试", "tests/agno_modular/test_mcp_factory.py"),
        ]
    else:
        print(f"[ERROR] 未知的测试模式: {test_pattern}")
        print("可用模式: 'mcp', 'agno_modular', 'all'")
        return False

    runner = TestRunner()
    success_count = 0

    for test_name, test_file in test_files:
        if os.path.exists(test_file):
            try:
                if runner.run_module_tests(test_name, test_file):
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] {test_name} 运行异常: {e}")
        else:
            print(f"[WARNING]  {test_name} 文件不存在: {test_file}")

    return runner.print_summary(success_count, len(test_files))


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="运行 agno_modular 测试套件")
    parser.add_argument(
        "--pattern", "-p",
        choices=["all", "mcp", "agno_modular"],
        default="all",
        help="选择要运行的测试模式"
    )

    args = parser.parse_args()

    if args.pattern == "all":
        runner = TestRunner()
        return runner.run_all_tests()
    else:
        return run_specific_test(args.pattern)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING]  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 测试运行器异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)