from core.config import singleton, BUILTMODELS
import os
import re
import json
import uuid
import time
from pathlib import Path
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy import Engine
from pydantic import BaseModel, Field, ValidationError
from core.agno.agent import Agent
from core.agno.tools.function import Function as Tool
from core.agno.media import Image as BinaryContent
# from pydantic_ai.usage import UsageLimits
from core.agent.model_config_mgr import ModelConfigMgr, ModelUseInterface
from core.models_builtin import load_embedding_model
from core.agent.memory_mgr import MemoryMgr
from core.agent.tool_provider import ToolProvider
from huggingface_hub import snapshot_download
from tqdm import tqdm

logger = logging.getLogger()

# 定义一个可以在运行时创建的 BridgeProgressReporter 类
def create_bridge_progress_reporter(bridge_events, model_name):
    """
    动态创建带有bridge events的tqdm子类
    
    这个工厂函数解决了在类方法内部创建子类时的作用域问题。
    """    
    class BridgeProgressReporter(tqdm):
        """
        继承自真正的tqdm类，确保完全兼容
        """
        
        def __init__(self, *args, **kwargs):
            # 注入我们的自定义参数
            self.bridge_events = bridge_events
            self.model_name = model_name
            
            # 调用父类初始化
            super().__init__(*args, **kwargs)
            
            # 发送开始事件
            if self.bridge_events and not self.disable:
                self.bridge_events.model_download_progress(
                    model_name=self.model_name,
                    current=0,
                    total=self.total or 0,
                    message=f"开始下载 {self.model_name}",
                    stage="downloading"
                )
        
        def update(self, n=1):
            """重写update方法，添加bridge events"""
            # 调用父类的update方法
            result = super().update(n)
            
            # 发送进度事件
            if self.bridge_events and not self.disable:
                # 格式化消息
                if self.unit_scale and self.unit == 'B':
                    # 自动缩放字节单位
                    current_mb = self.n / (1024 * 1024)
                    total_mb = self.total / (1024 * 1024) if self.total and self.total > 0 else 0
                    message = f"{self.desc}: {current_mb:.1f}MB/{total_mb:.1f}MB"
                else:
                    message = f"{self.desc}: {self.n}/{self.total or '?'}"
                
                self.bridge_events.model_download_progress(
                    model_name=self.model_name,
                    current=self.n,
                    total=self.total or 0,
                    message=message,
                    stage="downloading"
                )
            
            return result
        
        def close(self):
            """重写close方法，发送完成事件"""
            # 发送完成事件
            if self.bridge_events and not self.disable:
                self.bridge_events.model_download_progress(
                    model_name=self.model_name,
                    current=self.n,
                    total=self.total or self.n,
                    message=f"{self.model_name} 下载完成",
                    stage="completed"
                )
            
            # 调用父类的close方法
            return super().close()
    
    return BridgeProgressReporter

