"""
Agent管理模块使用示例
演示如何使用agno_modular进行Agent的增删改查操作
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# 假设已经初始化了必要的依赖
from agent_manager import AgentCRUDManager
from agent_models import AgentType, AgentStatus
from models_mgr import ModelsManager
from db_mgr import DBManager


async def basic_agent_examples():
    """基础Agent操作示例"""

    print("=== 基础Agent操作示例 ===")

    # 1. 创建模拟管理器（因为真实的需要数据库）
    print("注意: 由于需要数据库连接，这里使用模拟数据来演示基本功能")

    # 模拟Agent数据
    class MockAgent:
        def __init__(self, id, name, agent_type):
            self.id = id
            self.name = name
            self.agent_type = agent_type
            self.status = "active"
            self.created_at = datetime.now()
            self.updated_at = datetime.now()

    # 模拟Agent管理器
    class MockAgentManager:
        def __init__(self):
            self.agents = {}
            self.next_id = 1

        def create_custom_agent(self, name, agent_type, **kwargs):
            agent = MockAgent(self.next_id, name, agent_type)
            self.agents[self.next_id] = agent
            self.next_id += 1
            return agent

        def list_user_agents(self, user_id, **kwargs):
            return list(self.agents.values())

        def update_agent_config(self, agent_id, **kwargs):
            agent = self.agents.get(agent_id)
            if agent:
                for key, value in kwargs.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                agent.updated_at = datetime.now()
            return agent

        def search_agents(self, query, **kwargs):
            results = []
            for agent in self.agents.values():
                if query.lower() in agent.name.lower():
                    results.append(agent)
            return results

        def clone_agent(self, agent_id, new_name, **kwargs):
            original = self.agents.get(agent_id)
            if original:
                new_agent = MockAgent(self.next_id, new_name, original.agent_type)
                self.agents[self.next_id] = new_agent
                self.next_id += 1
                return new_agent
            return None

        def activate_agent(self, agent_id):
            return True

        def deactivate_agent(self, agent_id):
            return True

        def delete_agent(self, agent_id, soft_delete=True):
            if agent_id in self.agents:
                del self.agents[agent_id]
                return True
            return False

        def get_agent_statistics(self, agent_id, days=30):
            return {
                'total_uses': 10,
                'success_rate': 95.5,
                'avg_response_time': 1.2
            }

        def list_available_templates(self):
            return []

        def list_available_memory_configs(self):
            return []

        def create_agent_from_template(self, name, template_name, **kwargs):
            # 模拟基于模板创建
            agent = MockAgent(self.next_id, name, AgentType.QA)
            self.agents[self.next_id] = agent
            self.next_id += 1
            return agent

        def run_agent(self, agent_id, message, **kwargs):
            return f"这是来自Agent {agent_id}的模拟响应: 你问了'{message}'"

    agent_manager = MockAgentManager()

    # 2. 创建自定义Agent
    print("\n1. 创建自定义Agent")
    qa_agent = agent_manager.create_custom_agent(
        name="Python编程助手",
        agent_type=AgentType.QA,
        description="专门帮助用户解决Python编程问题",
        system_prompt="""你是一个专业的Python编程助手。

你的职责：
1. 提供准确的Python代码示例
2. 解释编程概念和最佳实践
3. 帮助调试和优化代码
4. 推荐合适的库和工具

