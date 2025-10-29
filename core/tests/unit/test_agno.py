# 添加项目路径
import os,sys
from pathlib import Path
print(Path(__file__).parent.parent.parent)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.agno.agent import Agent
from core.agno.models.openrouter import OpenRouter

# 创建基本智能体
agent = Agent(
    name="Assistant",
    model=OpenRouter(id='glm-4.6',
                     api_key="sk-3KdzUkc4E8wKKx7NnioVwV8R485m7EDqmL3IFBiD4UUOvlwr",
                     base_url='https://www.dmxapi.cn/v1'),
    instructions="You are a helpful AI assistant.",
    markdown=True,
)

# 执行智能体
agent.print_response("pip 查询可以下载某个库的可下载版本", stream=True)


