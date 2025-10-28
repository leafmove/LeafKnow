#!/usr/bin/env python3
"""
增强版Agno AI聊天应用
支持多种模型类型、模型管理、配置保存和加载、Ollama本地模型
"""

import asyncio
import json
import os
import sys
import subprocess
from typing import Optional, AsyncGenerator, Dict, List, Any, TYPE_CHECKING
from dataclasses import dataclass, asdict
from pathlib import Path

# 兼容Python 3.8的泛型类型注解
if TYPE_CHECKING:
    pass

# 安全的导入函数
def safe_import(module_path, class_name, error_message=None):
    """安全导入模块和类"""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError, TypeError) as e:
        if error_message:
            print(f"[警告] {error_message}")
        else:
            print(f"[警告] 无法导入 {module_path}.{class_name}: {str(e)}")
        return None

# Agno imports
Agent = safe_import("agno.agent", "Agent")
OpenAIChat = safe_import("agno.models.openai", "OpenAIChat")

# 尝试导入各种模型支持
OpenRouter = safe_import("agno.models.openrouter", "OpenRouter", "openrouter支持不可用")
OPENROUTER_AVAILABLE = OpenRouter is not None

Claude = safe_import("agno.models.anthropic", "Claude", "anthropic库未安装或Python版本不兼容，Claude模型功能不可用")
ANTHROPIC_AVAILABLE = Claude is not None

Groq = safe_import("agno.models.groq", "Groq", "groq库未安装，Groq模型功能不可用")
GROQ_AVAILABLE = Groq is not None

Ollama = safe_import("agno.models.ollama", "Ollama", "ollama库未安装，Ollama模型功能不可用")
OLLAMA_AVAILABLE = Ollama is not None


@dataclass
class ModelConfig:
    """模型配置类"""
    name: str  # 模型显示名称
    model_id: str  # 模型ID
    provider: str  # 提供商类型
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000
    description: str = ""  # 模型描述
    is_local: bool = False  # 是否为本地模型


