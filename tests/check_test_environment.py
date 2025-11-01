#!/usr/bin/env python3
"""
检查 ChatEngine 测试环境配置
验证所有必要的依赖和模块是否可用
"""

import sys
import os
sys.path.insert(0, r"D:\Workspace\LeafKnow")
import importlib

def check_python_version():
    """检查 Python 版本"""
    print("检查 Python 版本...")
    version = sys.version_info
    print(f"  当前版本: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("  ✅ Python 版本符合要求 (>= 3.8)")
        return True
    else:
        print("  ❌ Python 版本过低，需要 3.8 或更高版本")
        return False

def check_project_structure():
    """检查项目结构"""
    print("\n检查项目结构...")

    required_files = [
        "chat_engine.py",
        "core/",
        "core/agno/",
        "core/agno/db/",
        "core/agno/db/sqlite/",
        "tests/"
    ]

    required_modules = [
        "core.agno.db.sqlite.extended_sqlite",
        "core.agno.db.sqlite.config_data",
        "core.agno.db.sqlite.runtime_data",
        "core.agno.db.sqlite.schemas"
    ]

    # 检查文件结构
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - 不存在")
            all_files_exist = False

    # 检查模块导入
    print("\n检查核心模块导入...")
    all_modules_import = True
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name} - 导入失败: {e}")
            all_modules_import = False

    return all_files_exist and all_modules_import

def check_test_files():
    """检查测试文件"""
    print("\n检查测试文件...")

    test_files = [
        "tests/test_chat_engine.py",
        "tests/test_chat_engine_config.py",
        "tests/run_chat_engine_tests.py",
        "tests/demo_config_test.py"
    ]

    all_files_exist = True
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  ✅ {test_file}")
        else:
            print(f"  ❌ {test_file} - 不存在")
            all_files_exist = False

    return all_files_exist

def check_dependencies():
    """检查依赖项"""
    print("\n检查依赖项...")

    # 标准库模块
    std_lib_modules = [
        "unittest",
        "json",
        "tempfile",
        "shutil",
        "os",
        "sys",
        "time",
        "uuid",
        "pathlib",
        "threading",
        "asyncio",
        "concurrent.futures",
        "unittest.mock"
    ]

    all_std_lib_available = True
    print("  标准库模块:")
    for module_name in std_lib_modules:
        try:
            importlib.import_module(module_name)
            print(f"    ✅ {module_name}")
        except ImportError as e:
            print(f"    ❌ {module_name} - 导入失败: {e}")
            all_std_lib_available = False

    return all_std_lib_available

def check_chat_engine_import():
    """检查 ChatEngine 导入"""
    print("\n检查 ChatEngine 导入...")

    try:
        # 添加项目路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from chat_engine import ChatEngine
        print("  ✅ ChatEngine 导入成功")

        # 检查主要方法
        required_methods = [
            "__init__",
            "load_config",
            "save_config",
            "create_agent",
            "select_agent_by_name",
            "process_message",
            "get_agent_statistics",
            "add_knowledge",
            "add_memory",
            "add_evaluation"
        ]

        all_methods_exist = True
        print("  检查主要方法:")
        for method_name in required_methods:
            if hasattr(ChatEngine, method_name):
                print(f"    ✅ {method_name}")
            else:
                print(f"    ❌ {method_name} - 方法不存在")
                all_methods_exist = False

        return all_methods_exist

    except ImportError as e:
        print(f"  ❌ ChatEngine 导入失败: {e}")
        return False

def check_database_access():
    """检查数据库访问"""
    print("\n检查数据库访问...")

    try:
        import tempfile
        import sqlite3

        # 创建临时数据库测试
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name

        try:
            # 测试 SQLite 连接
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()

            # 创建测试表
            cursor.execute("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at INTEGER
                )
            """)

            # 插入测试数据
            cursor.execute(
                "INSERT INTO test_table (id, name, created_at) VALUES (?, ?, ?)",
                ("test_001", "test_name", 1234567890)
            )

            # 查询测试数据
            cursor.execute("SELECT * FROM test_table WHERE id = ?", ("test_001",))
            result = cursor.fetchone()

            conn.commit()
            conn.close()

            if result and result[1] == "test_name":
                print("  ✅ SQLite 数据库访问正常")
                return True
            else:
                print("  ❌ 数据库操作验证失败")
                return False

        finally:
            # 清理临时文件
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    except Exception as e:
        print(f"  ❌ 数据库访问测试失败: {e}")
        return False

def check_permissions():
    """检查文件权限"""
    print("\n检查文件权限...")

    try:
        import tempfile

        # 测试临时目录创建
        temp_dir = tempfile.mkdtemp()
        print(f"  ✅ 临时目录创建: {temp_dir}")

        # 测试文件创建
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        print(f"  ✅ 文件创建: {test_file}")

        # 测试文件读取
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"  ✅ 文件读取: 内容长度 {len(content)}")

        # 测试文件删除
        os.unlink(test_file)
        os.rmdir(temp_dir)
        print("  ✅ 文件和目录删除成功")

        return True

    except Exception as e:
        print(f"  ❌ 权限检查失败: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 70)
    print("ChatEngine 测试环境检查")
    print("=" * 70)

    checks = [
        ("Python 版本", check_python_version),
        ("项目结构", check_project_structure),
        ("测试文件", check_test_files),
        ("依赖项", check_dependencies),
        ("ChatEngine 导入", check_chat_engine_import),
        ("数据库访问", check_database_access),
        ("文件权限", check_permissions)
    ]

    results = []

    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ❌ {check_name} 检查时出错: {e}")
            results.append((check_name, False))

    # 显示总结
    print("\n" + "=" * 70)
    print("检查结果总结")
    print("=" * 70)

    passed_checks = 0
    total_checks = len(results)

    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{check_name:20} {status}")
        if result:
            passed_checks += 1

    print(f"\n总体结果: {passed_checks}/{total_checks} 项检查通过")

    if passed_checks == total_checks:
        print("🎉 测试环境配置完美！可以运行所有测试。")
        return 0
    else:
        print("⚠️  测试环境存在问题，请修复失败的检查项后再运行测试。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)