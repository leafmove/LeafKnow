from sqlmodel import (
    Field, 
    SQLModel, 
    create_engine, 
    Session, 
    select, 
    inspect, 
    text, 
    # asc, 
    # and_, 
    # or_, 
    # desc, 
    # not_,
    Column,
    Enum,
    JSON,
)
from sqlalchemy import Engine
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Dict, Any, Union, Optional
import os
from core.config import BUILTMODELS
    
# 任务状态枚举
class TaskStatus(str, PyEnum):
    RESERVED = "reserved"  # 预留/占位状态，等待数据填充
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"  # 添加取消状态

# 任务结果状态
class TaskResult(str, PyEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

# 3种任务优先级
class TaskPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# 任务类型
class TaskType(str, PyEnum):
    SCREENING = "screening"
    TAGGING = "tagging"
    MULTIVECTOR = "multivector"
    # REFINE = "refine"
    # MAINTENANCE = "maintenance"

# 供worker使用的tasks表
class Task(SQLModel, table=True):
    __tablename__ = "t_tasks"
    id: int = Field(default=None, primary_key=True)
    task_name: str
    task_type: str = Field(sa_column=Column(Enum(TaskType, values_callable=lambda obj: [e.value for e in obj]), default=TaskType.TAGGING.value))
    priority: str = Field(sa_column=Column(Enum(TaskPriority, values_callable=lambda obj: [e.value for e in obj]), default=TaskPriority.MEDIUM.value))
    status: str = Field(sa_column=Column(Enum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]), default=TaskStatus.PENDING.value))
    created_at: datetime = Field(default=datetime.now())  # 创建时间
    updated_at: datetime = Field(default=datetime.now())  # 更新时间
    start_time: Optional[datetime] = Field(default=None)  # 任务开始时间
    result: Optional[str] = Field(sa_column=Column(Enum(TaskResult, values_callable=lambda obj: [e.value for e in obj]), default=None))
    error_message: Optional[str] = Field(default=None)  # 错误信息
    extra_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # 任务额外数据
    target_file_path: Optional[str] = Field(default=None, index=True)  # 目标文件路径，专门用于MULTIVECTOR任务的高效查询
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

# 通知表
class Notification(SQLModel, table=True):
    __tablename__ = "t_notifications"
    id: int = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="t_tasks.id", index=True)  # 关联任务ID
    message: str
    created_at: datetime = Field(default=datetime.now())  # 创建时间
    read: bool = Field(default=False)  # 是否已读
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 监控的文件夹表，用来存储文件夹的路径和状态
class MyFolders(SQLModel, table=True):
    __tablename__ = "t_myfolders"
    id: int = Field(default=None, primary_key=True)
    path: str
    alias: Optional[str] = Field(default=None)  # 别名
    is_blacklist: bool = Field(default=False)  # 是否是用户不想监控的文件夹(黑名单)
    is_common_folder: bool = Field(default=False)  # 是否为常见文件夹（不可删除）
    parent_id: Optional[int] = Field(default=None, foreign_key="t_myfolders.id")  # 父文件夹ID，支持黑名单层级关系
    created_at: datetime = Field(default=datetime.now())  # 创建时间
    updated_at: datetime = Field(default=datetime.now())  # 更新时间
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# macOS Bundle扩展名表
class BundleExtension(SQLModel, table=True):
    __tablename__ = "t_bundle_extensions"
    id: int = Field(default=None, primary_key=True)
    extension: str = Field(index=True, unique=True)  # 扩展名（如.app, .bundle等）
    description: Optional[str] = Field(default=None)  # 描述
    is_active: bool = Field(default=True)  # 是否启用
    is_system_default: bool = Field(default=False)  # 是否为系统默认配置（不可删除/修改）
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 系统配置表
class SystemConfig(SQLModel, table=True):
    __tablename__ = "t_system_config"
    id: int = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)  # 配置键名
    value: str  # 配置值（有可能是JSON字符串）
    description: Optional[str] = Field(default=None)  # 配置描述
    updated_at: datetime = Field(default=datetime.now())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 文件粗筛规则类型枚举
class RuleType(str, PyEnum):
    EXTENSION = "extension"  # 文件扩展名分类
    FILENAME = "filename"    # 文件名模式/关键词识别
    FOLDER = "folder"        # 文件夹路径识别（用于包含/排除特定目录）
    OS_BUNDLE = "os_bundle"  # 操作系统特定的bundle文件夹类型

# 规则优先级
class RulePriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# 规则操作类型
class RuleAction(str, PyEnum):
    INCLUDE = "include"  # 包含在处理中
    EXCLUDE = "exclude"  # 排除在处理外
    LABEL = "label"         # 标记特定类型，但不影响处理流程

# 文件分类表 - 存储不同的文件分类
class FileCategory(SQLModel, table=True):
    __tablename__ = "t_file_categories"
    id: int = Field(default=None, primary_key=True)
    name: str  # 分类名称，如 "document", "image", "audio_video" 等
    description: Optional[str] = Field(default=None)  # 分类描述
    icon: Optional[str] = Field(default=None)  # 可选的图标标识
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 粗筛规则表 - 用于Rust端初步过滤文件
class FileFilterRule(SQLModel, table=True):
    __tablename__ = "t_file_filter_rules"
    id: int = Field(default=None, primary_key=True)
    name: str  # 规则名称
    description: Optional[str] = Field(default=None)  # 规则描述
    rule_type: str = Field(sa_column=Column(Enum(RuleType, values_callable=lambda obj: [e.value for e in obj])))
    category_id: Optional[int] = Field(default=None, foreign_key="t_file_categories.id")  # 关联的文件分类ID
    priority: str = Field(sa_column=Column(Enum(RulePriority, values_callable=lambda obj: [e.value for e in obj]), default=RulePriority.MEDIUM.value))
    action: str = Field(sa_column=Column(Enum(RuleAction, values_callable=lambda obj: [e.value for e in obj]), default=RuleAction.INCLUDE.value))
    enabled: bool = Field(default=True)  # 规则是否启用
    is_system: bool = Field(default=True)  # 是系统规则还是用户自定义规则
    pattern: str  # 匹配模式（正则表达式、通配符或关键词）
    pattern_type: str = Field(default="regex")  # 模式类型：regex, glob, keyword
    extra_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # 额外的配置数据，如嵌套文件结构规则
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 文件扩展名映射表 - 将扩展名映射到文件分类
class FileExtensionMap(SQLModel, table=True):
    __tablename__ = "t_file_extensions"
    id: int = Field(default=None, primary_key=True)
    extension: str  # 不含点的扩展名，如 "pdf", "docx"
    category_id: int = Field(foreign_key="t_file_categories.id")
    description: Optional[str] = Field(default=None)  # 可选描述
    priority: str = Field(sa_column=Column(Enum(RulePriority, values_callable=lambda obj: [e.value for e in obj]), default=RulePriority.MEDIUM.value))
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 标签类型
class TagsType(str, PyEnum):
    SYSTEM = "system" # 系统预定义标签
    USER = "user" # 用户自定义标签
    LLM = "llm" # LLM生成的标签

# 标签表
class Tags(SQLModel, table=True):
    __tablename__ = "t_tags"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)  # 标签名称
    type: str = Field(default=TagsType.USER.value)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 文件粗筛结果状态枚举
class FileScreenResult(str, PyEnum):
    PENDING = "pending"       # 等待进一步处理
    PROCESSED = "processed"   # 已被Python处理
    IGNORED = "ignored"       # 被忽略（符合排除规则）
    FAILED = "failed"         # 处理失败

