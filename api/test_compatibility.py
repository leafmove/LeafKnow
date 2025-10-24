#!/usr/bin/env python3
"""
Python版本兼容性测试脚本
用于验证当前Python环境是否满足项目依赖要求
"""

import sys
import subprocess
from typing import List, Tuple

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major != 3:
        print("需要Python 3.x")
        return False

    if version.minor < 10:
        print("需要Python 3.10或更高版本")
        return False

    print(f"Python版本符合要求 (>=3.10)")
    return True

def check_required_packages() -> List[Tuple[str, bool]]:
    """检查必需的包是否可以导入"""
    required_packages = [
        ("fastapi", "fastapi"),
        ("sqlmodel", "sqlmodel"),
        ("uvicorn", "uvicorn"),
        ("tiktoken", "tiktoken"),
        ("pydantic_ai", "pydantic_ai"),
        ("lancedb", "lancedb")
    ]

    results = []
    print("\n检查必需包的可导入性:")

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"[OK] {package_name}: 可导入")
            results.append((package_name, True))
        except ImportError as e:
            print(f"[FAIL] {package_name}: 导入失败 - {e}")
            results.append((package_name, False))

    return results

def check_uv_sync():
    """尝试运行uv sync来测试依赖安装"""
    print("\n尝试运行uv sync...")
    try:
        result = subprocess.run(
            ["uv", "sync", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("[OK] uv sync dry-run 成功")
            return True
        else:
            print(f"[FAIL] uv sync dry-run 失败:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("[FAIL] uv sync 超时")
        return False
    except FileNotFoundError:
        print("[FAIL] uv 未安装")
        return False

def main():
    """主测试函数"""
    print("LeafKnow API Python兼容性测试")
    print("=" * 50)

    # 检查Python版本
    python_ok = check_python_version()

    if not python_ok:
        print("\n[FAIL] Python版本不符合要求，请升级到Python 3.10+")
        sys.exit(1)

    # 检查包导入
    package_results = check_required_packages()
    failed_packages = [pkg for pkg, ok in package_results if not ok]

    # 检查uv同步
    uv_ok = check_uv_sync()

    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"Python版本: 符合要求")
    print(f"包导入: {len(package_results) - len(failed_packages)}/{len(package_results)} 成功")

    if failed_packages:
        print(f"失败的包: {', '.join(failed_packages)}")
        print("建议: 运行 'uv sync' 安装缺失的依赖")

    if uv_ok:
        print("依赖安装: 可以正常同步")
    else:
        print("依赖安装: 可能有问题")

    if failed_packages or not uv_ok:
        print("\n建议操作:")
        print("1. 运行 'uv sync' 安装所有依赖")
        print("2. 如果仍有问题，检查网络连接和Python环境")
        print("3. 考虑使用虚拟环境隔离依赖")
    else:
        print("\n环境配置完成，可以启动API服务！")

if __name__ == "__main__":
    main()