"""
LeafKnow 应用配置模块
"""
from functools import wraps
from uuid import uuid4
from pathlib import Path

# 内置模型配置
BUILTMODELS = {
    "EMBEDDING_MODEL": {
        "LLAMACPPPYTHON": "https://huggingface.co/ggml-org/embeddinggemma-300M-qat-q4_0-GGUF/blob/main/embeddinggemma-300M-qat-Q4_0.gguf",
        "MLXCOMMUNITY": "mlx-community/embeddinggemma-300m-4bit",
    },
    "EMBEDDING_DIMENSIONS" : 768,
    "VLM_MODEL": {
        "LLAMACPPPYTHON": "https://huggingface.co/NexaAI/Qwen3-VL-4B-Instruct-GGUF/blob/main/Qwen3-VL-4B-Instruct.Q4_K.gguf",
        "MLXCOMMUNITY": "mlx-community/Qwen3-VL-4B-Instruct-3bit",
    },
    "VLM_MAX_CONTEXT_LENGTH": 256*1024,
    "VLM_MAX_OUTPUT_TOKENS": 2048,
}

# 测试用本地SQLite数据库路径
PATH = Path(__file__).parent.parent
TEST_DB_PATH = (PATH / "autobox_id.db").as_posix()

# 单例
def singleton(cls):
    instances = {}    
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

# 生成短ID的工具函数
def generate_vector_id() -> str:
    """生成用于vector_id的短ID"""
    return str(uuid4()).replace('-', '')[:16]