@singleton
class ModelsMgr:
    def __init__(self, engine: Engine, base_dir: str):
        self.engine = engine
        self.base_dir = base_dir
        self.model_config_mgr = ModelConfigMgr(engine)
        self.tool_provider = ToolProvider(engine)
        self.memory_mgr = MemoryMgr(engine)

    def get_embedding(self, text_str: str) -> List[float]:
        """
        Generates an embedding for the given text using sync OpenAI client.
        
        This is typically called by backend processes (document parsing, vectorization),
        so model validation failures will trigger IPC events to notify the frontend.
        """
        model_path = self.model_config_mgr.get_embeddings_model_path()
        if model_path == "":
            model_path = self.download_huggingface_model(BUILTMODELS['EMBEDDING_MODEL']['MLXCOMMUNITY'], self.base_dir)
            self.model_config_mgr.set_embeddings_model_path(model_path)        
        try:
            model, tokenizer = load_embedding_model(model_path)
            
            # 使用批处理编码并指定参数
            if hasattr(tokenizer, 'batch_encode_plus'):
                inputs = tokenizer.batch_encode_plus(
                    [text_str], 
                    return_tensors="mlx", 
                    padding=True, 
                    truncation=True, 
                    max_length=512
                )
                input_ids = inputs["input_ids"]
                attention_mask = inputs.get("attention_mask", None)
            else:
                input_ids = tokenizer.encode(text_str, return_tensors="mlx")
                attention_mask = None
                
            # 调用模型时提供attention_mask参数（如果可用）
            if attention_mask is not None:
                outputs = model(input_ids, attention_mask=attention_mask)
            else:
                outputs = model(input_ids)
                
            # raw_embeds = outputs.last_hidden_state[:, 0, :] # CLS token
            text_embeds = outputs.text_embeds # mean pooled and normalized embeddings
            return text_embeds[0].tolist()
        except Exception as e:
            logger.error(f"Error on load embedding model or generating embeddings: {e}")
            return []

    async def get_tags_from_llm(self, file_path: str, file_summary: str, candidate_tags: List[str]) -> List[str]:
        """
        Generates tags from the LLM using instructor and litellm.
        
        This is typically called by backend processes (file processing, tagging),
        so model validation failures will trigger IPC events to notify the frontend.
        """

        class TagResponse(BaseModel):
            tags: List[str] = Field(default_factory=list, description="List of generated tags")
        
        try:
            model_interface: ModelUseInterface = self.model_config_mgr.get_structured_output_model_config()
        except Exception as e:
            logger.error(f"Failed to get structured output model config: {e}")
            return []
        model = self.model_config_mgr.model_adapter(model_interface)
        # System prompt 明确要求返回纯 JSON，不要 markdown 代码块
        system_prompt = """
You are an expert AI data curator for a desktop knowledge management app named "Leaf Know". Your mission is to analyze file information and generate a refined, consistent, and structured set of tags that are optimized for future retrieval and organization.

# CRITICAL OUTPUT REQUIREMENT
YOU MUST ONLY OUTPUT RAW JSON WITHOUT ANY MARKDOWN CODE BLOCKS.
DO NOT wrap your response in ```json or ``` tags.
DO NOT include ANY explanatory text before or after the JSON.
ONLY output the JSON object itself.

# ABSOLUTELY CRITICAL TAG LIMITS
- You MUST generate EXACTLY 3 to 7 tags. NO MORE, NO LESS.
- NEVER repeat the same tag multiple times.
- Each tag must be UNIQUE and DISTINCT.

# CONTEXT PROVIDED

You will be given three pieces of information to perform your task:
1.  **File Path**: The full path to the file. This often contains invaluable context like project names, dates, or categories that may not be present in the content itself.
2.  **Content Summary**: The first few thousand characters of the file's text content.
3.  **Candidate Tags**: An AI-generated list of suggested tags based on vector similarity to other files. These are intelligent suggestions that require your expert review.

# CORE INSTRUCTIONS: Your Cognitive Workflow

You must follow this four-step cognitive process to arrive at the final, high-quality tags.

---

### Step 1: Holistic Analysis
First, synthesize your understanding by thoroughly examining BOTH the `File Path` and the `Content Summary`. Form a comprehensive mental model of what the file is about, its purpose, and its context.

---

### Step 2: Candidate Curation & Refinement (Crucial Step)
This is where your expertise shines. Scrutinize the `Candidate Tags` list not as a command, but as a draft needing an editor.

* **EVALUATE & SELECT**: For each candidate tag, determine if it accurately and importantly represents a core concept of the file.
* **MERGE & UNIFY**: If multiple candidates are semantically similar (e.g., synonyms, abbreviations, plural/singular forms like "Web Dev", "Web Development"), merge them into a single, most standard, and representative tag (e.g., `Web_Development`).
* **REFINE**: If a candidate is relevant but imprecise, refine it to be more specific or accurate based on the file's context. For example, a candidate "API" might be refined to "API_Design" if the content is about specifications.
* **DISCARD**: You MUST discard any candidate tags that are irrelevant, too generic, or redundant after merging.

---

### Step 3: Conceptual Creation
After curating the candidates, identify any core conceptual gaps. If a major theme or category of the file is still not represented, create 1 to 3 new, high-level tags to fill these gaps. These new tags should represent a significant aspect that the curated candidates missed.

---

### Step 4: Finalization & Formatting
Assemble the final list of tags from Step 2 and Step 3. Before outputting, ensure the list adheres to these strict final rules:

* **Quantity**: The final list must contain between 3 and 7 tags. NEVER MORE THAN 7 TAGS.
* **Uniqueness**: Each tag MUST be unique. NEVER repeat the same tag multiple times. Check for duplicates before finalizing.
* **Language & Terminology**:
    * The tag language MUST match the dominant language of the `Content Summary`.
    * If Chinese characters are present, all tags MUST be in Chinese.
    * Globally recognized technical acronyms (e.g., API, CPU, RAG, AI, LLM) MUST be preserved in their original English uppercase form, even within Chinese tags (e.g., `AI模型`, `RAG应用`).
* **Formatting**:
    * All multi-word English tags MUST use a single underscore `_` as a separator (e.g., `Project_Management`).
    * Hyphens `-` that are part of a word must be preserved (e.g., `Man-in-the-Loop`).
    * Absolutely NO generic tags like "File", "Document", "Text", "资料", "文档".
    * Ensure there are no leading/trailing spaces or punctuation around the tags.

# OUTPUT FORMAT

YOU MUST respond ONLY with raw JSON. NO MARKDOWN CODE BLOCKS.
Do not wrap your output in ```json or ```.
Do not include ANY explanatory text before or after the JSON.

**Example Input (User Prompt):**
* File Path: `/Users/Admin/Work/Project_KF/specs/2025-09-02_后端API设计草案.md`
* Content Summary: `# KF 后端 API 规范 (草案)... 主要实体是文件(Files), 标签(Tags)... 我们将使用 FastAPI...`
* Candidate Tags: `["API", "Knowledge-Focus", "Database", "草稿"]`

**Your Correct and ONLY Output (RAW JSON, NO MARKDOWN):**
{
  "tags": [
    "API设计",
    "Knowledge-Focus",
    "后端",
    "草稿"
  ]
}
""".strip()
        user_prompt = self._build_tagging_prompt(file_path, file_summary, candidate_tags)
        
        # 用于记录每次验证尝试的原始响应
        validation_attempts = []
        
        agent = Agent(
            model=model,
            instructions=system_prompt,
        )

        try:
            if model_interface.model_identifier == BUILTMODELS['VLM_MODEL']['MLXCOMMUNITY']:
                # For mlx models, use regular text approach
                response = await agent.arun(user_prompt)
                if hasattr(response, 'content') and response.content:
                    # Try to parse JSON from content
                    try:
                        import json
                        result_data = json.loads(response.content)
                        tags = result_data.get('tags', [])
                    except:
                        # Fallback: simple text processing for mlx models
                        tags = user_prompt.split()[:5]  # Simple fallback
                else:
                    tags = []
            else:
                # For other models, use structured output
                response = await agent.arun(user_prompt, response_format=TagResponse)
                if hasattr(response, 'content'):
                    # Parse structured response
                    try:
                        import json
                        result_data = json.loads(response.content) if isinstance(response.content, str) else response.content
                        tags = result_data.get('tags', []) if isinstance(result_data, dict) else []
                    except:
                        tags = []
                else:
                    tags = []

            logger.info(f"Tag generation successful: {tags}")
        except Exception as e:
            logger.error(f"Unexpected error during tag generation: {e}")
            import traceback
            logger.error(f"Error details:\n{traceback.format_exc()}")
            return []

        # 把每个tag中间可能的空格替换为下划线，因为要避开英语中用连字符作为合成词的情况
        tags = [tag.replace(" ", "_") for tag in tags if isinstance(tag, str)]
        # 把每个tag前后的非字母数字字符去掉
        tags = [re.sub(r"^[^\w]+|[^\w]+$", "", tag) for tag in tags]
        return tags

    async def generate_session_title(self, first_message_content: str) -> str:
        """
        Generate an intelligent session title based on the first user message.
        
        This method is typically called by backend processes (session creation),
        and uses a non-streaming approach for title generation.
        
        Args:
            first_message_content: The first user message content
            
        Returns:
            Generated session title (max 20 characters)
        """
        
        class SessionTitleResponse(BaseModel):
            title: str = Field(description="Generated session title (max 20 characters)")
        
        try:
            model_interface: ModelUseInterface = self.model_config_mgr.get_text_model_config()
    
        except Exception as e:
            logger.error(f"Failed to get model config: {e}")
            return "new chat"
        model = self.model_config_mgr.model_adapter(model_interface)
        messages = [
            {"role": "system", "content": "You are an expert at creating concise, meaningful titles. Generate a short title (max 20 characters) that captures the essence of the user's request or question."},
            {"role": "user", "content": self._build_title_prompt(first_message_content)}
        ]
        agent = Agent(
            model=model,
            instructions=messages[0]['content'],
        )
        try:
            if model_interface.model_identifier == BUILTMODELS['VLM_MODEL']['MLXCOMMUNITY']:
                # For mlx models, use regular text approach
                response = await agent.arun(messages[1]['content'])
                if hasattr(response, 'content'):
                    title = response.content.strip()
                else:
                    title = ""
            else:
                # For other models, use structured output
                response = await agent.arun(messages[1]['content'], response_format=SessionTitleResponse)
                if hasattr(response, 'content'):
                    # Parse structured response
                    try:
                        import json
                        result_data = json.loads(response.content) if isinstance(response.content, str) else response.content
                        title = result_data.get('title', '') if isinstance(result_data, dict) else response.content
                    except:
                        title = response.content if response.content else ""
                else:
                    title = ""

            title = str(title).strip()

            # 确保标题长度不超过20个字符
            if len(title) > 20:
                title = title[:17] + "..."

            return title if title else "new chat"

        except Exception as e:
            logger.error(f"Failed to generate session title: {e}")
            # 降级处理：使用简单截取方式
            fallback_title = first_message_content.strip()[:17]
            if len(first_message_content) > 17:
                fallback_title += "..."
            return fallback_title or "new chat"

    def _build_title_prompt(self, first_message: str) -> str:
        """Build prompt for session title generation"""
        return f'''
Please create a concise and meaningful title for a chat session based on the user's first message.

**Requirements:**
1. **Length:** Maximum 20 characters (including Chinese characters, English letters, numbers, and symbols)
2. **Language:** Use the same language as the user's message (Chinese for Chinese input, English for English input)
3. **Content:** Capture the main topic or intent of the user's question/request
4. **Style:** Clear, descriptive, and professional
5. **Special Cases:** For simple greetings like "你好", "hello", use generic titles like "新对话", "New chat"

**User's First Message:**
---
{first_message}
---

Generate a title that best represents what this conversation will be about. Avoid overly specific titles for vague or greeting-only messages.
        '''

    def _build_tagging_prompt(self, file_path: str, summary: str, candidates: List[str]) -> str:
        """
        Builds a clean and structured user prompt containing the raw data for the tagging task.
        The Agent's system_prompt contains all the instructions.
        """
        # Format candidates for clear presentation
        candidate_str = ", ".join(f'"{t}"' for t in candidates) if candidates else "None provided."
        
        # Use f-string with clear markers for the model to parse
        return f"""
    --- Contextual Information ---
    File Path: {file_path}

    --- Candidate Tags (Reuse these if possible) ---
    [{candidate_str}]

    --- File Content Summary to Analyze ---
    {summary}

    ---

    Based on all the provided information and your system instructions, generate the tags for this file.
    """

    def get_chat_completion(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get a single chat completion response (non-streaming).
        
        This method can be used for both backend processing and frontend requests.
        For frontend-initiated requests, consider using silent_validation=True
        to let the frontend handle errors directly via HTTP responses.
        
        Args:
            messages: Chat messages
            role_type: Model role type
            
        Returns:
            The completion response as a string
        """
        try:
            model_interface = self.model_config_mgr.get_text_model_config()
        except Exception as e:
            logger.error(f"Failed to get model config: {e}")
            return ""
        model = self.model_config_mgr.model_adapter(model_interface)
        try:
            system_prompt = [msg['content'] for msg in messages if msg['role'] == 'system']
            # logger.info(f"System prompt for chat completion: {system_prompt}")
            agent = Agent(
                model=model,
                system_prompt=system_prompt[0] if system_prompt else "",
            )
            
            # 处理用户输入 - 兼容AI SDK v5的parts格式
            user_prompt_texts = []
            for msg in messages:
                if msg['role'] == 'user':
                    # 优先从parts中提取文本内容
                    content_text = ""
                    if "parts" in msg:
                        for part in msg["parts"]:
                            if part.get("type") == "text":
                                content_text += part.get("text", "")
                    
                    # 备用：检查传统的content字段
                    if not content_text:
                        content_text = msg.get("content", "")
                    
                    if content_text.strip():
                        user_prompt_texts.append(content_text.strip())
            
            if user_prompt_texts == []:
                raise ValueError("User prompt is empty")
            response = agent.run_sync(
                user_prompt=user_prompt_texts[0],
                # usage_limits=UsageLimits(output_tokens_limit=50),
            )
            return response.output
        except Exception as e:
            logger.error(f"Failed to get chat completion: {e}")
            raise ValueError("Failed to get chat completion")

    async def stream_agent_chat_v5_compatible(self, messages: List[Dict], session_id: int):
        """
        创建一个符合Vercel AI SDK v5 UI Message Stream格式的流响应生成器

        简化版本，避免复杂的流式处理逻辑
        """
        try:
            logger.info(f"Agent chat v5_compatible invoked for session_id: {session_id}")

            # 先预检查消息中是否包含图片，以确定使用哪种模型配置
            has_images = False
            for msg in messages:
                if msg['role'] == 'user' and "parts" in msg:
                    for part in msg["parts"]:
                        if part.get("type") == "file" and part.get("mediaType", "").startswith("image/"):
                            has_images = True
                            break
                if has_images:
                    break

            # 根据是否包含图片选择合适的模型配置
            if has_images:
                # logger.info("检测到图片消息，使用视觉模型配置")
                model_interface: ModelUseInterface = self.model_config_mgr.get_vision_model_config()
            else:
                # logger.info("纯文本消息，使用文本模型配置")
                model_interface: ModelUseInterface = self.model_config_mgr.get_text_model_config()

            if model_interface is None:
                error_msg = "can't use vision model" if has_images else "can't use text model"
                error_msg = f"{error_msg}, please check model configuration"
                logger.error(error_msg)
                yield f'data: {json.dumps({"type": "error", "errorText": error_msg})}\n\n'
                return

            model = self.model_config_mgr.model_adapter(model_interface)

            # 准备工具
            tools = [Tool(tool, takes_ctx=True) for tool in self.tool_provider.get_tools_for_session(session_id)]
            logger.info(f"当前工具数: {len(tools)}")

            # 构建系统prompt
            system_prompt = ["You are a helpful assistant."]
            # 加载场景相关的系统prompt
            scenario_system_prompt = self.tool_provider.get_session_scenario_system_prompt(session_id)
            system_prompt.append(scenario_system_prompt) if scenario_system_prompt is not None else None

            # 处理用户输入 - 兼容AI SDK v5的parts格式
            user_prompt = ""
            for msg in messages:
                if msg['role'] == 'user':
                    # 优先从parts中提取文本内容
                    if "parts" in msg:
                        for part in msg["parts"]:
                            if part.get("type") == "text":
                                user_prompt += part.get("text", "")
                    # 备用：检查传统的content字段
                    if not user_prompt:
                        user_prompt = msg.get("content", "")

            if not user_prompt.strip():
                yield f'data: {"type": "error", "errorText": "User prompt is empty"}\n\n'
                return

            # 创建agent
            agent = Agent(
                model=model,
                tools=tools,
                system_prompt=system_prompt,
            )

            # 使用agent.run_sync获取完整响应，然后模拟流式输出
            response = agent.run_sync(user_prompt=user_prompt)

            if response and hasattr(response, 'output'):
                content = response.output
                # 模拟流式输出
                part_id = f"msg_{uuid.uuid4().hex}"
                yield f'data: {json.dumps({"type": "text-start", "id": part_id})}\n\n'

                # 分块输出内容
                chunk_size = 10
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    data = {
                        "type": "text-delta",
                        "id": part_id,
                        "delta": chunk
                    }
                    yield f'data: {json.dumps(data)}\n\n'

                yield f'data: {json.dumps({"type": "text-end", "id": part_id})}\n\n'

            # 结束事件
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"Error in stream_agent_chat_v5_compatible: {e}")
            yield f'data: {json.dumps({"type": "error", "errorText": str(e)})}\n\n'

    def download_huggingface_model(self, model_id: str, cache_dir: str = None) -> str:
        """
        下载指定的huggingface模型到本地
        
        Args:
            model_id: HuggingFace模型ID，如 'BAAI/bge-small-zh-v1.5'
            cache_dir: 缓存目录，默认使用HuggingFace默认目录
            
        Returns:
            str: 下载后的本地模型路径
            
        Raises:
            Exception: 下载过程中的其他错误
        """
        
        max_attempts_per_endpoint = 3
        endpoints = ['https://huggingface.co', 'https://hf-mirror.com']
        last_exception = None

        for endpoint in endpoints:
            for attempt in range(max_attempts_per_endpoint):
                try:
                    # 使用工厂函数创建自定义的tqdm子类
                    ProgressReporter = create_bridge_progress_reporter(
                        bridge_events=self.bridge_events,
                        model_name=model_id
                    )            
                    # 使用snapshot_download下载模型
                    local_path = snapshot_download(
                        repo_id=model_id,
                        cache_dir=cache_dir,
                        tqdm_class=ProgressReporter,
                        allow_patterns=["*.safetensors", "*.json", "*.txt"],  # 只下载需要的文件
                        endpoint=endpoint, # 添加endpoint参数
                    )
                    # 发送完成事件
                    self.bridge_events.model_download_completed(
                        model_name=model_id,
                        local_path=local_path,
                        message=f"模型 {model_id} 下载完成"
                    )
                    return local_path
                except Exception as e:
                    last_exception = e
                    error_msg = f"下载模型失败 (尝试 {attempt + 1}/{max_attempts_per_endpoint}，镜像站: {endpoint}): {str(e)}"
                    logger.warning(f"下载模型 {model_id} 失败: {e}", exc_info=True)
                    # 发送失败事件，但不是最终失败，只是单次尝试失败
                    self.bridge_events.model_download_progress(
                        model_name=model_id,
                        current=0,
                        total=0,
                        message=f"下载失败 (尝试 {attempt + 1}/{max_attempts_per_endpoint}，镜像站: {endpoint})",
                        stage="failed_attempt"
                    )
                    time.sleep(2) # 等待2秒后重试

            logger.error(f"镜像站 {endpoint} 下载模型 {model_id} 失败，已达到最大重试次数 {max_attempts_per_endpoint}。")

        # 如果所有镜像站和所有尝试都失败了
        error_msg = f"所有镜像站下载模型 {model_id} 均失败: {str(last_exception)}"
        logger.error(error_msg, exc_info=True)
        # 发送最终失败事件
        self.bridge_events.model_download_failed(
            model_name=model_id,
            error_message=error_msg,
            details={"exception_type": type(last_exception).__name__ if last_exception else "UnknownError"}
        )            
        return ""

    def _get_rag_context(self, session_id: int, user_query: str, available_tokens: int) -> Tuple[str, list]:
        """
        获取RAG上下文和来源信息
        
        Args:
            session_id: 会话ID  
            user_query: 用户查询内容
            available_tokens: 可用token数量
            
        Returns:
            tuple: (rag_context_text, rag_sources_list)
        """
        try:
            # 获取会话Pin文件对应的文档ID
            from core.agent.chatsession_mgr import ChatSessionMgr
            chat_mgr = ChatSessionMgr(self.engine)
            document_ids = chat_mgr.get_pinned_document_ids(session_id)
            
            if not document_ids:
                logger.debug(f"会话 {session_id} 没有Pin文档，跳过RAG")
                return "", []
            
            # 使用SearchManager进行检索
            from core.agent.lancedb_mgr import LanceDBMgr
            lancedb_mgr = LanceDBMgr(base_dir=self.base_dir)
            from core.agent.search_mgr import SearchManager
            search_mgr = SearchManager(
                engine=self.engine, 
                lancedb_mgr=lancedb_mgr, 
                models_mgr=self
            )
            # 执行搜索，限制在Pin的文档内
            search_response = search_mgr.search_documents(
                query=user_query,
                top_k=5,  # 取前5个最相关的片段
                document_ids=document_ids  # 限制搜索范围
            )
            
            # 检查搜索是否成功
            if not search_response or not search_response.get('success', False):
                error_msg = search_response.get('error', '未知错误') if search_response else '搜索响应为空'
                logger.debug(f"RAG检索失败: {error_msg}")
                return "", []
            
            # 获取实际的搜索结果
            search_results = search_response.get('raw_results', [])
            if not search_results:
                logger.debug(f"RAG检索无结果，查询: {user_query[:50]}...")
                return "", []
            
            logger.debug(f"RAG检索到 {len(search_results)} 个结果")
            if search_results:
                logger.debug(f"首个结果字段: {list(search_results[0].keys())}")
            
            # 构建RAG上下文文本
            context_parts = []
            sources = []
            
            for result in search_results:
                # 限制每个片段的长度，避免token超限
                content = result.get('retrieval_content', '')[:1000]  # 限制1000字符
                
                # 将distance转换为相似度百分比 (1 - normalized_distance)
                distance = result.get('_distance', 1.0)  # 修正字段名
                # 假设distance在0-2之间，转换为相似度百分比
                similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                
                source_info = {
                    'chunk_id': result.get('child_chunk_id', ''),
                    'file_path': result.get('file_path', ''),
                    'similarity_score': similarity_score,  # 使用转换后的相似度
                    'content': content,
                    'metadata': result.get('metadata', {})
                }
                
                context_parts.append(f"**来源**: {result.get('file_path', '未知文件')}\n{content}")
                sources.append(source_info)
            
            rag_context = "\n\n".join(context_parts)
            
            logger.info(f"RAG成功检索 {len(sources)} 个片段，总长度: {len(rag_context)} 字符")
            return rag_context, sources
            
        except Exception as e:
            logger.error(f"RAG检索失败: {e}", exc_info=True)
            return "", []

    def _send_rag_to_observation_window(self, rag_sources: list, user_query: str):
        """
        通过桥接器发送RAG数据到知识观察窗
        
        Args:
            rag_sources: RAG检索的来源列表
            user_query: 用户查询内容
        """
        try:
            if not rag_sources:
                return
                
            # 构建发送给观察窗的数据
            observation_data = {
                "timestamp": int(time.time() * 1000),
                "query": user_query[:200],  # 限制查询长度
                "sources_count": len(rag_sources),
                "sources": [
                    {
                        "file_path": source.get('file_path', ''),
                        "similarity_score": round(source.get('similarity_score', 0.0), 3),
                        "content_preview": source.get('content', '')[:300],  # 内容预览
                        "chunk_id": source.get('chunk_id'),
                        "metadata": source.get('metadata', {})
                    }
                    for source in rag_sources
                ],
                "event_type": "rag_retrieval"
            }
            
            # 通过桥接器发送事件
            self.bridge_events.send_event("rag-retrieval-result", observation_data)
            
            logger.debug(f"RAG观察数据已发送: {len(rag_sources)} 个来源")
            
        except Exception as e:
            logger.error(f"发送RAG观察数据失败: {e}", exc_info=True)

    # def cosine_similarity_list_input(self, a: List[float], b: List[float]) -> float:
    #     """
    #     计算两个List[float]（向量）之间的余弦相似度。

    #     Args:
    #         a: 第一个输入列表（表示向量）。
    #         b: 第二个输入列表（表示向量）。

    #     Returns:
    #         一个浮点数，表示输入向量之间的余弦相似度。
    #         如果任一向量为零向量，则返回 0.0。
    #     """
    #     # 将 List[float] 转换为 mlx.core.array
    #     vec_a = mx.array(a)
    #     vec_b = mx.array(b)

    #     # 计算点积
    #     # mlx.core.sum(vec_a * vec_b) 会将所有元素相乘后求和，等同于向量点积
    #     dot_product = mx.sum(vec_a * vec_b)

    #     # 计算L2范数（magnitude）
    #     norm_a = mx.linalg.norm(vec_a)
    #     norm_b = mx.linalg.norm(vec_b)

    #     # 避免除以零：如果任一范数为零，则相似度为零
    #     denominator = norm_a * norm_b
        
    #     # 使用mx.where处理除以零的情况。
    #     # 如果denominator不为0，则执行 dot_product / denominator，否则返回0.0。
    #     # 由于我们期望返回一个浮点数，这里直接取其item()。
    #     # 注意：如果处理批量数据，通常不会用.item()。但对于两个单一向量，这是合适的。
    #     similarity = mx.where(denominator != 0, dot_product / denominator, mx.array(0.0)).item()
        
    #     return float(similarity)

    async def coreading_v5_compatible(self, messages: List[Dict], session_id: int):
        """
        [临时方案] 提供给"共读"模型的stream接口，兼容AI SDK v5协议。

        简化版本，避免复杂的流式处理逻辑
        """
        try:
            model_interface: ModelUseInterface = self.model_config_mgr.get_vision_model_config()
            if model_interface is None:
                error_msg = "can't use vision model"
                logger.error(error_msg)
                yield f'data: {json.dumps({"type": "error", "errorText": error_msg})}\n\n'
                return

            model = self.model_config_mgr.model_adapter(model_interface)

            # 构建系统prompt
            system_prompt = self.tool_provider.get_session_scenario_system_prompt(session_id)

            # 处理用户输入 - 兼容AI SDK v5的parts格式
            user_prompt = ""
            for msg in messages:
                if msg['role'] == 'user':
                    # 优先从parts中提取文本内容
                    if "parts" in msg:
                        for part in msg["parts"]:
                            if part.get("type") == "text":
                                user_prompt += part.get("text", "")
                    # 备用：检查传统的content字段
                    if not user_prompt:
                        user_prompt = msg.get("content", "")

            if not user_prompt.strip():
                yield f'data: {"type": "error", "errorText": "User prompt is empty"}\n\n'
                return

            # 创建agent
            agent = Agent(
                model=model,
                system_prompt=system_prompt,
            )

            # 使用agent.run_sync获取完整响应，然后模拟流式输出
            response = agent.run_sync(user_prompt=user_prompt)

            if response and hasattr(response, 'output'):
                content = response.output
                # 模拟流式输出
                part_id = f"msg_{uuid.uuid4().hex}"
                yield f'data: {json.dumps({"type": "text-start", "id": part_id})}\n\n'

                # 分块输出内容
                chunk_size = 10
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    data = {
                        "type": "text-delta",
                        "id": part_id,
                        "delta": chunk
                    }
                    yield f'data: {json.dumps(data)}\n\n'

                yield f'data: {json.dumps({"type": "text-end", "id": part_id})}\n\n'

            # 结束事件
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            yield 'data: [DONE]\n\n'

        except Exception as e:
            logger.error(f"Error in coreading_v5_compatible: {e}")
            yield f'data: {json.dumps({"type": "error", "errorText": str(e)})}\n\n'

# for testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        # format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(stream=sys.stdout)]
    )

    from core.config import TEST_DB_PATH
    from sqlmodel import create_engine
    engine = create_engine(f'sqlite:///{TEST_DB_PATH}')
    mgr = ModelsMgr(engine, base_dir=Path(TEST_DB_PATH).parent)

    # # Test get TEXT model interface
    # model_interface = mgr.model_config_mgr.get_text_model_config()
    # print(model_interface.model_dump())
    

    # Test embedding generation
    # embedding = mgr.get_embedding("北京是中国的首都，拥有丰富的历史和文化。")
    # print("Embedding Length:", len(embedding))
    
    # # Test tag generation
    # tags = mgr.get_tags_from_llm("北京是中国的首都，拥有丰富的历史和文化。", ["北京", "首都"])
    # print("Generated Tags:", tags)
        
    # # test generate title
    # title = mgr.generate_session_title('你好，我想了解一下人工智能的发展历史')
    # print('Generated title:', title)
    
    # Test chat completion
    try:
        chat_response = mgr.get_chat_completion([
            {"role": "user", "content": "尽量列举一些首都城市的名字"}
        ])
        print("Chat Response:", chat_response)
    except Exception as e:
        print("Chat Error:", e)

    # # test stream
    # import asyncio
    # async def test_stream():
    #     messages = [
    #         {'role': 'user', 'content': '今天的谷歌股价是多少？'}
    #     ]
        
    #     print('Testing Vercel AI SDK compatible stream protocol:')
    #     print('=' * 50)

    #     async for chunk in mgr.stream_agent_chat_v5_compatible(messages, session_id=1):
    #         # print(chunk, end='')
    #         try:
    #             print(json.dumps(json.loads(chunk.lstrip('data: ')), ensure_ascii=False), end='')
    #         except Exception as e:
    #             print(f"Error processing chunk: {e}")
    #             pass
    # asyncio.run(test_stream())

    # # 下载MLX优化的Qwen3 Embedding模型
    # import os
    # cache_dir = os.path.dirname(TEST_DB_PATH)
    # path = mgr.download_embedding_model(EMBEDDING_MODEL, cache_dir)
    # print(path)
    
    # # === RAG测试代码 ===
    # print("\n" + "="*50)
    # print("测试RAG检索结果和相似度计算")
    # print("="*50)
    
    # # 测试会话ID=18的RAG检索
    # session_id = 18
    # user_query = "Manus项目有哪些经验教训？"
    # available_tokens = 2000
    
    # print(f"测试查询: {user_query}")
    # print(f"会话ID: {session_id}")
    
    # try:
    #     rag_context, rag_sources = mgr._get_rag_context(session_id, user_query, available_tokens)
        
    #     print("\n检索结果:")
    #     print(f"- 上下文长度: {len(rag_context)} 字符")
    #     print(f"- 来源数量: {len(rag_sources)}")
        
    #     if rag_sources:
    #         print("\n详细来源信息:")
    #         for i, source in enumerate(rag_sources):
    #             print(f"\n[来源 {i+1}]")
    #             print(f"  文件: {source.get('file_path', 'Unknown')}")
    #             print(f"  相似度分数: {source.get('similarity_score', 0.0)}")
    #             print(f"  内容长度: {len(source.get('content', ''))}")
    #             print(f"  内容预览: {source.get('content', '')[:200]}...")
                
    #             # 如果有原始distance数据，也显示出来
    #             if 'raw_distance' in source:
    #                 print(f"  原始距离: {source.get('raw_distance')}")
        
    #     # 同时测试SearchManager的原始返回
    #     print("\n" + "-"*30)
    #     print("原始SearchManager返回数据:")
        
    #     from core.chatsession_mgr import ChatSessionMgr
    #     chat_mgr = ChatSessionMgr(engine)
    #     document_ids = chat_mgr.get_pinned_document_ids(session_id)
    #     print(f"Pin的文档ID: {document_ids}")
        
    #     if document_ids:
    #         from core.lancedb_mgr import LanceDBMgr
    #         from core.search_mgr import SearchManager
            
    #         lancedb_mgr = LanceDBMgr(base_dir=base_dir)

    #         search_mgr = SearchManager(
    #             engine=engine, 
    #             lancedb_mgr=lancedb_mgr, 
    #             models_mgr=mgr
    #         )
            
    #         search_response = search_mgr.search_documents(
    #             query=user_query,
    #             top_k=5,
    #             document_ids=document_ids
    #         )
            
    #         if search_response and search_response.get('success'):
    #             raw_results = search_response.get('raw_results', [])
    #             print(f"原始结果数量: {len(raw_results)}")
                
    #             if raw_results:
    #                 print(f"\n首个原始结果字段: {list(raw_results[0].keys())}")
                    
    #                 for i, result in enumerate(raw_results[:3]):  # 只显示前3个
    #                     print(f"\n[原始结果 {i+1}]")
    #                     print(f"  所有字段: {result}")
                        
    #                     distance = result.get('distance', 'N/A')
    #                     print(f"  原始distance: {distance}")
                        
    #                     # 使用相同的转换公式
    #                     if isinstance(distance, (int, float)):
    #                         similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
    #                         print(f"  转换后相似度: {similarity_score} ({similarity_score*100:.1f}%)")
    #         else:
    #             print(f"搜索失败: {search_response.get('error', '未知错误') if search_response else '无响应'}")
                
    # except Exception as e:
    #     print(f"RAG测试失败: {e}")
    #     import traceback
    #     traceback.print_exc()