# 粗筛结果表 - 存储Rust进行初步规则匹配后的结果
class FileScreeningResult(SQLModel, table=True):
    __tablename__ = "t_file_screening_results"
    # 在SQLAlchemy中，__table_args__需要是一个元组，最后一个元素可以是包含选项的字典
    __table_args__ = ({
        "sqlite_autoincrement": True,
        "schema": None,
        "sqlite_with_rowid": True,
    },)
    id: int = Field(default=None, primary_key=True)
    file_path: str            # 文件完整路径
    file_name: str = Field(index=True)  # 文件名（含扩展名），增加索引以优化文件名搜索
    file_size: int            # 文件大小（字节）
    extension: Optional[str] = Field(default=None, index=True)  # 文件扩展名（不含点），增加索引以优化按扩展名过滤
    file_hash: Optional[str] = Field(default=None, index=True)  # 文件哈希值（部分哈希: 大于4k的部分，小于4k则是整个文件），增加索引以优化重复文件查找
    created_time: Optional[datetime] = Field(default=None)  # 文件创建时间
    modified_time: datetime = Field(index=True)  # 文件最后修改时间，增加索引以优化时间范围查询
    accessed_time: Optional[datetime] = Field(default=None)  # 文件最后访问时间
    tagged_time: Optional[datetime] = Field(default=None)  # 上一次打标签时间，用来判定是否需要重新处理

    # 粗筛分类结果
    category_id: Optional[int] = Field(default=None, index=True)  # 根据扩展名或规则确定的分类ID（已有索引）
    matched_rules: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))  # 匹配的规则ID列表

    # 额外元数据和特征
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # 其他元数据信息
    labels: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # 初步标记的标牌
    tags_display_ids: Optional[str] = Field(default=None)  # 标签ID列表（逗号分隔字符串）
    
    # 处理状态
    status: str = Field(
        sa_column=Column(
            Enum(FileScreenResult, values_callable=lambda obj: [e.value for e in obj]), 
            default=FileScreenResult.PENDING.value,
            index=True  # 增加索引以优化状态过滤
        )
    )
    error_message: Optional[str] = Field(default=None)  # 错误信息，如果有

    # 任务关联和时间戳
    task_id: Optional[int] = Field(default=None, index=True)  # 关联的处理任务ID（如果有），增加索引以优化任务关联查询
    created_at: datetime = Field(default=datetime.now())  # 记录创建时间
    updated_at: datetime = Field(default=datetime.now(), index=True)  # 记录更新时间，增加索引以优化按更新时间排序
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 文档表
# 用于记录被处理的原始文件信息。
# 设计意图: 管理最原始的入口文件，file_hash能避免重复处理未变更的文件，status字段则可以支持异步处理和失败重试机制。
class Document(SQLModel, table=True):
    __tablename__ = "t_documents"
    id: int = Field(default=None, primary_key=True)
    file_path: str = Field(index=True, unique=True) # 文件的绝对路径，唯一且索引
    file_hash: str # 文件内容的哈希值，用于检测文件是否变更
    docling_json_path: str # Docling解析后存储的JSON文件路径，便于复用
    status: str = Field(default="pending") # 处理状态: pending, processing, done, error
    processed_at: datetime = Field(default_factory=datetime.now)

# 父块表
# 这是系统的核心实体，代表了我们最终要提供给LLM进行答案合成的“原始内容块”。
# 设计意图: 这是“父文档”策略的直接体现。无论原始形态是文字、图片还是我们后来创造的知识卡片，都在这里有一个统一的表示。通过document_id与源文档关联。
class ParentChunk(SQLModel, table=True):
    __tablename__ = "t_parent_chunks"
    id: int = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="t_documents.id", index=True) # 关联的原始文档
    chunk_type: str = Field(index=True) # 类型: 'text', 'image', 'table', 'knowledge_card'
    # 原始内容或其引用
    content: str # 如果是text/knowledge_card, 直接存内容; 如果是image/table, 存储其图片文件的路径
    metadata_json: str # 存储额外元数据, 如页码、位置坐标等
    created_at: datetime = Field(default_factory=datetime.now)

# 子块表
# 代表了用于向量化和检索的“代理”单元。
# 设计意图: 这是连接关系世界和向量世界的“桥梁”。parent_chunk_id建立了清晰的从属关系，而vector_id则指向了它在LanceDB中的“向量化身”。
class ChildChunk(SQLModel, table=True):
    __tablename__ = "t_child_chunks"
    id: int = Field(default=None, primary_key=True)
    parent_chunk_id: int = Field(foreign_key="t_parent_chunks.id", index=True) # 明确的父子关系
    # 用于向量化的文本内容
    retrieval_content: str # 可能是文本摘要、图片描述、或者“图片描述+周围文本”的组合
    vector_id: str = Field(unique=True, index=True) # 与LanceDB中向量记录对应的唯一ID, 如UUID

# 模型来源
class ModelSourceType(str, PyEnum):
    BUILTIN = "builtin" # App内置框架(MLX/llama-cpp-python)直接运行的模型，直接管理下载过程
    CONFIGURABLE = "configurable" # 可配置的模型服务商，本地如Ollama、LM Studio，远程如OpenAI、Anthropic
    VIP = "vip" # 由本App服务端提供的模型组合
# 模型提供者表
# 这张表用来定义模型的来源。它可以是Ollama，可以是OpenAI，也可以是您自己的VIP服务。
# 设计意图: 将“模型从哪里来”这个问题抽象成一个独立的实体，极大地提高了扩展性。未来出现新的托管平台，只需增加一个新的provider_type即可。
class ModelProvider(SQLModel, table=True):
    __tablename__ = "t_model_providers"
    id: int = Field(default=None, primary_key=True)
    # 显示名称，用户可读的名称
    display_name: str = Field(index=True, unique=True)  # - 预填充名字。- VIP服务从云端拉取。- 用户新增openai-compatible类名称
    source_type: str = Field(default=ModelSourceType.CONFIGURABLE.value)
    provider_type: str = Field(default="")  # 提供者类型，来自agno.models
    base_url: Optional[str] = Field(default=None)  # 如果source_type为vip则此项无效，具体值在每个模型配置上
    api_key: Optional[str] = Field(default=None)  # 如果source_type为vip则为加密后的值(密钥暂时写死，实现用户登录后从云端获取)
    # 存放一些特别的provider-specific数据，比如Azure OpenAI的api_version、VertexAI的project_id/location等
    extra_data_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    is_active: bool = Field(default=False)  # 是否启用
    is_user_added: bool = Field(default=True)  # 用户新增的，用户可以删除
    get_key_url: Optional[str] = Field(default=None)
    support_discovery: bool = Field(default=True)
    use_proxy: bool = Field(default=False)

# 模型能力，前端当作i18n的key
class ModelCapability(str, PyEnum):
    TEXT = "text"
    REASONING = "reasoning"
    VISION = "vision"
    TOOL_USE = "tool_use"
    STRUCTURED_OUTPUT = "structured_output"
    WEB_SEARCH = "web_search"  # Web search capability for finding information online
    EMBEDDING = "embedding"
    RERANKER = "reranker"
    CODE_GENERATION = "code_generation"
    TTS = "tts"
    ASR = "asr"
    IMAGE_GENERATION = "image_generation"
