"""
记忆管理工厂模块
用于创建和配置不同类型的记忆管理器
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

from agno.memory.manager import MemoryManager
from agno.models.base import Model
from agno.db.base import BaseDb, AsyncBaseDb
from agno.db.schemas import UserMemory


@dataclass
class MemoryConfig:
    """记忆管理配置类"""

    # 模型配置
    model: Optional[Model] = None

    # 系统配置
    system_message: Optional[str] = None
    memory_capture_instructions: Optional[str] = None
    additional_instructions: Optional[str] = None

    # 数据库配置
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None

    # 操作权限配置
    delete_memories: bool = False
    update_memories: bool = True
    add_memories: bool = True
    clear_memories: bool = False

    # 检索配置
    retrieval_method: str = "last_n"
    retrieval_limit: int = 10

    # 其他配置
    debug_mode: bool = False
    auto_create: bool = True


def create_memory_manager(config: MemoryConfig) -> MemoryManager:
    """
    创建记忆管理器

    Args:
        config: 记忆管理配置

    Returns:
        配置好的MemoryManager实例
    """

    memory_manager = MemoryManager(
        model=config.model,
        system_message=config.system_message,
        memory_capture_instructions=config.memory_capture_instructions,
        additional_instructions=config.additional_instructions,
        db=config.db,
        delete_memories=config.delete_memories,
        update_memories=config.update_memories,
        add_memories=config.add_memories,
        clear_memories=config.clear_memories,
        debug_mode=config.debug_mode,
    )

    return memory_manager


def create_conversation_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建对话记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        对话记忆管理器
    """

    memory_capture_instructions = """
    记忆应该捕获对话中的重要信息，包括：
    - 用户的个人信息：姓名、职业、兴趣、偏好等
    - 重要的事实和事件
    - 用户的观点和偏好
    - 对话中的重要上下文
    - 用户的需求和目标
    - 其他对对话有帮助的信息
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        **kwargs
    )

    return create_memory_manager(config)


def create_personal_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建个人信息记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        个人信息记忆管理器
    """

    memory_capture_instructions = """
    记忆应该专注于用户的个人信息，包括：
    - 基本信息：姓名、年龄、职业、位置等
    - 兴趣爱好：喜欢的活动、运动、音乐等
    - 偏好：喜欢和不喜欢的事物
    - 习惯：日常习惯、工作习惯等
    - 关系：家人、朋友、同事等重要关系
    - 重要生活事件：工作变动、搬家、重要成就等
    - 健康信息：过敏、健康问题、锻炼习惯等
    - 财务偏好：消费习惯、理财方式等
    """

    system_message = """你是一个个人信息管理助手，专门负责记录和管理用户的个人信息。

    请仔细分析对话内容，识别和提取用户的个人信息，并确保：
    1. 只记录真实的个人信息
    2. 保持信息的准确性和时效性
    3. 尊重用户隐私，不记录敏感信息
    4. 及时更新变化的信息
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        system_message=system_message,
        **kwargs
    )

    return create_memory_manager(config)


def create_task_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建任务记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        任务记忆管理器
    """

    memory_capture_instructions = """
    记忆应该专注于任务相关信息，包括：
    - 任务的描述和要求
    - 任务的进度和状态
    - 遇到的问题和解决方案
    - 任务的截止日期和优先级
    - 任务的相关资源和工具
    - 任务的成果和反馈
    - 用户的任务偏好和习惯
    """

    system_message = """你是一个任务管理助手，专门负责记录和管理用户的任务信息。

    请关注任务相关的信息，确保：
    1. 准确记录任务的具体要求
    2. 跟踪任务的进展状态
    3. 记录重要的决策和变更
    4. 提供有用的任务管理建议
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        system_message=system_message,
        **kwargs
    )

    return create_memory_manager(config)


def create_learning_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建学习记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        学习记忆管理器
    """

    memory_capture_instructions = """
    记忆应该专注于学习相关信息，包括：
    - 学习的内容和主题
    - 学习的进度和掌握程度
    - 学习的方法和策略
    - 遇到的困难和理解难点
    - 学习资源和参考材料
    - 重要的知识点和概念
    - 学习心得和体会
    - 学习目标和计划
    """

    system_message = """你是一个学习管理助手，专门负责记录和管理用户的学习信息。

    请关注学习过程中的重要信息，确保：
    1. 准确记录学习内容和进度
    2. 识别学习中的难点和重点
    3. 提供有效的学习建议
    4. 跟踪学习成果和改进
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        system_message=system_message,
        **kwargs
    )

    return create_memory_manager(config)


def create_preference_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建偏好记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        偏好记忆管理器
    """

    memory_capture_instructions = """
    记忆应该专注于用户偏好信息，包括：
    - 沟通风格偏好：正式/非正式、简洁/详细等
    - 内容偏好：感兴趣的话题、不喜欢的话题
    - 交互偏好：回答长度、是否使用表情符号等
    - 视觉偏好：颜色、布局、风格等
    - 工作偏好：工作方式、环境偏好等
    - 消费偏好：品牌偏好、价格敏感度等
    - 娱乐偏好：电影类型、音乐风格、游戏类型等
    - 社交偏好：社交场合偏好、沟通方式偏好等
    """

    system_message = """你是一个偏好管理助手，专门负责记录和管理用户的偏好信息。

    请仔细观察和分析用户的偏好，确保：
    1. 准确识别用户的偏好模式
    2. 理解偏好的原因和背景
    3. 根据偏好调整交互方式
    4. 注意偏好的变化和发展
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        system_message=system_message,
        **kwargs
    )

    return create_memory_manager(config)


def create_context_memory(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    **kwargs
) -> MemoryManager:
    """
    创建上下文记忆管理器

    Args:
        model: AI模型
        db: 数据库
        **kwargs: 其他配置

    Returns:
        上下文记忆管理器
    """

    memory_capture_instructions = """
    记忆应该专注于对话上下文信息，包括：
    - 对话的主题和背景
    - 之前讨论的内容和结论
    - 当前对话的目标和意图
    - 相关的环境信息
    - 时间和时序信息
    - 涉及的人物和关系
    - 重要的转折点和决策
    - 未解决的问题和待办事项
    """

    system_message = """你是一个上下文管理助手，专门负责记录和管理对话的上下文信息。

    请维护对话的连贯性和一致性，确保：
    1. 准确理解对话的背景和上下文
    2. 保持对话的逻辑连贯性
    3. 识别重要的上下文变化
    4. 提供相关的历史信息
    """

    config = MemoryConfig(
        model=model,
        db=db,
        memory_capture_instructions=memory_capture_instructions,
        system_message=system_message,
        **kwargs
    )

    return create_memory_manager(config)


def create_multi_memory_system(
    model: Model,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
    memory_types: List[str] = None,
    **kwargs
) -> Dict[str, MemoryManager]:
    """
    创建多记忆系统

    Args:
        model: AI模型
        db: 数据库
        memory_types: 记忆类型列表
        **kwargs: 其他配置

    Returns:
        多个记忆管理器的字典
    """

    if memory_types is None:
        memory_types = ["conversation", "personal", "task", "preference"]

    memory_creators = {
        "conversation": create_conversation_memory,
        "personal": create_personal_memory,
        "task": create_task_memory,
        "learning": create_learning_memory,
        "preference": create_preference_memory,
        "context": create_context_memory,
    }

    memory_system = {}
    for memory_type in memory_types:
        if memory_type in memory_creators:
            memory_system[memory_type] = memory_creators[memory_type](
                model=model,
                db=db,
                **kwargs
            )

    return memory_system