class ModelManager:
    """模型管理器"""

    def __init__(self, config_file: str = "model_configs.json"):
        self.config_file = Path(config_file)
        self.models: Dict[str, ModelConfig] = {}
        self.current_model: Optional[str] = None
        self.load_configs()
        self._init_default_models()

    def _init_default_models(self):
        """初始化默认模型配置"""
        if not self.models:
            # OpenAI 模型
            self.add_model(ModelConfig(
                name="OpenAI GPT-4o-mini",
                model_id="gpt-4o-mini",
                provider="openai",
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY") or "your_api_key_here",  # 请替换为您的实际API密钥
                description="OpenAI的GPT-4o mini模型，适合一般对话"
            ))

            self.add_model(ModelConfig(
                name="OpenAI GPT-4o",
                model_id="gpt-4o",
                provider="openai",
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY") or "your_api_key_here",  # 请替换为您的实际API密钥
                description="OpenAI的GPT-4o模型，更强的推理能力"
            ))

            # Claude 模型 (如果可用)
            if ANTHROPIC_AVAILABLE:
                self.add_model(ModelConfig(
                    name="Claude 3.5 Sonnet",
                    model_id="claude-3-5-sonnet-20241022",
                    provider="anthropic",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    description="Anthropic的Claude 3.5 Sonnet模型，优秀的推理能力"
                ))

            # Groq 模型 (如果可用)
            if GROQ_AVAILABLE:
                self.add_model(ModelConfig(
                    name="Groq Llama 3.1 8B",
                    model_id="llama-3.1-8b-instant",
                    provider="groq",
                    api_key=os.getenv("GROQ_API_KEY"),
                    description="Groq的Llama 3.1 8B模型，快速响应"
                ))

            # OpenRouter 模型 (如果可用)
            if OPENROUTER_AVAILABLE:
                self.add_model(ModelConfig(
                    name="OpenRouter Mixtral",
                    model_id="mistralai/mixtral-8x7b-instruct",
                    provider="openrouter",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1",
                    description="OpenRouter的Mixtral模型"
                ))

            # 默认设置为第一个模型
            if self.models:
                self.current_model = list(self.models.keys())[0]

    def add_model(self, config: ModelConfig) -> bool:
        """添加模型配置"""
        try:
            self.models[config.name] = config
            if self.current_model is None:
                self.current_model = config.name
            return True
        except Exception as e:
            print(f"[错误] 添加模型失败: {str(e)}")
            return False

    def remove_model(self, name: str) -> bool:
        """删除模型配置"""
        if name in self.models:
            del self.models[name]
            if self.current_model == name:
                self.current_model = next(iter(self.models), None)
            return True
        return False

    def get_model(self, name: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(name)

    def get_current_model(self) -> Optional[ModelConfig]:
        """获取当前模型配置"""
        if self.current_model:
            return self.models.get(self.current_model)
        return None

    def set_current_model(self, name: str) -> bool:
        """设置当前模型"""
        if name in self.models:
            self.current_model = name
            return True
        return False

    def list_models(self) -> List[ModelConfig]:
        """列出所有模型"""
        return list(self.models.values())

    def scan_ollama_models(self) -> List[str]:
        """扫描本地Ollama模型"""
        if not OLLAMA_AVAILABLE:
            print("[警告] Ollama库未安装，无法获取模型列表")
            return []

        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                models = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])  # 模型名称
                return models
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"[警告] 无法获取Ollama模型列表: {str(e)}")
            print("[提示] 请确保Ollama已安装并运行: https://ollama.ai")
        return []

    def add_ollama_models(self):
        """自动添加本地Ollama模型"""
        ollama_models = self.scan_ollama_models()
        for model_name in ollama_models:
            config_name = f"Ollama {model_name}"
            if config_name not in self.models:
                self.add_model(ModelConfig(
                    name=config_name,
                    model_id=model_name,
                    provider="ollama",
                    base_url="http://localhost:11434",
                    is_local=True,
                    description=f"本地Ollama模型: {model_name}"
                ))
                print(f"[OK] 添加Ollama模型: {model_name}")

    def save_configs(self) -> bool:
        """保存配置到文件"""
        try:
            configs = {
                "models": {name: asdict(config) for name, config in self.models.items()},
                "current_model": self.current_model
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[错误] 保存配置失败: {str(e)}")
            return False

    def load_configs(self) -> bool:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    self.models = {}
                    for name, config_data in configs.get("models", {}).items():
                        self.models[name] = ModelConfig(**config_data)
                    self.current_model = configs.get("current_model")
                    return True
        except Exception as e:
            print(f"[警告] 加载配置失败: {str(e)}")
        return False

    def create_model_instance(self, config: ModelConfig):
        """根据配置创建模型实例"""
        try:
            if config.provider == "openai":
                # 验证API密钥
                if not config.api_key or config.api_key == "your_api_key_here":
                    print(f"[错误] OpenAI API密钥未设置或使用默认值")
                    print(f"[提示] 请设置环境变量 OPENAI_API_KEY 或在代码中配置实际API密钥")
                    return None

                return OpenAIChat(
                    id=config.model_id,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            elif config.provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    raise ImportError("Ollama库未安装，请运行: pip install ollama")

                # Ollama使用options参数来设置temperature和max_tokens
                options = {
                    "temperature": config.temperature,
                }
                if config.max_tokens:
                    options["num_predict"] = config.max_tokens

                return Ollama(
                    id=config.model_id,
                    host=config.base_url,
                    options=options,
                )
            elif config.provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError("Anthropic库未安装，请运行: pip install anthropic")
                return Claude(
                    id=config.model_id,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            elif config.provider == "groq":
                if not GROQ_AVAILABLE:
                    raise ImportError("Groq库未安装，请运行: pip install groq")
                return Groq(
                    id=config.model_id,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            elif config.provider == "openrouter":
                if not OPENROUTER_AVAILABLE:
                    raise ImportError("OpenRouter支持不可用")
                return OpenRouter(
                    id=config.model_id,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    base_url=config.base_url,
                )
            else:
                raise ValueError(f"不支持的提供商: {config.provider}")
        except Exception as e:
            print(f"[错误] 创建模型实例失败: {str(e)}")
            return None


class EnhancedChatApp:
    """增强版AI聊天应用"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.system_prompt = "你是一个有用的AI助手，请用简洁明了的语言回答问题。"
        self.use_streaming = True
        self.current_agent = None

    def show_model_menu(self) -> bool:
        """显示模型选择菜单"""
        print("\n" + "=" * 60)
        print("模型管理菜单")
        print("=" * 60)

        models = self.model_manager.list_models()
        current = self.model_manager.current_model

        for i, model in enumerate(models, 1):
            current_mark = " [当前]" if model.name == current else ""
            local_mark = " [本地]" if model.is_local else ""
            provider_info = f"({model.provider})"
            print(f"{i:2d}. {model.name}{current_mark}{local_mark} {provider_info}")
            if model.description:
                print(f"     {model.description}")

        print(f"{len(models)+1:2d}. 刷新Ollama模型")
        print(f"{len(models)+2:2d}. 添加自定义模型")
        print(f"{len(models)+3:2d}. 删除模型")
        print(f"{len(models)+4:2d}. 保存配置")
        print(f"{len(models)+5:2d}. 查看当前配置")
        print(" 0. 返回聊天")

        try:
            choice = input("\n请选择操作: ").strip()
            return self.handle_model_menu_choice(choice, len(models))
        except KeyboardInterrupt:
            print("\n返回聊天")
            return False

    def handle_model_menu_choice(self, choice: str, model_count: int) -> bool:
        """处理模型菜单选择"""
        try:
            choice_num = int(choice)

            if choice_num == 0:
                return False
            elif 1 <= choice_num <= model_count:
                # 选择模型
                models = list(self.model_manager.list_models())
                selected_model = models[choice_num - 1]
                if self.model_manager.set_current_model(selected_model.name):
                    print(f"[OK] 已切换到模型: {selected_model.name}")
                    self._create_current_agent()
                return True
            elif choice_num == model_count + 1:
                # 刷新Ollama模型
                print("正在扫描本地Ollama模型...")
                self.model_manager.add_ollama_models()
                return True
            elif choice_num == model_count + 2:
                # 添加自定义模型
                self._add_custom_model()
                return True
            elif choice_num == model_count + 3:
                # 删除模型
                self._delete_model()
                return True
            elif choice_num == model_count + 4:
                # 保存配置
                if self.model_manager.save_configs():
                    print("[OK] 配置已保存")
                else:
                    print("[错误] 保存配置失败")
                return True
            elif choice_num == model_count + 5:
                # 查看当前配置
                self._show_current_config()
                return True
            else:
                print("[错误] 无效选择")
                return True
        except ValueError:
            print("[错误] 请输入有效数字")
            return True

    def _add_custom_model(self):
        """添加自定义模型"""
        print("\n添加自定义模型")
        print("-" * 30)

        name = input("模型名称: ").strip()
        if not name:
            print("[错误] 模型名称不能为空")
            return

        if name in self.model_manager.models:
            print("[错误] 模型名称已存在")
            return

        model_id = input("模型ID: ").strip()
        if not model_id:
            print("[错误] 模型ID不能为空")
            return

        print("\n支持的提供商:")
        providers = []
        if True:  # OpenAI总是可用
            providers.append("openai")
        if OLLAMA_AVAILABLE:
            providers.append("ollama")
        if ANTHROPIC_AVAILABLE:
            providers.append("anthropic")
        if GROQ_AVAILABLE:
            providers.append("groq")
        if OPENROUTER_AVAILABLE:
            providers.append("openrouter")

        for i, provider in enumerate(providers, 1):
            print(f"{i}. {provider}")

        if not providers:
            print("[错误] 没有可用的模型提供商")
            return

        try:
            provider_choice = int(input("选择提供商: ")) - 1
            if 0 <= provider_choice < len(providers):
                provider = providers[provider_choice]
            else:
                print("[错误] 无效选择")
                return
        except ValueError:
            print("[错误] 请输入有效数字")
            return

        base_url = input("Base URL (可选): ").strip() or None
        api_key = input("API Key (可选): ").strip() or None

        try:
            temperature = float(input("Temperature [0.7]: ").strip() or "0.7")
            max_tokens = int(input("Max Tokens [2000]: ").strip() or "2000")
        except ValueError:
            print("[错误] 参数格式错误，使用默认值")
            temperature = 0.7
            max_tokens = 2000

        description = input("模型描述 (可选): ").strip() or ""

        config = ModelConfig(
            name=name,
            model_id=model_id,
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            description=description,
            is_local=(provider == "ollama")
        )

        if self.model_manager.add_model(config):
            print(f"[OK] 模型已添加: {name}")
        else:
            print("[错误] 添加模型失败")

    def _delete_model(self):
        """删除模型"""
        models = self.model_manager.list_models()
        if not models:
            print("[错误] 没有可删除的模型")
            return

        print("\n选择要删除的模型:")
        for i, model in enumerate(models, 1):
            print(f"{i}. {model.name}")

        try:
            choice = int(input("选择模型编号: ")) - 1
            if 0 <= choice < len(models):
                model_name = models[choice].name
                if self.model_manager.remove_model(model_name):
                    print(f"[OK] 模型已删除: {model_name}")
                else:
                    print("[错误] 删除模型失败")
            else:
                print("[错误] 无效选择")
        except ValueError:
            print("[错误] 请输入有效数字")

    def _show_current_config(self):
        """显示当前配置"""
        current_model = self.model_manager.get_current_model()
        if not current_model:
            print("[错误] 没有当前模型")
            return

        print("\n当前模型配置:")
        print("-" * 30)
        print(f"名称: {current_model.name}")
        print(f"模型ID: {current_model.model_id}")
        print(f"提供商: {current_model.provider}")
        print(f"Base URL: {current_model.base_url or '默认'}")
        print(f"API Key: {'已设置' if current_model.api_key else '未设置'}")
        print(f"Temperature: {current_model.temperature}")
        print(f"Max Tokens: {current_model.max_tokens}")
        print(f"本地模型: {'是' if current_model.is_local else '否'}")
        if current_model.description:
            print(f"描述: {current_model.description}")

    def _create_current_agent(self):
        """创建当前模型的Agent"""
        config = self.model_manager.get_current_model()
        if not config:
            print("[错误] 没有选择模型")
            return

        model_instance = self.model_manager.create_model_instance(config)
        if model_instance:
            self.current_agent = Agent(
                model=model_instance,
                instructions=[self.system_prompt],
                markdown=True,
            )
            print(f"[OK] Agent已创建: {config.name}")
        else:
            print("[错误] 创建Agent失败")

    def chat_non_streaming(self, user_prompt: str) -> str:
        """非流式聊天"""
        if not self.current_agent:
            return "[错误] 没有可用的Agent"

        try:
            response = self.current_agent.run(user_prompt)
            return response.content if response.content else "抱歉，我没有收到有效回复。"
        except Exception as e:
            return f"[错误] 聊天失败: {str(e)}"

    def chat_streaming(self, user_prompt: str) :
        """流式聊天"""
        if not self.current_agent:
            yield "[错误] 没有可用的Agent"
            return
        # print("正在处理...",self.current_agent)
        try:
            # 使用正确的agno流式API
            for chunk in self.current_agent.run(user_prompt, stream=True):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"[错误] 流式聊天失败: {str(e)}"

    def _print_streaming_response(self, user_prompt: str):
        """打印流式响应"""
        for chunk in self.chat_streaming(user_prompt):
            print(chunk, end="", flush=True)
        print()  # 换行

    def interactive_chat(self):
        """交互式聊天界面"""
        print("=" * 60)
        print("增强版 Agno AI聊天应用")
        print("=" * 60)

        # 初始化
        print("正在初始化...")
        self.model_manager.add_ollama_models()  # 自动扫描Ollama模型
        self._create_current_agent()

        # 聊天循环
        print("\n=== 开始聊天 ===")
        print("命令:")
        print("  'models' - 模型管理")
        print("  'stream' - 切换流式/非流式模式")
        print("  'system' - 修改系统提示词")
        print("  'quit' 或 'exit' - 退出")

        while True:
            try:
                user_input = input(f"\n用户 [{self.model_manager.current_model}]: ").strip()

                if user_input.lower() in ['quit', 'exit']:
                    # 保存配置
                    self.model_manager.save_configs()
                    print("再见! 配置已保存。")
                    break
                elif user_input.lower() == 'models':
                    # 模型管理
                    while self.show_model_menu():
                        pass
                    continue
                elif user_input.lower() == 'stream':
                    self.use_streaming = not self.use_streaming
                    mode = "流式" if self.use_streaming else "非流式"
                    print(f"已切换到{mode}模式")
                    continue
                elif user_input.lower() == 'system':
                    # 修改系统提示词
                    new_prompt = input(f"新系统提示词 [当前: {self.system_prompt}]: ").strip()
                    if new_prompt:
                        self.system_prompt = new_prompt
                        self._create_current_agent()  # 重新创建Agent
                        print("[OK] 系统提示词已更新")
                    continue
                elif not user_input:
                    continue

                # 检查用户是否在尝试切换模型 (格式: "model_name: message")
                if ":" in user_input and not user_input.startswith(("http://", "https://", "ftp://")):
                    potential_model, message = user_input.split(":", 1)
                    potential_model = potential_model.strip()
                    message = message.strip()

                    # 尝试查找匹配的模型
                    found_model = None
                    for model in self.model_manager.list_models():
                        if (potential_model.lower() in model.name.lower() or
                            potential_model.lower() in model.model_id.lower() or
                            model.name.lower() in potential_model.lower() or
                            model.model_id.lower() in potential_model.lower()):
                            found_model = model
                            break

                    # 如果没有找到，尝试作为Ollama模型添加
                    if not found_model and ("ollama" in potential_model.lower() or
                                          any(keyword in potential_model.lower() for keyword in ["deepseek", "llama", "qwen", "mistral", "codellama"])):
                        # 提取模型名称
                        if "ollama" in potential_model.lower():
                            ollama_model_name = potential_model.replace("ollama", "").strip()
                        else:
                            ollama_model_name = potential_model

                        # 标准化模型名称
                        ollama_model_name = ollama_model_name.strip()
                        config_name = f"Ollama {ollama_model_name}"

                        # 检查是否已经存在
                        existing_model = self.model_manager.get_model(config_name)
                        if existing_model:
                            found_model = existing_model
                        else:
                            # 尝试创建Ollama模型配置
                            ollama_config = ModelConfig(
                                name=config_name,
                                model_id=ollama_model_name,
                                provider="ollama",
                                base_url="http://localhost:11434",
                                is_local=True,
                                description=f"动态添加的Ollama模型: {ollama_model_name}"
                            )

                            if self.model_manager.add_model(ollama_config):
                                found_model = ollama_config
                                print(f"[OK] 已添加Ollama模型: {config_name}")
                                print(f"[提示] 请确保Ollama服务运行且模型已安装")
                            else:
                                print(f"[WARN] 无法添加Ollama模型: {ollama_model_name}")

                    # 如果找到模型，切换并处理消息
                    if found_model:
                        if self.model_manager.set_current_model(found_model.name):
                            print(f"[OK] 已切换到模型: {found_model.name}")
                            self._create_current_agent()
                            user_input = message if message else "你好"  # 如果没有消息，使用默认问候
                        else:
                            print(f"[ERROR] 切换模型失败: {found_model.name}")
                    else:
                        print(f"[WARN] 未找到模型: {potential_model}")
                        print(f"[提示] 可用模型: {', '.join([m.name for m in self.model_manager.list_models()[:3]])}...")
                        print(f"[提示] 使用 'models' 命令管理模型")

                print("AI: ", end="", flush=True)

                if self.use_streaming:
                    # 流式输出
                    try:
                        self._print_streaming_response(user_input)
                    except KeyboardInterrupt:
                        print("\n[用户中断]")
                    except Exception as e:
                        print(f"\n[错误] {str(e)}")
                else:
                    # 非流式输出
                    try:
                        response = self.chat_non_streaming(user_input)
                        print(response)
                    except KeyboardInterrupt:
                        print("\n[用户中断]")
                    except Exception as e:
                        print(f"[错误] {str(e)}")

            except KeyboardInterrupt:
                print("\n使用 'quit' 退出程序")
            except Exception as e:
                print(f"[错误] {str(e)}")


def main():
    """主函数"""
    app = EnhancedChatApp()

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # 演示模式
        print("演示模式暂不支持，请使用交互式模式")
        print("运行: python enhanced_chat_app.py")
    else:
        # 交互式模式
        app.interactive_chat()


if __name__ == "__main__":
    main()