# 模型配置表
# 这张表代表一个具体可用的模型。
# 设计意图: 将一个具体的模型实例（如本地的llama3:8b）与其能力和属性绑定。这些属性可以来自您的云端目录，也可以由用户手动配置。
class ModelConfiguration(SQLModel, table=True):
    __tablename__ = "t_model_configurations"
    id: int = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="t_model_providers.id", index=True) # 关联到提供者
    model_identifier: str # 模型在对应平台官方标识符，如 'gemma:2b', 'gpt-4o'
    display_name: str # 用户可自定义的别名
    # 模型的“能力”清单
    capabilities_json: List[str] = Field(default=[], sa_column=Column(JSON)) # e.g., ['text', 'embedding', 'vision']
    # vip服务的每个模型来自不同的服务商，一定有不同的base_url. 以及model-specific的数据。
    extra_data_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    max_context_length: int = Field(default=0) # This max tokens number includes input, output, and reasoning tokens. 
    max_output_tokens: int = Field(default=0) # This max tokens number includes output tokens only.
    is_enabled: bool = Field(default=False) # 默认不启用

# 能力指派表
# 它将App内的具体“任务”指派给一个配置好的“模型”。
# 设计意图: 彻底解耦“功能”和“实现”。当App需要进行“视觉分析”时，它不关心具体是哪个模型，
# 而是去查这张表，找到被指派给vision_analysis这个“岗位”的模型，
# 然后去调用它。用户可以在设置界面中，像拖拽指派任务一样，决定哪个模型负责哪个功能。
class CapabilityAssignment(SQLModel, table=True):
    __tablename__ = "t_capability_assignments"    
    # ModelCapability value作主键
    capability_value: str = Field(primary_key=True)
    # 指派给哪个模型配置来完成这个任务
    model_configuration_id: int = Field(foreign_key="t_model_configurations.id")

# 聊天会话表
class ChatSession(SQLModel, table=True):
    __tablename__ = "t_chat_sessions"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON)) # 会话元数据：{"topic": "...", "file_count": 3, "message_count": 15}
    is_active: bool = Field(default=True)
    selected_tool_names: List[str] = Field(default=[], sa_column=Column(JSON)) # 会话中用户选中的额外工具
    scenario_id: Optional[int] = Field(default=None, foreign_key="t_scenarios.id") # 关联的"场景"ID

# 聊天消息表
class ChatMessage(SQLModel, table=True):
    __tablename__ = "t_chat_messages"
    id: int = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="t_chat_sessions.id", index=True)
    message_id: str = Field(max_length=100, unique=True)
    role: str = Field(max_length=50) # user, assistant, tool
    content: Optional[str] = Field(default=None) # 纯文本内容，用于快速预览和不支持结构化内容的场景

    # 存储符合Vercel AI SDK UI协议的结构化消息内容
    # e.g. [{'type': 'text', 'text': '...'}, {'type': 'tool-call', 'toolName': '...', 'args': {...}}]
    parts: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)

# 会话Pin文件表（会话级隔离）
class ChatSessionPinFile(SQLModel, table=True):
    __tablename__ = "t_chat_session_pin_files"
    id: int = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="t_chat_sessions.id", index=True)
    file_path: str = Field(max_length=500)
    file_name: str = Field(max_length=100)
    pinned_at: datetime = Field(default_factory=datetime.now)
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

# 工具类型
class ToolType(str, PyEnum):
    DIRECT = "direct"  # 直接调用Python函数
    CHANNEL = "channel"  # 通过消息通道调用前端功能
    MCP = "mcp"  # 通过模型上下文协议调用 https://github.com/modelcontextprotocol
