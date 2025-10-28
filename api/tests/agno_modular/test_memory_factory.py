"""
Memory工厂模块单元测试
测试记忆管理器配置和创建功能
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加路径以导入agno_modular模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agno_modular'))

from memory_factory import (
    MemoryConfig,
    create_memory_manager,
    create_conversation_memory,
    create_personal_memory,
    create_task_memory,
    create_learning_memory,
    create_preference_memory,
    create_context_memory,
    create_multi_memory_system
)


class TestMemoryConfig(unittest.TestCase):
    """测试MemoryConfig配置类"""

    def test_default_initialization(self):
        """测试默认初始化"""
        config = MemoryConfig()

        self.assertIsNone(config.model)
        self.assertIsNone(config.system_message)
        self.assertIsNone(config.memory_capture_instructions)
        self.assertIsNone(config.additional_instructions)
        self.assertIsNone(config.db)
        self.assertFalse(config.delete_memories)
        self.assertTrue(config.update_memories)
        self.assertTrue(config.add_memories)
        self.assertFalse(config.clear_memories)
        self.assertEqual(config.retrieval_method, "last_n")
        self.assertEqual(config.retrieval_limit, 10)
        self.assertFalse(config.debug_mode)
        self.assertTrue(config.auto_create)

    def test_custom_initialization(self):
        """测试自定义初始化"""
        mock_model = Mock()
        mock_db = Mock()

        config = MemoryConfig(
            model=mock_model,
            system_message="Test system message",
            memory_capture_instructions="Test capture instructions",
            db=mock_db,
            delete_memories=True,
            update_memories=False,
            add_memories=False,
            retrieval_method="semantic",
            retrieval_limit=20,
            debug_mode=True,
            auto_create=False
        )

        self.assertEqual(config.model, mock_model)
        self.assertEqual(config.system_message, "Test system message")
        self.assertEqual(config.memory_capture_instructions, "Test capture instructions")
        self.assertEqual(config.db, mock_db)
        self.assertTrue(config.delete_memories)
        self.assertFalse(config.update_memories)
        self.assertFalse(config.add_memories)
        self.assertEqual(config.retrieval_method, "semantic")
        self.assertEqual(config.retrieval_limit, 20)
        self.assertTrue(config.debug_mode)
        self.assertFalse(config.auto_create)

    def test_field_types(self):
        """测试字段类型"""
        config = MemoryConfig()

        # 测试布尔字段
        self.assertIsInstance(config.delete_memories, bool)
        self.assertIsInstance(config.update_memories, bool)
        self.assertIsInstance(config.add_memories, bool)
        self.assertIsInstance(config.clear_memories, bool)
        self.assertIsInstance(config.debug_mode, bool)
        self.assertIsInstance(config.auto_create, bool)

        # 测试字符串字段
        self.assertIsInstance(config.retrieval_method, str)

        # 测试数字字段
        self.assertIsInstance(config.retrieval_limit, int)

    def test_retrieval_configuration(self):
        """测试检索配置"""
        # 测试默认检索配置
        config = MemoryConfig()
        self.assertEqual(config.retrieval_method, "last_n")
        self.assertEqual(config.retrieval_limit, 10)

        # 测试自定义检索配置
        config = MemoryConfig(
            retrieval_method="similarity",
            retrieval_limit=50
        )
        self.assertEqual(config.retrieval_method, "similarity")
        self.assertEqual(config.retrieval_limit, 50)


class TestCreateMemoryManager(unittest.TestCase):
    """测试create_memory_manager函数"""

    @patch('memory_factory.MemoryManager')
    def test_create_basic_memory_manager(self, mock_memory_manager_class):
        """测试创建基本记忆管理器"""
        mock_memory_manager = Mock()
        mock_memory_manager_class.return_value = mock_memory_manager

        config = MemoryConfig()

        result = create_memory_manager(config)

        # 验证MemoryManager被正确调用
        mock_memory_manager_class.assert_called_once_with(
            model=None,
            system_message=None,
            memory_capture_instructions=None,
            additional_instructions=None,
            db=None,
            delete_memories=False,
            update_memories=True,
            add_memories=True,
            clear_memories=False,
            debug_mode=False,
        )

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.MemoryManager')
    def test_create_memory_manager_with_all_parameters(self, mock_memory_manager_class):
        """测试使用所有参数创建记忆管理器"""
        mock_memory_manager = Mock()
        mock_memory_manager_class.return_value = mock_memory_manager
        mock_model = Mock()
        mock_db = Mock()

        config = MemoryConfig(
            model=mock_model,
            system_message="Test system message",
            memory_capture_instructions="Test capture instructions",
            additional_instructions="Test additional instructions",
            db=mock_db,
            delete_memories=True,
            update_memories=False,
            add_memories=True,
            clear_memories=False,
            debug_mode=True
        )

        result = create_memory_manager(config)

        # 验证所有参数被正确传递
        mock_memory_manager_class.assert_called_once_with(
            model=mock_model,
            system_message="Test system message",
            memory_capture_instructions="Test capture instructions",
            additional_instructions="Test additional instructions",
            db=mock_db,
            delete_memories=True,
            update_memories=False,
            add_memories=True,
            clear_memories=False,
            debug_mode=True,
        )

        self.assertEqual(result, mock_memory_manager)


class TestSpecializedMemoryManagers(unittest.TestCase):
    """测试专用记忆管理器创建函数"""

    @patch('memory_factory.create_memory_manager')
    def test_create_conversation_memory(self, mock_create_manager):
        """测试创建对话记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()
        mock_db = Mock()

        result = create_conversation_memory(mock_model, mock_db)

        # 验证create_memory_manager被调用
        mock_create_manager.assert_called_once()
        config = mock_create_manager.call_args[0][0]

        self.assertEqual(config.model, mock_model)
        self.assertEqual(config.db, mock_db)
        self.assertIn("对话中的重要信息", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_conversation_memory_with_kwargs(self, mock_create_manager):
        """测试使用kwargs创建对话记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_conversation_memory(
            mock_model,
            debug_mode=True,
            retrieval_limit=20
        )

        # 验证额外参数被传递
        config = mock_create_manager.call_args[0][0]
        self.assertTrue(config.debug_mode)
        self.assertEqual(config.retrieval_limit, 20)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_personal_memory(self, mock_create_manager):
        """测试创建个人信息记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_personal_memory(mock_model)

        # 验证配置
        config = mock_create_manager.call_args[0][0]
        self.assertEqual(config.model, mock_model)
        self.assertIn("个人信息管理助手", config.system_message)
        self.assertIn("基本信息：姓名、年龄、职业", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_task_memory(self, mock_create_manager):
        """测试创建任务记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_task_memory(mock_model)

        # 验证配置
        config = mock_create_manager.call_args[0][0]
        self.assertEqual(config.model, mock_model)
        self.assertIn("任务管理助手", config.system_message)
        self.assertIn("任务的描述和要求", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_learning_memory(self, mock_create_manager):
        """测试创建学习记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_learning_memory(mock_model)

        # 验证配置
        config = mock_create_manager.call_args[0][0]
        self.assertEqual(config.model, mock_model)
        self.assertIn("学习管理助手", config.system_message)
        self.assertIn("学习的内容和主题", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_preference_memory(self, mock_create_manager):
        """测试创建偏好记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_preference_memory(mock_model)

        # 验证配置
        config = mock_create_manager.call_args[0][0]
        self.assertEqual(config.model, mock_model)
        self.assertIn("偏好管理助手", config.system_message)
        self.assertIn("沟通风格偏好", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_create_context_memory(self, mock_create_manager):
        """测试创建上下文记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_context_memory(mock_model)

        # 验证配置
        config = mock_create_manager.call_args[0][0]
        self.assertEqual(config.model, mock_model)
        self.assertIn("上下文管理助手", config.system_message)
        self.assertIn("对话的主题和背景", config.memory_capture_instructions)

        self.assertEqual(result, mock_memory_manager)


class TestCreateMultiMemorySystem(unittest.TestCase):
    """测试创建多记忆系统"""

    @patch('memory_factory.create_conversation_memory')
    @patch('memory_factory.create_personal_memory')
    @patch('memory_factory.create_task_memory')
    def test_create_multi_memory_system_default(self, mock_task, mock_personal, mock_conversation):
        """测试创建默认多记忆系统"""
        mock_conversation.return_value = Mock()
        mock_personal.return_value = Mock()
        mock_task.return_value = Mock()
        mock_model = Mock()

        result = create_multi_memory_system(mock_model)

        # 验证默认记忆类型被创建
        mock_conversation.assert_called_once()
        mock_personal.assert_called_once()
        mock_task.assert_called_once()

        # 验证返回的记忆系统（默认包含4个类型）
        self.assertIn("conversation", result)
        self.assertIn("personal", result)
        self.assertIn("task", result)
        self.assertIn("preference", result)  # 默认还包含preference
        self.assertEqual(len(result), 4)

    @patch('memory_factory.create_memory_manager')
    def test_create_multi_memory_system_custom_types(self, mock_create_manager):
        """测试创建自定义记忆类型的多记忆系统"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        custom_types = ["conversation", "task", "learning", "preference"]
        result = create_multi_memory_system(
            mock_model,
            memory_types=custom_types
        )

        # 验证create_memory_manager被调用4次
        self.assertEqual(mock_create_manager.call_count, 4)

        # 验证返回的记忆系统包含所有请求的类型
        for memory_type in custom_types:
            self.assertIn(memory_type, result)

        self.assertEqual(len(result), 4)

    @patch('memory_factory.create_memory_manager')
    def test_create_multi_memory_system_with_db(self, mock_create_manager):
        """测试带有数据库的多记忆系统"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()
        mock_db = Mock()

        result = create_multi_memory_system(
            mock_model,
            db=mock_db,
            memory_types=["conversation", "personal"]
        )

        # 验证每个记忆管理器都使用相同的数据库
        self.assertEqual(mock_create_manager.call_count, 2)
        for call in mock_create_manager.call_args_list:
            config = call[0][0]
            self.assertEqual(config.model, mock_model)
            self.assertEqual(config.db, mock_db)

        self.assertEqual(len(result), 2)

    @patch('memory_factory.create_memory_manager')
    def test_create_multi_memory_system_with_kwargs(self, mock_create_manager):
        """测试使用kwargs的多记忆系统"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        result = create_multi_memory_system(
            mock_model,
            memory_types=["conversation"],
            debug_mode=True,
            retrieval_limit=30
        )

        # 验证kwargs被传递给记忆管理器
        config = mock_create_manager.call_args[0][0]
        self.assertTrue(config.debug_mode)
        self.assertEqual(config.retrieval_limit, 30)

        self.assertEqual(len(result), 1)

    def test_create_multi_memory_system_empty_types(self):
        """测试空记忆类型列表"""
        mock_model = Mock()

        result = create_multi_memory_system(
            mock_model,
            memory_types=[]
        )

        # 应该返回空字典
        self.assertEqual(result, {})

    @patch('memory_factory.create_memory_manager')
    def test_create_multi_memory_system_unknown_type(self, mock_create_manager):
        """测试包含未知记忆类型的多记忆系统"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        # 包含一个未知的记忆类型
        result = create_multi_memory_system(
            mock_model,
            memory_types=["conversation", "unknown_type"]
        )

        # 只有已知类型应该被创建
        self.assertEqual(mock_create_manager.call_count, 1)
        self.assertIn("conversation", result)
        self.assertNotIn("unknown_type", result)
        self.assertEqual(len(result), 1)


class TestMemoryEdgeCases(unittest.TestCase):
    """测试记忆管理器的边界情况"""

    @patch('memory_factory.MemoryManager')
    def test_memory_config_without_model(self, mock_memory_manager_class):
        """测试没有模型的记忆配置"""
        mock_memory_manager = Mock()
        mock_memory_manager_class.return_value = mock_memory_manager

        config = MemoryConfig()  # 没有设置model
        result = create_memory_manager(config)

        # 验证即使没有模型，记忆管理器也能创建
        mock_memory_manager_class.assert_called_once()
        self.assertEqual(result, mock_memory_manager)

    @patch('memory_factory.create_memory_manager')
    def test_specialized_memory_without_db(self, mock_create_manager):
        """测试没有数据库的专用记忆管理器"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        # 测试所有专用记忆管理器都能在没有数据库的情况下创建
        managers = [
            create_conversation_memory(mock_model),
            create_personal_memory(mock_model),
            create_task_memory(mock_model),
            create_learning_memory(mock_model),
            create_preference_memory(mock_model),
            create_context_memory(mock_model)
        ]

        # 验证所有管理器都创建成功
        for manager in managers:
            self.assertEqual(manager, mock_memory_manager)

        self.assertEqual(mock_create_manager.call_count, 6)

    @patch('memory_factory.MemoryManager')
    def test_memory_with_extreme_retrieval_limit(self, mock_memory_manager_class):
        """测试极端检索限制的记忆管理器"""
        mock_memory_manager = Mock()
        mock_memory_manager_class.return_value = mock_memory_manager

        # 测试极大和极小的检索限制
        configs = [
            MemoryConfig(retrieval_limit=1),
            MemoryConfig(retrieval_limit=1000),
            MemoryConfig(retrieval_limit=0)
        ]

        for config in configs:
            create_memory_manager(config)

        # 验证所有配置都能创建记忆管理器
        self.assertEqual(mock_memory_manager_class.call_count, 3)

    def test_memory_config_all_boolean_combinations(self):
        """测试所有布尔参数组合"""
        boolean_fields = [
            'delete_memories',
            'update_memories',
            'add_memories',
            'clear_memories',
            'debug_mode',
            'auto_create'
        ]

        # 测试一些布尔组合
        combinations = [
            {field: True for field in boolean_fields},
            {field: False for field in boolean_fields},
            {field: i % 2 == 0 for i, field in enumerate(boolean_fields)}
        ]

        for combination in combinations:
            config = MemoryConfig(**combination)

            # 验证配置能正确创建
            for field, expected_value in combination.items():
                self.assertEqual(getattr(config, field), expected_value)


class TestMemoryInstructionsContent(unittest.TestCase):
    """测试记忆指令内容"""

    @patch('memory_factory.create_memory_manager')
    def test_conversation_memory_instructions_content(self, mock_create_manager):
        """测试对话记忆指令内容"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        create_conversation_memory(mock_model)

        config = mock_create_manager.call_args[0][0]
        instructions = config.memory_capture_instructions

        # 验证指令包含预期的内容
        expected_keywords = [
            "个人信息",
            "重要的事实和事件",
            "用户的观点和偏好",
            "对话中的重要上下文",
            "用户的需求和目标"
        ]

        for keyword in expected_keywords:
            self.assertIn(keyword, instructions)

    @patch('memory_factory.create_memory_manager')
    def test_personal_memory_instructions_content(self, mock_create_manager):
        """测试个人信息记忆指令内容"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        create_personal_memory(mock_model)

        config = mock_create_manager.call_args[0][0]
        instructions = config.memory_capture_instructions

        # 验证指令包含个人信息相关内容
        expected_keywords = [
            "基本信息",
            "兴趣爱好",
            "偏好",
            "习惯",
            "关系",
            "重要生活事件",
            "健康信息",
            "财务偏好"
        ]

        for keyword in expected_keywords:
            self.assertIn(keyword, instructions)

    @patch('memory_factory.create_memory_manager')
    def test_task_memory_instructions_content(self, mock_create_manager):
        """测试任务记忆指令内容"""
        mock_memory_manager = Mock()
        mock_create_manager.return_value = mock_memory_manager
        mock_model = Mock()

        create_task_memory(mock_model)

        config = mock_create_manager.call_args[0][0]
        instructions = config.memory_capture_instructions

        # 验证指令包含任务相关内容
        expected_keywords = [
            "任务的描述和要求",
            "任务的进度和状态",
            "遇到的问题和解决方案",
            "任务的截止日期和优先级",
            "任务的相关资源和工具",
            "任务的成果和反馈"
        ]

        for keyword in expected_keywords:
            self.assertIn(keyword, instructions)


if __name__ == '__main__':
    unittest.main()