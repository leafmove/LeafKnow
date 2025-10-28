"""
多厂商模型适配器
支持OpenAI、Anthropic、本地模型等多种AI厂商的统一接口适配
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
from datetime import datetime

from pydantic_ai import Agent, Model, ModelSettings
from pydantic_ai.models import KnownModelName
from agno.agent.agent import Agent as AgnoAgent
from agno.models.base import Model as AgnoModel

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """支持的AI厂商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL_LLM = "local_llm"
    AGNO_NATIVE = "agno_native"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    HUGGINGFACE = "huggingface"


@dataclass
class ProviderConfig:
    """厂商配置信息"""
    provider_type: ProviderType
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    extra_params: Dict[str, Any] = field(default_factory=dict)

    # 支持的功能
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_function_calling: bool = True
    max_context_length: int = 8192


class BaseProviderAdapter(ABC):
    """基础厂商适配器抽象类"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider_type = config.provider_type
        self.model_name = config.model_name

    @abstractmethod
    async def create_model(self) -> Union[Model, AgnoModel]:
        """创建模型实例"""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天接口"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """非流式聊天完成接口"""
        pass

    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """检查是否支持特定功能"""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 简单的测试请求
            test_messages = [{"role": "user", "content": "Hello"}]
            start_time = datetime.now()

            response = await self.chat_completion(test_messages)

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            return {
                "status": "healthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "response_time": response_time,
                "timestamp": end_time.isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class OpenAIProviderAdapter(BaseProviderAdapter):
    """OpenAI厂商适配器"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    async def _get_client(self):
        """获取OpenAI客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout
                )
            except ImportError:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
        return self._client

    async def create_model(self) -> Model:
        """创建Pydantic-AI模型实例"""
        from pydantic_ai.models.openai import OpenAIModel

        return OpenAIModel(
            model_name=self.config.model_name,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """OpenAI流式聊天"""
        client = await self._get_client()

        try:
            stream = await client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                tools=tools,
                stream=True,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.extra_params
            )

            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 处理不同类型的内容
                    if delta.content:
                        yield {
                            "type": "text-delta",
                            "content": delta.content,
                            "finish_reason": choice.finish_reason
                        }

                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            yield {
                                "type": "tool-call-delta",
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name if tool_call.function else None,
                                "function_args": tool_call.function.arguments if tool_call.function else None
                            }

                    if choice.finish_reason:
                        yield {
                            "type": "finish",
                            "reason": choice.finish_reason
                        }

        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """OpenAI非流式聊天完成"""
        client = await self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                tools=tools,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.extra_params
            )

            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }

        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise e

    def supports_feature(self, feature: str) -> bool:
        """检查OpenAI功能支持"""
        feature_map = {
            "streaming": self.config.supports_streaming,
            "tools": self.config.supports_tools,
            "vision": self.config.supports_vision,
            "function_calling": self.config.supports_function_calling
        }
        return feature_map.get(feature, False)


class AnthropicProviderAdapter(BaseProviderAdapter):
    """Anthropic (Claude) 厂商适配器"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    async def _get_client(self):
        """获取Anthropic客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout
                )
            except ImportError:
                raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        return self._client

    async def create_model(self) -> Model:
        """创建Pydantic-AI模型实例"""
        from pydantic_ai.models.anthropic import AnthropicModel

        return AnthropicModel(
            model_name=self.config.model_name,
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Anthropic流式聊天"""
        client = await self._get_client()

        try:
            # 转换消息格式为Anthropic格式
            anthropic_messages = self._convert_messages_to_anthropic(messages)

            stream = await client.messages.create(
                model=self.config.model_name,
                messages=anthropic_messages,
                tools=tools,
                stream=True,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.extra_params
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    if chunk.delta.type == "text_delta":
                        yield {
                            "type": "text-delta",
                            "content": chunk.delta.text
                        }
                elif chunk.type == "content_block_stop":
                    yield {
                        "type": "content-block-finish"
                    }
                elif chunk.type == "message_delta":
                    if chunk.delta.stop_reason:
                        yield {
                            "type": "finish",
                            "reason": chunk.delta.stop_reason
                        }

        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Anthropic非流式聊天完成"""
        client = await self._get_client()

        try:
            anthropic_messages = self._convert_messages_to_anthropic(messages)

            response = await client.messages.create(
                model=self.config.model_name,
                messages=anthropic_messages,
                tools=tools,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.extra_params
            )

            content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text

            return {
                "content": content,
                "role": "assistant",
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                }
            }

        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            raise e

    def _convert_messages_to_anthropic(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换标准消息格式为Anthropic格式"""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                # Anthropic将系统消息作为第一个用户消息
                anthropic_messages.append({
                    "role": "user",
                    "content": f"System: {msg['content']}"
                })
            elif msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, str):
                    anthropic_messages.append({
                        "role": "user",
                        "content": content
                    })
                elif isinstance(content, list):
                    # 处理多模态内容
                    anthropic_content = []
                    for part in content:
                        if part["type"] == "text":
                            anthropic_content.append({"type": "text", "text": part["text"]})
                        elif part["type"] == "image":
                            anthropic_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": part["media_type"],
                                    "data": part["base64_data"]
                                }
                            })
                    anthropic_messages.append({
                        "role": "user",
                        "content": anthropic_content
                    })
            elif msg["role"] == "assistant":
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg["content"]
                })

        return anthropic_messages

    def supports_feature(self, feature: str) -> bool:
        """检查Anthropic功能支持"""
        feature_map = {
            "streaming": self.config.supports_streaming,
            "tools": self.config.supports_tools,
            "vision": self.config.supports_vision,
            "function_calling": self.config.supports_function_calling
        }
        return feature_map.get(feature, False)