# 大模型可使用的工具表
class Tool(SQLModel, table=True):
    __tablename__ = "t_tools"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True, unique=True)
    tool_type: str = Field(sa_column=Column(Enum(ToolType, values_callable=lambda obj: [e.value for e in obj]), default=ToolType.DIRECT.value))
    description: Optional[str] = Field(default=None, max_length=500)
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# 场景表
class Scenario(SQLModel, table=True):
    __tablename__ = "t_scenarios"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)
    display_name: Optional[str] = Field(default=None, max_length=100)
    system_prompt: Optional[str] = Field(default=None, max_length=500)
    preset_tool_names: List[str] = Field(default=[], sa_column=Column(JSON))  # 存储Tool ID列表
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# OAuth用户信息表
class User(SQLModel, table=True):
    __tablename__ = "t_users"
    id: int = Field(default=None, primary_key=True)
    oauth_provider: str = Field(max_length=50, index=True)  # google, github
    oauth_id: str = Field(max_length=255, index=True, unique=True)  # OAuth提供商的用户唯一ID
    email: str = Field(max_length=255, index=True)
    name: str = Field(max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    session_token: Optional[str] = Field(default=None)  # JWT token
    token_expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DBManager:
    """数据库结构管理类，负责新建和后续维护各业务模块数据表结构、索引、触发器等
    从上层拿到session，自己不管理数据库连接"""
    
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def init_db(self) -> bool:
        """初始化数据库 - 使用统一的Session连接管理，避免多连接冲突"""
        inspector = inspect(self.engine)
        
        with Session(self.engine) as session:
            # 创建任务表
            if not inspector.has_table(Task.__tablename__):
                # 使用engine创建表
                Task.__table__.create(self.engine, checkfirst=True)
                print(f"Created table {Task.__tablename__}")
                # * 删除表中已经完成的24小时之前的任务
                session.exec(text(f'''
                    DELETE FROM {Task.__tablename__}
                    WHERE status = 'completed' AND updated_at < datetime('now', '-24 hours');
                '''))
                session.commit()
        with Session(self.engine) as session:
            # 创建通知表
            if not inspector.has_table(Notification.__tablename__):
                Notification.__table__.create(self.engine, checkfirst=True)
                # 创建触发器 - 当任务表中洞察任务状态成功完成时插入通知
                # conn.execute(text(f'''
                #     CREATE TRIGGER IF NOT EXISTS notify_insight_task
                #     AFTER UPDATE ON {Task.__tablename__}
                #     FOR EACH ROW
                #     WHEN NEW.task_type = 'insight' AND NEW.status = 'completed' AND NEW.result = 'success'
                #     BEGIN
                #         INSERT INTO {Notification.__tablename__} (task_id, message, created_at, read)
                #         VALUES (NEW.id, '洞察任务完成', CURRENT_TIMESTAMP, 0);
                #     END;
                # '''))
                session.commit()
        with Session(self.engine) as session:
            # 创建文件夹表
            if not inspector.has_table(MyFolders.__tablename__):
                MyFolders.__table__.create(self.engine, checkfirst=True)
                self._init_default_directories()  # 初始化默认文件夹
            
            # 创建Bundle扩展名表
            if not inspector.has_table(BundleExtension.__tablename__):
                BundleExtension.__table__.create(self.engine, checkfirst=True)
                self._init_bundle_extensions()  # 初始化Bundle扩展名数据
            
            # 创建系统配置表
            if not inspector.has_table(SystemConfig.__tablename__):
                SystemConfig.__table__.create(self.engine, checkfirst=True)
                system_configs = [
                    {
                        "key": "proxy",
                        "value": "http://127.0.0.1:7890",
                        "description": "Proxy server address"
                    },
                ]
                for config_data in system_configs:
                    new_config = SystemConfig(
                        key=config_data["key"],
                        value=config_data["value"],
                        description=config_data["description"]
                    )
                    session.add(new_config)
                session.commit()
            
            # 创建文件分类表
            if not inspector.has_table(FileCategory.__tablename__):
                FileCategory.__table__.create(self.engine, checkfirst=True)
                self._init_file_categories()  # 初始化文件分类数据
            
            # 创建文件扩展名映射表
            if not inspector.has_table(FileExtensionMap.__tablename__):
                FileExtensionMap.__table__.create(self.engine, checkfirst=True)
                self._init_file_extensions()  # 初始化文件扩展名映射数据
            
            # 创建文件过滤规则表
            if not inspector.has_table(FileFilterRule.__tablename__):
                FileFilterRule.__table__.create(self.engine, checkfirst=True)
                self._init_basic_file_filter_rules()  # 初始化基础文件过滤规则（简化版）
                        
            # 创建标签表
            if not inspector.has_table(Tags.__tablename__):
                Tags.__table__.create(self.engine, checkfirst=True)
            
            # 创建文件粗筛结果表
            if not inspector.has_table(FileScreeningResult.__tablename__):
                FileScreeningResult.__table__.create(self.engine, checkfirst=True)
                # 创建索引 - 为文件路径创建唯一索引
                session.exec(text(f'CREATE UNIQUE INDEX IF NOT EXISTS idx_file_path ON {FileScreeningResult.__tablename__} (file_path);'))
                # 创建索引 - 为文件状态创建索引，便于查询待处理文件
                session.exec(text(f'CREATE INDEX IF NOT EXISTS idx_file_status ON {FileScreeningResult.__tablename__} (status);'))
                # 创建索引 - 为修改时间创建索引，便于按时间查询
                session.exec(text(f'CREATE INDEX IF NOT EXISTS idx_modified_time ON {FileScreeningResult.__tablename__} (modified_time);'))
                # 创建索引 - 为task_id创建索引，便于查询关联任务
                session.exec(text(f'CREATE INDEX IF NOT EXISTS idx_task_id ON {FileScreeningResult.__tablename__} (task_id);'))

            # 创建 FTS5 虚拟表和触发器
            if not inspector.has_table('t_files_fts'):
                session.exec(text("""
                    CREATE VIRTUAL TABLE t_files_fts USING fts5(
                        file_id UNINDEXED,
                        tags_search_ids
                    );
                """))
            
            # 删除旧的触发器（如果存在）
            session.exec(text("DROP TRIGGER IF EXISTS trg_files_after_insert;"))
            session.exec(text("DROP TRIGGER IF EXISTS trg_files_after_delete;"))
            session.exec(text("DROP TRIGGER IF EXISTS trg_files_after_update;"))
            
            # 创建新的触发器
            session.exec(text(f"""
                CREATE TRIGGER IF NOT EXISTS trg_files_after_insert AFTER INSERT ON {FileScreeningResult.__tablename__}
                BEGIN
                    INSERT INTO t_files_fts (file_id, tags_search_ids)
                    VALUES (NEW.id, REPLACE(IFNULL(NEW.tags_display_ids, ''), ',', ' '));
                END;
            """))

            session.exec(text(f"""
                CREATE TRIGGER IF NOT EXISTS trg_files_after_delete AFTER DELETE ON {FileScreeningResult.__tablename__}
                BEGIN
                    DELETE FROM t_files_fts WHERE file_id = OLD.id;
                END;
            """))

            session.exec(text(f"""
                CREATE TRIGGER IF NOT EXISTS trg_files_after_update AFTER UPDATE ON {FileScreeningResult.__tablename__}
                BEGIN
                    DELETE FROM t_files_fts WHERE file_id = OLD.id;
                    INSERT INTO t_files_fts (file_id, tags_search_ids)
                    VALUES (NEW.id, REPLACE(IFNULL(NEW.tags_display_ids, ''), ',', ' '));
                END;
            """))

            # 创建文档表
            # TODO 根据后续代码里的要求创建索引
            if not inspector.has_table(Document.__tablename__):
                Document.__table__.create(self.engine, checkfirst=True)
            # 创建父块表
            if not inspector.has_table(ParentChunk.__tablename__):
                ParentChunk.__table__.create(self.engine, checkfirst=True)
            # 创建子块表
            if not inspector.has_table(ChildChunk.__tablename__):
                ChildChunk.__table__.create(self.engine, checkfirst=True)
        
            # 创建聊天会话表
            if not inspector.has_table(ChatSession.__tablename__):
                ChatSession.__table__.create(self.engine, checkfirst=True)
            # 创建聊天消息表
            if not inspector.has_table(ChatMessage.__tablename__):
                ChatMessage.__table__.create(self.engine, checkfirst=True)
                # INDEX(session_id, created_at)   -- 查询优化
                session.exec(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_chat_message_session ON {ChatMessage.__tablename__} (session_id, created_at);
                """))
            # 创建会话Pin文件表
            if not inspector.has_table(ChatSessionPinFile.__tablename__):
                ChatSessionPinFile.__table__.create(self.engine, checkfirst=True)
                # UNIQUE(session_id, file_path)   -- 同一会话中文件唯一
                session.exec(text(f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_session_pin_file ON {ChatSessionPinFile.__tablename__} (session_id, file_path);
                """))
            
            # 模型提供者表
            if not inspector.has_table(ModelProvider.__tablename__):
                ModelProvider.__table__.create(self.engine, checkfirst=True)
                # 初始化默认模型提供者
                data = [
                    {
                        "display_name": "OpenAI", 
                        "provider_type": "openai",
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "https://api.openai.com/v1", 
                        "is_user_added": False,
                        "get_key_url": "https://platform.openai.com/api-keys",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "Anthropic", 
                        "provider_type": "anthropic", 
                        "source_type": ModelSourceType.CONFIGURABLE.value,
                        "base_url": "https://api.anthropic.com/v1",
                        "is_user_added": False,
                        "get_key_url": "https://console.anthropic.com/settings/keys",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "Google Gemini", 
                        "provider_type": "google", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "https://generativelanguage.googleapis.com/v1beta",
                        "is_user_added": False,
                        "get_key_url": "https://aistudio.google.com/apikey",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "Grok (xAI)", 
                        "provider_type": "grok", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "https://api.x.ai/v1",
                        "is_user_added": False,
                        "get_key_url": "https://console.x.ai/",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "OpenRouter", 
                        "provider_type": "openai", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "https://openrouter.ai/api/v1",
                        "is_user_added": False,
                        "get_key_url": "https://openrouter.ai/keys",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "Groq", 
                        "provider_type": "groq", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "https://api.groq.com/openai/v1",
                        "is_user_added": False,
                        "get_key_url": "https://console.groq.com/keys",
                        "support_discovery": False,
                        "use_proxy": False,
                    },
                    {
                        "display_name": "Ollama", 
                        "provider_type": "openai", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "http://127.0.0.1:11434/v1",
                        "is_user_added": False,
                        "get_key_url": "",
                        "support_discovery": True,
                        "extra_data_json": {"discovery_api": "http://127.0.0.1:11434/api/tags"},
                        "use_proxy": False,
                    },
                    {
                        "display_name": "LM Studio", 
                        "provider_type": "openai", 
                        "source_type": ModelSourceType.CONFIGURABLE.value, 
                        "base_url": "http://127.0.0.1:1234/api/v0",
                        "is_user_added": False,
                        "get_key_url": "",
                        "support_discovery": True,
                        "use_proxy": False,
                    },
                ]
                session.add_all([ModelProvider(**provider) for provider in data])
                session.commit()
            
            # 模型配置表
            if not inspector.has_table(ModelConfiguration.__tablename__):
                ModelConfiguration.__table__.create(self.engine, checkfirst=True)
                # provider_id和model_identifier的组合唯一
                session.exec(text(f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_provider_id_model_identifier ON {ModelConfiguration.__tablename__} (provider_id, model_identifier);
                """))
                data = [
                    # 内置模型 - 直接运行在本地
                    {
                        "provider_id": 1,  # [Builtin]
                        "model_identifier": BUILTMODELS['VLM_MODEL']['MLXCOMMUNITY'],
                        "display_name": "Qwen3-VL 4B (3-bit)", 
                        "capabilities_json": [ModelCapability.VISION.value, ModelCapability.TEXT.value, ModelCapability.STRUCTURED_OUTPUT.value, ModelCapability.TOOL_USE.value],
                        "max_context_length": 256*1024,
                        "max_output_tokens": 1024,
                        "is_enabled": True,
                    }
                ]
                session.add_all([ModelConfiguration(**model) for model in data])
                session.commit()
            
            # 能力指派表
            if not inspector.has_table(CapabilityAssignment.__tablename__):
                CapabilityAssignment.__table__.create(self.engine, checkfirst=True)
                # 将builtin模型指派给各能力
                data = [
                    {
                        "capability_value": ModelCapability.VISION.value,
                        "model_configuration_id": 1,  # Qwen3-VL 4B
                    },
                    {
                        "capability_value": ModelCapability.TEXT.value,
                        "model_configuration_id": 1,  # Qwen3-VL 4B
                    },
                    {
                        "capability_value": ModelCapability.STRUCTURED_OUTPUT.value,
                        "model_configuration_id": 1,  # Qwen3-VL 4B
                    },
                    {
                        "capability_value": ModelCapability.TOOL_USE.value,
                        "model_configuration_id": 1,  # Qwen3-VL 4B
                    },
                ]
                session.add_all([CapabilityAssignment(**assignment) for assignment in data])
                session.commit()
            
            # OAuth用户表
            if not inspector.has_table(User.__tablename__):
                User.__table__.create(self.engine, checkfirst=True)
                print(f"Created table {User.__tablename__}")
                # 创建索引
                session.exec(text(f'CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_provider_id ON {User.__tablename__} (oauth_provider, oauth_id);'))
                session.exec(text(f'CREATE INDEX IF NOT EXISTS idx_email ON {User.__tablename__} (email);'))
                session.commit()
        
            # 工具表
            if not inspector.has_table(Tool.__tablename__):
                Tool.__table__.create(self.engine, checkfirst=True)
                data = [
                    {
                        "name": "get_current_time",
                        "description": "取得当前日期和时间，可选timezone参数指定时区",
                        "tool_type": ToolType.DIRECT.value,
                        "metadata_json": {"model_path": "tools.datetime_tools:get_current_time"}
                    },
                    {
                        "name": "local_file_search",
                        "description": "本机文件搜索工具。参数是一个搜索关键词，返回匹配的文件路径列表。",
                        "tool_type": ToolType.DIRECT.value,  # 直接调用
                        "metadata_json": {"model_path": "tools.local_file_search:local_file_search"}
                    },
                    {
                        "name": "multimodal_vectorize",
                        "description": "给文件进行多模态向量化，以便后续支持多模态检索",
                        "tool_type": ToolType.DIRECT.value,
                        "metadata_json": {"model_path": "tools.vector_store:multimodal_vectorize"}
                    },
                    {
                        "name": "search_use_tavily",
                        "description": "使用Tavily进行网络搜索",
                        "tool_type": ToolType.MCP.value,
                        "metadata_json": {
                            "model_path": "tools.web_search:search_use_tavily",
                            "api_key": "",
                            "languages": {
                                "zh": "使用Tavily进行网络搜索",
                                "en": "Using Tavily for web search",
                            },
                            "icon": {
                                "light": "https://www.tavily.com/images/logo.svg",
                                "dark": "https://www.tavily.com/images/logo.svg"
                            }
                        }
                    },
                    # {
                    #     "name": "handle_pdf_reading",
                    #     "description": "通过系统默认PDF阅读器打开PDF文件。并重新排布窗口，本App位于左侧，PDF阅读器位于右侧。",
                    #     "tool_type": "channel",  # 通过工具通道调用
                    #     "metadata_json": {"model_path": "tools.co_reading:handle_pdf_reading"}
                    # },
                ]
                session.add_all([Tool(**tool) for tool in data])
                session.commit()

            # 场景表
            if not inspector.has_table(Scenario.__tablename__):
                Scenario.__table__.create(self.engine, checkfirst=True)
                data = [
                    {
                        "name": "co_reading", 
                        "description": "AI跟你一起阅读电子书", 
                        "display_name": "共读电子书",
                        "system_prompt": """
你是一个专业的PDF阅读助手，具有视觉能力。用户正在使用PDF阅读器阅读文档，你收到的图片是用户当前阅读页面的截图。

你的任务：
1. 准确识别PDF截图中的文本内容和图表信息
2. 理解用户当前的阅读进度和关注点  
3. 基于截图内容回答用户的问题
4. 理解和利用“相关知识背景”中的信息而不是想象和编造

注意事项：
- 截图反映了用户当前的视野范围，请重点关注可见内容
- 如果截图不清晰或内容不完整，请告知用户并建议进行内容放大后再次发问
- 结合用户的问题和截图内容提供精准回答
- 保持简洁专业的回复风格
""".strip(),
                        "preset_tool_ids": [],
                        "metadata_json": []
                    },
                ]
                session.add_all([Scenario(**scenario) for scenario in data])
                session.commit()
                
            # 提交所有数据库更改
            session.commit()
            return True


    def _init_bundle_extensions(self) -> None:
        """初始化macOS Bundle扩展名数据"""
        bundle_extensions = [
            # 应用程序Bundle
            {"extension": ".app", "description": "macOS application"},
            {"extension": ".bundle", "description": "macOS bundle"},
            {"extension": ".framework", "description": "macOS framework bundle"},
            {"extension": ".plugin", "description": "macOS plugin bundle"},
            {"extension": ".kext", "description": "macOS core extension"},
            
            # 媒体和创意软件Bundle
            {"extension": ".fcpbundle", "description": "Final Cut Pro project"},
            {"extension": ".imovielibrary", "description": "iMovie library"},
            {"extension": ".tvlibrary", "description": "TV library"},
            {"extension": ".theater", "description": "Theater app library"},
            {"extension": ".photoslibrary", "description": "Photos library"},
            {"extension": ".logicx", "description": "Logic Pro X project"},
            
            # 办公软件Bundle
            {"extension": ".pages", "description": "Apple Pages document bundle"},
            {"extension": ".numbers", "description": "Apple Numbers spreadsheet bundle"},
            {"extension": ".key", "description": "Apple Keynote presentation bundle"},
            
            # 开发工具Bundle
            {"extension": ".xcodeproj", "description": "Xcode project bundle"},
            {"extension": ".xcworkspace", "description": "Xcode workspace bundle"},
            {"extension": ".playground", "description": "Swift Playground bundle"},
            {"extension": ".xcassets", "description": "Xcode asset catalog bundle"},
            {"extension": ".xcdatamodeld", "description": "Core Data model bundle"},
            
            # 设计和自动化Bundle
            {"extension": ".sketch", "description": "Sketch design file bundle"},
            {"extension": ".workflow", "description": "Automator workflow bundle"},
            {"extension": ".action", "description": "Automator action bundle"},
            {"extension": ".lbaction", "description": "LaunchBar action bundle"},
            
            # 系统相关Bundle
            {"extension": ".prefpane", "description": "System Preferences pane"},
            {"extension": ".appex", "description": "App extension"},
            {"extension": ".component", "description": "Audio unit component"},
            {"extension": ".wdgt", "description": "Dashboard widget"},
            {"extension": ".qlgenerator", "description": "Quick Look generator"},
            {"extension": ".mdimporter", "description": "Spotlight metadata importer"},
            {"extension": ".safari-extension", "description": "Safari extension"},
            
            # 本地化和资源Bundle
            {"extension": ".lproj", "description": "Localization resource directory"},
            {"extension": ".nib", "description": "Interface Builder file bundle"},
            {"extension": ".storyboard", "description": "Interface Builder storyboard bundle"},
            
            # 其他Bundle
            {"extension": ".download", "description": "Incomplete download bundle"},
            {"extension": ".scptd", "description": "AppleScript file"},
            {"extension": ".rtfd", "description": "Rich Text Format directory"},
        ]
        
        bundle_objs = []
        for ext_data in bundle_extensions:
            bundle_objs.append(
                BundleExtension(
                    extension=ext_data["extension"],
                    description=ext_data["description"],
                    is_active=True,
                    is_system_default=True  # 系统初始化的记录标记为不可删除/修改
                )
            )
        with Session(self.engine) as session:
            session.add_all(bundle_objs)
            session.commit()
    
    def _init_basic_file_filter_rules(self) -> None:
        """初始化基础文件过滤规则（仅保留基础忽略规则）"""
        
        # 基础忽略规则 - 系统文件和临时文件
        basic_ignore_rules = [
            # macOS system files
            {
                "name": "macOS system files",
                "description": "Ignore files generated by macOS",
                "rule_type": RuleType.FILENAME.value,
                "pattern": r"^\.(DS_Store|AppleDouble|LSOverride|DocumentRevisions-V100|fseventsd|Spotlight-V100|TemporaryItems|Trashes|VolumeIcon\.icns|com\.apple\.timemachine\.donotpresent)$",
                "pattern_type": "regex",
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            },
            # Windows system files
            {
                "name": "Windows system files",
                "description": "Ignore files generated by Windows",
                "rule_type": RuleType.FILENAME.value,
                "pattern": r"^(Thumbs\.db|ehthumbs\.db|Desktop\.ini|\$RECYCLE\.BIN|System Volume Information)$",
                "pattern_type": "regex",
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            },
            # Common temporary files
            {
                "name": "Temporary files",
                "description": "Ignore various temporary files",
                "rule_type": RuleType.FILENAME.value,
                "pattern": r"(\.tmp$|\.temp$|~$|\$.*\$|\.swp$|\.swo$)",
                "pattern_type": "regex",
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            },
            # Development related ignore directories
            {
                "name": "Development tool cache directories",
                "description": "Ignore cache directories generated by development tools",
                "rule_type": RuleType.FOLDER.value,
                "pattern": r"(node_modules|\.git|\.svn|\.hg|__pycache__|\.pytest_cache|\.tox|\.coverage|build|dist|\.env|venv|env)(/|$)",
                "pattern_type": "regex", 
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            },
            # System cache directories
            {
                "name": "System cache directories",
                "description": "Ignore system cache directories",
                "rule_type": RuleType.FOLDER.value,
                "pattern": r"(Library/Caches|Library/Logs|\.cache|\.local/share/Trash)(/|$)",
                "pattern_type": "regex",
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            },
            # IDE configuration directories
            {
                "name": "IDE configuration directories",
                "description": "Ignore IDE configuration directories",
                "rule_type": RuleType.FOLDER.value,
                "pattern": r"(\.vscode|\.idea|\.eclipse|\.settings)(/|$)",
                "pattern_type": "regex",
                "action": RuleAction.EXCLUDE.value,
                "priority": RulePriority.HIGH.value
            }
        ]
        
        # 转换为FileFilterRule对象并批量插入
        rule_objs = []
        for rule_data in basic_ignore_rules:
            rule_objs.append(
                FileFilterRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    rule_type=rule_data["rule_type"],
                    category_id=rule_data.get("category_id"),
                    pattern=rule_data["pattern"],
                    pattern_type=rule_data.get("pattern_type", "regex"),
                    action=rule_data["action"],
                    priority=rule_data["priority"],
                    is_system=True,
                    enabled=True,
                    extra_data=rule_data.get("extra_data")
                )
            )
        with Session(self.engine) as session:
            session.add_all(rule_objs)
            session.commit()
    
    def _init_file_categories(self) -> None:
        """初始化文件分类数据"""
        categories = [
            FileCategory(name="document", description="Document files", icon="📄"),
            FileCategory(name="image", description="Image files", icon="🖼️"),
            FileCategory(name="audio_video", description="Audio/Video files", icon="🎬"),
            FileCategory(name="archive", description="Archive files", icon="🗃️"),
            FileCategory(name="installer", description="Installer files", icon="📦"),
            FileCategory(name="code", description="Code files", icon="💻"),
            FileCategory(name="design", description="Design files", icon="🎨"),
            FileCategory(name="temp", description="Temporary files", icon="⏱️"),
            FileCategory(name="other", description="Other files", icon="📎"),
        ]
        with Session(self.engine) as session:
            session.add_all(categories)
            session.commit()

    def _init_file_extensions(self) -> None:
        """初始化文件扩展名映射"""
        # 获取分类ID映射
        with Session(self.engine) as session:
            stmt = select(FileCategory)
            category_map = {cat.name: cat.id for cat in session.exec(stmt).all()}
            
            # 文档类扩展名
            doc_extensions = [
                # MS Office
                {"extension": "doc", "category_id": category_map["document"], "description": "Microsoft Word Document (Old Version)"},
                {"extension": "docx", "category_id": category_map["document"], "description": "Microsoft Word Document"},
                {"extension": "ppt", "category_id": category_map["document"], "description": "Microsoft PowerPoint Presentation (Old Version)"},
                {"extension": "pptx", "category_id": category_map["document"], "description": "Microsoft PowerPoint Presentation"},
                {"extension": "xls", "category_id": category_map["document"], "description": "Microsoft Excel Spreadsheet (Old Version)"},
                {"extension": "xlsx", "category_id": category_map["document"], "description": "Microsoft Excel Spreadsheet"},
                # Apple iWork
                {"extension": "pages", "category_id": category_map["document"], "description": "Apple Pages Document"},
                {"extension": "key", "category_id": category_map["document"], "description": "Apple Keynote Presentation"},
                {"extension": "numbers", "category_id": category_map["document"], "description": "Apple Numbers Spreadsheet"},
                # Text Documents
                {"extension": "md", "category_id": category_map["document"], "description": "Markdown Document"},
                {"extension": "markdown", "category_id": category_map["document"], "description": "Markdown Document"},
                {"extension": "txt", "category_id": category_map["document"], "description": "Plain Text Document"},
                {"extension": "rtf", "category_id": category_map["document"], "description": "Rich Text Format Document"},
                # E-books/Fixed Format
                {"extension": "pdf", "category_id": category_map["document"], "description": "PDF Document", "priority": "high"},
                {"extension": "epub", "category_id": category_map["document"], "description": "EPUB E-book"},
                {"extension": "mobi", "category_id": category_map["document"], "description": "MOBI E-book"},
                # Web Documents
                {"extension": "html", "category_id": category_map["document"], "description": "HTML Web Page"},
                {"extension": "htm", "category_id": category_map["document"], "description": "HTML Web Page"},
            ]
            
            # Image Extensions
            image_extensions = [
                {"extension": "jpg", "category_id": category_map["image"], "description": "JPEG Image", "priority": "high"},
                {"extension": "jpeg", "category_id": category_map["image"], "description": "JPEG Image", "priority": "high"},
                {"extension": "png", "category_id": category_map["image"], "description": "PNG Image", "priority": "high"},
                {"extension": "gif", "category_id": category_map["image"], "description": "GIF Image"},
                {"extension": "bmp", "category_id": category_map["image"], "description": "BMP Image"},
                {"extension": "tiff", "category_id": category_map["image"], "description": "TIFF Image"},
                {"extension": "heic", "category_id": category_map["image"], "description": "HEIC Image (Apple Devices)"},
                {"extension": "webp", "category_id": category_map["image"], "description": "WebP Image"},
                {"extension": "svg", "category_id": category_map["image"], "description": "SVG Vector Image"},
                {"extension": "cr2", "category_id": category_map["image"], "description": "Canon RAW Image"},
                {"extension": "nef", "category_id": category_map["image"], "description": "Nikon RAW Image"},
                {"extension": "arw", "category_id": category_map["image"], "description": "Sony RAW Image"},
                {"extension": "dng", "category_id": category_map["image"], "description": "Generic RAW Image"},
            ]
            
            # Audio/Video Extensions
            av_extensions = [
                # Audio
                {"extension": "mp3", "category_id": category_map["audio_video"], "description": "MP3 Audio", "priority": "high"},
                {"extension": "wav", "category_id": category_map["audio_video"], "description": "WAV Audio"},
                {"extension": "aac", "category_id": category_map["audio_video"], "description": "AAC Audio"},
                {"extension": "flac", "category_id": category_map["audio_video"], "description": "FLAC Lossless Audio"},
                {"extension": "ogg", "category_id": category_map["audio_video"], "description": "OGG Audio"},
                {"extension": "m4a", "category_id": category_map["audio_video"], "description": "M4A Audio"},
                # Video
                {"extension": "mp4", "category_id": category_map["audio_video"], "description": "MP4 Video", "priority": "high"},
                {"extension": "mov", "category_id": category_map["audio_video"], "description": "MOV Video (Apple Devices)", "priority": "high"},
                {"extension": "avi", "category_id": category_map["audio_video"], "description": "AVI Video"},
                {"extension": "mkv", "category_id": category_map["audio_video"], "description": "MKV Video"},
                {"extension": "wmv", "category_id": category_map["audio_video"], "description": "WMV Video (Windows)"},
                {"extension": "flv", "category_id": category_map["audio_video"], "description": "Flash Video"},
                {"extension": "webm", "category_id": category_map["audio_video"], "description": "WebM Video"},
            ]
            
            # Archive Extensions
            archive_extensions = [
                {"extension": "zip", "category_id": category_map["archive"], "description": "ZIP Archive", "priority": "high"},
                {"extension": "rar", "category_id": category_map["archive"], "description": "RAR Archive"},
                {"extension": "7z", "category_id": category_map["archive"], "description": "7-Zip Archive"},
                {"extension": "tar", "category_id": category_map["archive"], "description": "TAR Archive"},
                {"extension": "gz", "category_id": category_map["archive"], "description": "GZIP Archive"},
                {"extension": "bz2", "category_id": category_map["archive"], "description": "BZIP2 Archive"},
            ]
            
            # Installer Extensions
            installer_extensions = [
                {"extension": "dmg", "category_id": category_map["installer"], "description": "macOS Disk Image", "priority": "high"},
                {"extension": "pkg", "category_id": category_map["installer"], "description": "macOS Installer Package", "priority": "high"},
                {"extension": "exe", "category_id": category_map["installer"], "description": "Windows Executable File", "priority": "high"},
                {"extension": "msi", "category_id": category_map["installer"], "description": "Windows Installer Package"},
            ]
            
            # Code Extensions
            code_extensions = [
                {"extension": "py", "category_id": category_map["code"], "description": "Python Source Code"},
                {"extension": "js", "category_id": category_map["code"], "description": "JavaScript Source Code"},
                {"extension": "ts", "category_id": category_map["code"], "description": "TypeScript Source Code"},
                {"extension": "java", "category_id": category_map["code"], "description": "Java Source Code"},
                {"extension": "c", "category_id": category_map["code"], "description": "C Source Code"},
                {"extension": "cpp", "category_id": category_map["code"], "description": "C++ Source Code"},
                {"extension": "h", "category_id": category_map["code"], "description": "C/C++ Header File"},
                {"extension": "cs", "category_id": category_map["code"], "description": "C# Source Code"},
                {"extension": "php", "category_id": category_map["code"], "description": "PHP Source Code"},
                {"extension": "rb", "category_id": category_map["code"], "description": "Ruby Source Code"},
                {"extension": "go", "category_id": category_map["code"], "description": "Go Source Code"},
                {"extension": "swift", "category_id": category_map["code"], "description": "Swift Source Code"},
                {"extension": "kt", "category_id": category_map["code"], "description": "Kotlin Source Code"},
                {"extension": "sh", "category_id": category_map["code"], "description": "Shell Script"},
                {"extension": "bat", "category_id": category_map["code"], "description": "Windows Batch File"},
                {"extension": "json", "category_id": category_map["code"], "description": "JSON Data File"},
                {"extension": "yaml", "category_id": category_map["code"], "description": "YAML Configuration File"},
                {"extension": "yml", "category_id": category_map["code"], "description": "YAML Configuration File"},
                {"extension": "toml", "category_id": category_map["code"], "description": "TOML Configuration File"},
                {"extension": "xml", "category_id": category_map["code"], "description": "XML Data File"},
                {"extension": "css", "category_id": category_map["code"], "description": "CSS Stylesheet"},
                {"extension": "scss", "category_id": category_map["code"], "description": "SCSS Stylesheet"},
            ]
            
            # Design Extensions
            design_extensions = [
                {"extension": "psd", "category_id": category_map["design"], "description": "Photoshop Design File"},
                {"extension": "ai", "category_id": category_map["design"], "description": "Adobe Illustrator Design File"},
                {"extension": "sketch", "category_id": category_map["design"], "description": "Sketch Design File"},
                {"extension": "fig", "category_id": category_map["design"], "description": "Figma Design File"},
                {"extension": "xd", "category_id": category_map["design"], "description": "Adobe XD Design File"},
            ]
            
            # Temporary File Extensions
            temp_extensions = [
                {"extension": "tmp", "category_id": category_map["temp"], "description": "Temporary File"},
                {"extension": "temp", "category_id": category_map["temp"], "description": "Temporary File"},
                {"extension": "part", "category_id": category_map["temp"], "description": "Incomplete Downloaded File"},
                {"extension": "crdownload", "category_id": category_map["temp"], "description": "Chrome Download Temporary File"},
                {"extension": "download", "category_id": category_map["temp"], "description": "Download Temporary File"},
                {"extension": "bak", "category_id": category_map["temp"], "description": "Backup File"},
            ]
            
            # 合并所有扩展名
            all_extensions = []
            all_extensions.extend(doc_extensions)
            all_extensions.extend(image_extensions)
            all_extensions.extend(av_extensions)
            all_extensions.extend(archive_extensions)
            all_extensions.extend(installer_extensions)
            all_extensions.extend(code_extensions)
            all_extensions.extend(design_extensions)
            all_extensions.extend(temp_extensions)
            
            # 转换为FileExtensionMap对象并批量插入
            extension_objs = []
            for ext_data in all_extensions:
                priority = ext_data.get("priority", "medium")
                extension_objs.append(
                    FileExtensionMap(
                        extension=ext_data["extension"],
                        category_id=ext_data["category_id"],
                        description=ext_data["description"],
                        priority=priority
                    )
                )
            
            session.add_all(extension_objs)
            session.commit()

    def _init_default_directories(self) -> None:
        """初始化默认系统文件夹"""
        import platform
        
        # 检查是否已有文件夹记录，如果有则跳过初始化
        with Session(self.engine) as session:
            existing_count = session.exec(select(MyFolders)).first()
            if existing_count is not None:
                return
        
        default_dirs = []
        system = platform.system()
        
        # 设置用户主目录
        home_dir = os.path.expanduser("~") if system != "Windows" else os.environ.get("USERPROFILE", "")
        
        if system == "Darwin":  # macOS
            # 白名单常用文件夹（用户数据文件夹，通常希望被扫描）
            whitelist_common_dirs = [
                {"name": "Desktop", "path": os.path.join(home_dir, "Desktop")},
                {"name": "Documents", "path": os.path.join(home_dir, "Documents")},
                {"name": "Downloads", "path": os.path.join(home_dir, "Downloads")},
                {"name": "Pictures", "path": os.path.join(home_dir, "Pictures")},
                {"name": "Music", "path": os.path.join(home_dir, "Music")},
                {"name": "Movies", "path": os.path.join(home_dir, "Movies")},
            ]
            
        elif system == "Windows":
            # Windows系统
            if home_dir:
                # 白名单常用文件夹
                whitelist_common_dirs = [
                    {"name": "Desktop", "path": os.path.join(home_dir, "Desktop")},
                    {"name": "Documents", "path": os.path.join(home_dir, "Documents")},
                    {"name": "Downloads", "path": os.path.join(home_dir, "Downloads")},
                    {"name": "Pictures", "path": os.path.join(home_dir, "Pictures")},
                    {"name": "Music", "path": os.path.join(home_dir, "Music")},
                    {"name": "Videos", "path": os.path.join(home_dir, "Videos")},
                ]
                
            else:
                whitelist_common_dirs = []
        else:
            # Linux系统
            whitelist_common_dirs = [
                {"name": "Desktop", "path": os.path.join(home_dir, "Desktop")},
                {"name": "Documents", "path": os.path.join(home_dir, "Documents")},
                {"name": "Downloads", "path": os.path.join(home_dir, "Downloads")},
                {"name": "Pictures", "path": os.path.join(home_dir, "Pictures")},
                {"name": "Music", "path": os.path.join(home_dir, "Music")},
                {"name": "Videos", "path": os.path.join(home_dir, "Videos")},
            ]
        
        # 处理白名单文件夹（用户数据文件夹）
        for dir_info in whitelist_common_dirs:
            if os.path.exists(dir_info["path"]) and os.path.isdir(dir_info["path"]):
                default_dirs.append(
                    MyFolders(
                        path=dir_info["path"],
                        alias=dir_info["name"],
                        is_blacklist=False,
                        is_common_folder=True  # 标记为常见文件夹，界面上不可删除
                    )
                )
        
        if default_dirs:
            with Session(self.engine) as session:
                session.add_all(default_dirs)
                session.commit()

if __name__ == '__main__':
    import os
    from core.config import TEST_DB_PATH
    from sqlalchemy import event
    
    def setup_sqlite_wal_mode(engine):
        """为SQLite引擎设置WAL模式和优化参数"""
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """设置SQLite优化参数和WAL模式"""
            cursor = dbapi_connection.cursor()
            # 启用WAL模式（Write-Ahead Logging）
            cursor.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式为NORMAL，在WAL模式下提供良好的性能和安全性平衡
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 设置缓存大小（负数表示KB，这里设置为64MB）
            cursor.execute("PRAGMA cache_size=-65536")
            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys=ON")
            # 设置临时存储为内存模式
            cursor.execute("PRAGMA temp_store=MEMORY")
            # 设置WAL自动检查点阈值（页面数）
            cursor.execute("PRAGMA wal_autocheckpoint=1000")
            cursor.close()

    def create_optimized_sqlite_engine(sqlite_url, **kwargs):
        """创建优化的SQLite引擎，自动配置WAL模式"""
        default_connect_args = {"check_same_thread": False, "timeout": 30}
        # 合并用户提供的connect_args
        if "connect_args" in kwargs:
            default_connect_args.update(kwargs["connect_args"])
        kwargs["connect_args"] = default_connect_args
        # 创建引擎
        engine = create_engine(sqlite_url, echo=False, **kwargs)
        # 设置WAL模式
        setup_sqlite_wal_mode(engine)
        return engine
    
    # # 清理可能存在的WAL文件残留
    # wal_file = TEST_DB_PATH + "-wal"
    # shm_file = TEST_DB_PATH + "-shm"
    
    # if os.path.exists(wal_file) or os.path.exists(shm_file):
    #     print("检测到WAL/SHM文件残留，尝试清理...")
    #     try:
    #         # 尝试删除WAL和SHM文件
    #         if os.path.exists(wal_file):
    #             os.remove(wal_file)
    #             print("已删除WAL文件")
    #         if os.path.exists(shm_file):
    #             os.remove(shm_file)
    #             print("已删除SHM文件")
    #     except Exception as cleanup_error:
    #         print(f"清理WAL/SHM文件失败: {cleanup_error}")
    #         print("请手动删除这些文件后重试")
    #         exit(1)
    
    print(f"数据库文件检查完成: {TEST_DB_PATH}")
    
    # 使用优化的引擎（和main.py一样的配置）
    sqlite_url = f'sqlite:///{TEST_DB_PATH}'
    engine = create_optimized_sqlite_engine(
        sqlite_url,
        pool_size=5,       # 设置连接池大小
        max_overflow=10,   # 允许的最大溢出连接数
        pool_timeout=30,   # 获取连接的超时时间
        pool_recycle=1800  # 30分钟回收一次连接
    )
    
    print("创建优化SQLite引擎完成，WAL模式已配置")
    
    # 使用单一连接进行完整的数据库初始化流程 - 避免连接池竞争
    print("开始单一连接数据库初始化流程...")
    try:
        # 使用单个连接完成所有操作
        with engine.connect() as conn:
            print("设置WAL模式和优化参数...")
            # 显式设置WAL模式和优化参数
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=-65536"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
            
            # 验证WAL模式设置
            journal_mode = conn.execute(text("PRAGMA journal_mode")).fetchone()[0]
            if journal_mode.upper() != 'WAL':
                print(f"警告：WAL模式设置可能失败，当前模式: {journal_mode}")
            else:
                print("WAL模式设置成功")
            
            # 使用同一个连接创建Session并进行数据库初始化
            print("开始数据库结构初始化...")
            db_mgr = DBManager(engine=engine)
            db_mgr.init_db()
            
            # 最终提交连接级别的事务
            conn.commit()
            print("数据库初始化完成")
            
    except Exception as error:
        print(f"数据库初始化失败: {error}")
        print("这可能表明数据库被其他进程锁定，请检查是否有其他程序正在使用数据库")
        import traceback
        traceback.print_exc()
        exit(1)