请保持回答的专业性和实用性。""",
        capabilities=["text", "reasoning", "code_generation"],
        tool_names=["get_current_time", "local_file_search"],
        enable_memory=True,
        memory_config_name="conversation_memory",
        debug_mode=True
    )

    print(f"✅ 创建成功: {qa_agent.name} (ID: {qa_agent.id})")

    # 3. 基于模板创建Agent
    print("\n2. 基于模板创建Agent")
    try:
        research_agent = agent_manager.create_agent_from_template(
            name="AI研究助手",
            template_name="research_assistant",
            custom_instructions="专注于人工智能和机器学习领域的研究",
            enable_memory=True
        )
        print(f"✅ 模板创建成功: {research_agent.name} (ID: {research_agent.id})")
    except Exception as e:
        print(f"❌ 模板创建失败: {e}")

    # 4. 运行Agent
    print("\n3. 运行Agent")
    try:
        response = agent_manager.run_agent(
            agent_id=qa_agent.id,
            message="如何用Python实现一个二分查找算法？请提供代码示例。",
            user_id=123
        )
        print(f"✅ Agent响应: {response[:200]}...")
    except Exception as e:
        print(f"❌ Agent运行失败: {e}")

    # 5. 查询Agent列表
    print("\n4. 查询Agent列表")
    agents = agent_manager.list_user_agents(user_id=123)
    for agent in agents:
        print(f"  - {agent.name} ({agent.agent_type}) - {agent.status}")

    return agent_manager


async def agent_management_examples(agent_manager: AgentCRUDManager):
    """Agent管理操作示例"""

    print("\n=== Agent管理操作示例 ===")

    # 假设我们有一个已存在的Agent
    agents = agent_manager.list_user_agents(user_id=123)
    if not agents:
        print("❌ 没有找到可用的Agent")
        return

    agent = agents[0]
    print(f"使用Agent: {agent.name} (ID: {agent.id})")

    # 1. 更新Agent配置
    print("\n1. 更新Agent配置")
    updated_agent = agent_manager.update_agent_config(
        agent_id=agent.id,
        description="更新后的描述：专业的Python编程和数据分析助手",
        capabilities=["text", "reasoning", "code_generation", "structured_output"],
        debug_mode=False
    )
    print(f"✅ 更新成功: {updated_agent.description}")

    # 2. 搜索Agent
    print("\n2. 搜索Agent")
    search_results = agent_manager.search_agents(
        query="Python",
        user_id=123,
        limit=5
    )
    print(f"找到 {len(search_results)} 个相关Agent:")
    for result in search_results:
        print(f"  - {result.name}: {result.description}")

    # 3. 克隆Agent
    print("\n3. 克隆Agent")
    try:
        cloned_agent = agent_manager.clone_agent(
            agent_id=agent.id,
            new_name="Python高级助手",
            user_id=123
        )
        print(f"✅ 克隆成功: {cloned_agent.name} (ID: {cloned_agent.id})")
    except Exception as e:
        print(f"❌ 克隆失败: {e}")

    # 4. Agent状态管理
    print("\n4. Agent状态管理")

    # 停用Agent
    success = agent_manager.deactivate_agent(agent.id)
    print(f"停用Agent: {'✅ 成功' if success else '❌ 失败'}")

    # 重新激活Agent
    success = agent_manager.activate_agent(agent.id)
    print(f"激活Agent: {'✅ 成功' if success else '❌ 失败'}")

    # 5. 获取使用统计
    print("\n5. 获取使用统计")
    stats = agent_manager.get_agent_statistics(agent.id, days=30)
    print(f"统计信息:")
    print(f"  - 总使用次数: {stats['total_uses']}")
    print(f"  - 成功率: {stats['success_rate']}%")
    print(f"  - 平均响应时间: {stats['avg_response_time']}ms")


async def configuration_examples(agent_manager: AgentCRUDManager):
    """配置管理示例"""

    print("\n=== 配置管理示例 ===")

    # 1. 获取可用模板
    print("\n1. 获取可用模板")
    templates = agent_manager.list_available_templates()
    print(f"可用模板 ({len(templates)} 个):")
    for template in templates:
        print(f"  - {template.display_name} ({template.name}): {template.description}")

    # 2. 获取记忆配置
    print("\n2. 获取记忆配置")
    memory_configs = agent_manager.list_available_memory_configs()
    print(f"记忆配置 ({len(memory_configs)} 个):")
    for config in memory_configs:
        print(f"  - {config.name}: {config.description}")

    # 3. 导出Agent配置
    print("\n3. 导出Agent配置")
    agents = agent_manager.list_user_agents(user_id=123)
    if agents:
        agent = agents[0]
        config = agent_manager.export_agent_config(agent.id)
        print(f"导出的配置 ({agent.name}):")
        print(json.dumps(config, indent=2, ensure_ascii=False))

        # 4. 导入配置创建新Agent
        print("\n4. 导入配置创建新Agent")
        try:
            imported_agent = agent_manager.import_agent_config(
                config_data=config,
                name="导入的助手",
                user_id=123
            )
            print(f"✅ 导入成功: {imported_agent.name} (ID: {imported_agent.id})")
        except Exception as e:
            print(f"❌ 导入失败: {e}")


async def advanced_usage_examples(agent_manager: AgentCRUDManager):
    """高级使用示例"""

    print("\n=== 高级使用示例 ===")

    # 1. 批量创建不同类型的Agent
    print("\n1. 批量创建不同类型的Agent")

    agent_types = [
        (AgentType.QA, "问答助手", "回答用户问题"),
        (AgentType.TASK, "任务助手", "执行具体任务"),
        (AgentType.RESEARCH, "研究助手", "进行深度研究"),
        (AgentType.CREATIVE, "创意助手", "提供创意方案")
    ]

    created_agents = []
    for agent_type, name, description in agent_types:
        try:
            agent = agent_manager.create_custom_agent(
                name=f"AI{name}",
                agent_type=agent_type,
                description=f"人工智能{name}，{description}",
                system_prompt=f"你是AI{name}，专门负责{description}",
                capabilities=["text", "reasoning"],
                enable_memory=True,
                user_id=123
            )
            created_agents.append(agent)
            print(f"✅ 创建成功: {agent.name}")
        except Exception as e:
            print(f"❌ 创建失败 {name}: {e}")

    # 2. 批量运行测试
    print("\n2. 批量运行测试")
    test_messages = [
        "什么是人工智能？",
        "帮我分析一下当前时间",
        "研究一下机器学习的发展趋势",
        "给我一些创新的编程思路"
    ]

    for i, agent in enumerate(created_agents[:len(test_messages)]):
        try:
            response = agent_manager.run_agent(
                agent_id=agent.id,
                message=test_messages[i],
                user_id=123
            )
            print(f"✅ {agent.name} 响应成功")
        except Exception as e:
            print(f"❌ {agent.name} 响应失败: {e}")

    # 3. 性能测试
    print("\n3. 性能测试")
    if created_agents:
        test_agent = created_agents[0]
        start_time = datetime.now()

        try:
            # 连续运行多次
            for i in range(5):
                response = agent_manager.run_agent(
                    agent_id=test_agent.id,
                    message=f"测试消息 {i+1}: 简单回答这个问题",
                    user_id=123
                )

            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            avg_time = total_time / 5

            print(f"✅ 性能测试完成")
            print(f"  - 总时间: {total_time:.2f}秒")
            print(f"  - 平均响应时间: {avg_time:.2f}秒")

        except Exception as e:
            print(f"❌ 性能测试失败: {e}")

    # 4. 清理测试数据
    print("\n4. 清理测试数据")
    for agent in created_agents:
        try:
            success = agent_manager.delete_agent(agent.id, soft_delete=False)
            print(f"删除 {agent.name}: {'✅ 成功' if success else '❌ 失败'}")
        except Exception as e:
            print(f"删除 {agent.name} 失败: {e}")


async def api_usage_examples():
    """API使用示例"""

    print("\n=== API使用示例 ===")

    # 这些是HTTP请求示例，实际使用时需要发送到API端点

    api_examples = {
        "创建Agent": {
            "method": "POST",
            "url": "/api/agents/",
            "data": {
                "name": "HTTP测试助手",
                "agent_type": "qa",
                "description": "通过HTTP API创建的测试助手",
                "system_prompt": "你是一个通过HTTP API创建的测试助手",
                "capabilities": ["text", "reasoning"],
                "enable_memory": True
            }
        },

        "运行Agent": {
            "method": "POST",
            "url": "/api/agents/1/run",
            "data": {
                "message": "你好，请介绍一下你自己",
                "stream": False
            }
        },

        "更新Agent": {
            "method": "PUT",
            "url": "/api/agents/1",
            "data": {
                "description": "更新后的描述",
                "capabilities": ["text", "reasoning", "web_search"]
            }
        },

        "搜索Agent": {
            "method": "GET",
            "url": "/api/agents/search?query=助手&limit=10",
            "data": None
        },

        "获取统计": {
            "method": "GET",
            "url": "/api/agents/1/stats?days=7",
            "data": None
        }
    }

    for name, example in api_examples.items():
        print(f"\n{name}:")
        print(f"  方法: {example['method']}")
        print(f"  URL: {example['url']}")
        if example['data']:
            print(f"  数据: {json.dumps(example['data'], indent=4, ensure_ascii=False)}")


async def main():
    """主函数 - 运行所有示例"""

    print("🤖 Agent管理模块使用示例")
    print("=" * 50)

    try:
        # 基础操作示例
        agent_manager = await basic_agent_examples()

        if agent_manager:
            # 管理操作示例
            await agent_management_examples(agent_manager)

            # 配置管理示例
            await configuration_examples(agent_manager)

            # 高级使用示例
            await advanced_usage_examples(agent_manager)

        # API使用示例
        await api_usage_examples()

        print("\n" + "=" * 50)
        print("✅ 所有示例执行完成！")

    except Exception as e:
        print(f"\n❌ 示例执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())