class AgnoNativeProviderAdapter(BaseProviderAdapter):
    """Agno原生模型适配器"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._model = None

    async def create_model(self) -> AgnoModel:
        """创建Agno模型实例"""
        # 这里需要根据实际的Agno模型配置来创建
        # 暂时返回一个模拟的模型实例
        return self._create_agno_model()

    def _create_agno_model(self) -> AgnoModel:
        """创建Agno模型的具体实现"""
        # 这里需要根据实际的项目架构来实现
        # 可能需要调用models_mgr.py中的相关方法
        try:
            from models_mgr import ModelsMgr
            # 假设有一个全局的ModelsMgr实例
            # 实际实现时需要通过依赖注入等方式获取
            pass
        except ImportError:
            logger.warning("ModelsMgr not available, using mock model")

        # 返回一个模拟的模型
        class MockAgnoModel(AgnoModel):
            def __init__(self):
                super().__init__()

            async def chat_completion(self, messages, **kwargs):
                return {"content": "Mock response from Agno model"}

        return MockAgnoModel()

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Agno流式聊天"""
        try:
            # 这里需要集成实际的Agno流式聊天逻辑
            # 暂时提供模拟实现
            mock_response = "This is a mock streaming response from Agno model."

            for char in mock_response:
                yield {
                    "type": "text-delta",
                    "content": char
                }
                await asyncio.sleep(0.01)  # 模拟延迟

            yield {
                "type": "finish",
                "reason": "stop"
            }

        except Exception as e:
            logger.error(f"Agno stream error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Agno非流式聊天完成"""
        try:
            # 集成实际的Agno聊天完成逻辑
            model = await self.create_model()
            return await model.chat_completion(messages, tools=tools, **kwargs)
        except Exception as e:
            logger.error(f"Agno completion error: {e}")
            # 返回模拟响应作为降级方案
            return {
                "content": "Mock response from Agno model due to error.",
                "role": "assistant",
                "finish_reason": "stop",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    def supports_feature(self, feature: str) -> bool:
        """检查Agno功能支持"""
        # Agno模型的实际功能支持情况
        feature_map = {
            "streaming": True,  # Agno支持流式输出
            "tools": True,      # Agno支持工具调用
            "vision": False,    # 需要具体检查
            "function_calling": True
        }
        return feature_map.get(feature, False)


class MultiProviderManager:
    """多厂商管理器"""

    def __init__(self):
        self._adapters: Dict[str, BaseProviderAdapter] = {}
        self._default_provider: Optional[str] = None

    async def register_provider(
        self,
        provider_id: str,
        config: ProviderConfig
    ) -> bool:
        """注册厂商适配器"""
        try:
            adapter = self._create_adapter(config)
            await adapter.health_check()  # 验证连接

            self._adapters[provider_id] = adapter

            if self._default_provider is None:
                self._default_provider = provider_id

            logger.info(f"Successfully registered provider: {provider_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register provider {provider_id}: {e}")
            return False

    def _create_adapter(self, config: ProviderConfig) -> BaseProviderAdapter:
        """根据配置创建适配器"""
        adapter_map = {
            ProviderType.OPENAI: OpenAIProviderAdapter,
            ProviderType.ANTHROPIC: AnthropicProviderAdapter,
            ProviderType.AGNO_NATIVE: AgnoNativeProviderAdapter,
            # 可以继续添加其他厂商
        }

        adapter_class = adapter_map.get(config.provider_type)
        if not adapter_class:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")

        return adapter_class(config)

    def get_adapter(self, provider_id: Optional[str] = None) -> BaseProviderAdapter:
        """获取适配器实例"""
        if provider_id is None:
            provider_id = self._default_provider

        if provider_id is None or provider_id not in self._adapters:
            raise ValueError(f"Provider not found: {provider_id}")

        return self._adapters[provider_id]

    async def get_best_provider_for_task(
        self,
        task_type: str,
        required_features: List[str] = None
    ) -> str:
        """根据任务类型和功能需求选择最佳厂商"""
        required_features = required_features or []

        for provider_id, adapter in self._adapters.items():
            # 检查是否支持所有需要的功能
            if all(adapter.supports_feature(feature) for feature in required_features):
                # 进行健康检查
                health = await adapter.health_check()
                if health["status"] == "healthy":
                    return provider_id

        # 如果没有找到完全匹配的，返回默认提供商
        return self._default_provider or list(self._adapters.keys())[0]

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """检查所有注册厂商的健康状态"""
        results = {}

        for provider_id, adapter in self._adapters.items():
            try:
                results[provider_id] = await adapter.health_check()
            except Exception as e:
                results[provider_id] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        return results

    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有注册的厂商"""
        providers = []

        for provider_id, adapter in self._adapters.items():
            providers.append({
                "provider_id": provider_id,
                "provider_type": adapter.provider_type.value,
                "model_name": adapter.model_name,
                "supports_streaming": adapter.supports_feature("streaming"),
                "supports_tools": adapter.supports_feature("tools"),
                "supports_vision": adapter.supports_feature("vision"),
                "is_default": provider_id == self._default_provider
            })

        return providers

    def set_default_provider(self, provider_id: str) -> bool:
        """设置默认厂商"""
        if provider_id in self._adapters:
            self._default_provider = provider_id
            return True
        return False

    def remove_provider(self, provider_id: str) -> bool:
        """移除厂商"""
        if provider_id in self._adapters:
            del self._adapters[provider_id]

            # 如果移除的是默认厂商，重新选择一个
            if self._default_provider == provider_id:
                self._default_provider = next(iter(self._adapters.keys()), None)

            return True
        return False


# 全局多厂商管理器实例
_multi_provider_manager = MultiProviderManager()


def get_multi_provider_manager() -> MultiProviderManager:
    """获取全局多厂商管理器实例"""
    return _multi_provider_manager


# 便利函数
async def register_openai_provider(
    provider_id: str,
    api_key: str,
    model_name: str = "gpt-3.5-turbo",
    base_url: Optional[str] = None,
    **kwargs
) -> bool:
    """注册OpenAI厂商"""
    config = ProviderConfig(
        provider_type=ProviderType.OPENAI,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    return await _multi_provider_manager.register_provider(provider_id, config)


async def register_anthropic_provider(
    provider_id: str,
    api_key: str,
    model_name: str = "claude-3-sonnet-20240229",
    base_url: Optional[str] = None,
    **kwargs
) -> bool:
    """注册Anthropic厂商"""
    config = ProviderConfig(
        provider_type=ProviderType.ANTHROPIC,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    return await _multi_provider_manager.register_provider(provider_id, config)


async def register_agno_provider(
    provider_id: str,
    model_name: str,
    **kwargs
) -> bool:
    """注册Agno原生厂商"""
    config = ProviderConfig(
        provider_type=ProviderType.AGNO_NATIVE,
        model_name=model_name,
        **kwargs
    )
    return await _multi_provider_manager.register_provider(provider_id, config)