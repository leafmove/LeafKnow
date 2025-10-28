#!/usr/bin/env python3
"""
Example: Using Python 3.8 Compatible MCP with Agno Agent

This example demonstrates how to create an agno agent that uses MCP tools
through the Python 3.8 compatible implementation.
"""

import asyncio
import sys
import os

# Add the agno package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.utils.mcp import create_filesystem_mcp_session, MCPToolWrapper


async def create_mcp_file_agent():
    """Create an agent with filesystem MCP tools"""

    print("Creating MCP session for filesystem operations...")

    # Create filesystem MCP session
    session = create_filesystem_mcp_session(".")
    await session.initialize()

    print("Loading available tools...")

    # Get available tools
    mcp_tools = await session.list_tools()
    print(f"Found {len(mcp_tools)} MCP tools:")
    for tool in mcp_tools:
        print(f"  - {tool.name}: {tool.description}")

    # Convert MCP tools to agno functions
    agno_functions = []
    for mcp_tool in mcp_tools:
        wrapper = MCPToolWrapper(mcp_tool, session)
        agno_function = wrapper.to_agno_function()
        agno_functions.append(agno_function)
        print(f"  ✓ Converted {mcp_tool.name} to agno function")

    # Create the agent with MCP tools
    # Note: You'll need to set your OpenAI API key
    agent = Agent(
        model=OpenAIChat(id="gpt-3.5-turbo"),
        tools=agno_functions,
        instructions="""You are a helpful assistant that can work with files.
        You have access to filesystem tools through MCP that allow you to:
        - Read files with read_file
        - Write files with write_file
        - List directory contents with list_directory

        When working with files, always explain what you're doing and show the results."""
    )

    return agent, session


async def main():
    """Main example function"""

    print("Python 3.8 Compatible MCP + Agno Agent Example")
    print("=" * 50)

    # Create test data
    test_file = "example_data.txt"
    with open(test_file, "w") as f:
        f.write("Hello, MCP World!\n")
        f.write("This is a test file created for the MCP agent example.\n")
        f.write("The agent can read and write this file using MCP tools.\n")

    try:
        # Create agent with MCP tools
        agent, session = await create_mcp_file_agent()

        print("\nAgent created successfully!")
        print("Now testing the agent with file operations...")

        # Test 1: List files in current directory
        print("\n--- Test 1: List directory contents ---")
        response1 = await agent.arun("List the files in the current directory")
        print(f"Agent response: {response1.content if response1 else 'No response'}")

        # Test 2: Read the test file
        print("\n--- Test 2: Read test file ---")
        response2 = await agent.arun(f"Read the contents of {test_file}")
        print(f"Agent response: {response2.content if response2 else 'No response'}")

        # Test 3: Write a new file
        print("\n--- Test 3: Create a new file ---")
        response3 = await agent.arun(
            "Create a new file called 'mcp_output.txt' with a summary of what you found in the directory"
        )
        print(f"Agent response: {response3.content if response3 else 'No response'}")

        # Test 4: Read the newly created file
        print("\n--- Test 4: Read the newly created file ---")
        response4 = await agent.arun("Read the contents of mcp_output.txt")
        print(f"Agent response: {response4.content if response4 else 'No response'}")

        print("\n[SUCCESS] All agent tests completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up session and test files
        if 'session' in locals():
            await session.close()
            print("[SUCCESS] MCP session closed")

        # Remove test files
        for file in [test_file, "mcp_output.txt"]:
            if os.path.exists(file):
                os.remove(file)
                print(f"[SUCCESS] Removed test file: {file}")


async def simple_mcp_demo():
    """Simple demonstration of MCP without requiring OpenAI API"""

    print("\n" + "=" * 50)
    print("Simple MCP Demo (No API Key Required)")
    print("=" * 50)

    # Create test file
    test_file = "simple_test.txt"
    with open(test_file, "w") as f:
        f.write("This is a simple test file for MCP demonstration.")

    session = create_filesystem_mcp_session(".")

    try:
        await session.initialize()
        tools = await session.list_tools()

        print(f"Available tools: {[tool.name for tool in tools]}")

        # Test reading the file directly with MCP
        result = await session.call_tool("read_file", {"path": test_file})

        if not result.isError and result.content:
            content = result.content[0].text
            print(f"File content via MCP: {content}")

        # Test listing directory
        result = await session.call_tool("list_directory", {"path": "."})

        if not result.isError and result.content:
            files = result.content[0].text.split('\n')
            print(f"Files in directory (first 5): {files[:5]}")

        print("[SUCCESS] Simple MCP demo completed successfully!")

    except Exception as e:
        print(f"[ERROR] Error in simple demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await session.close()

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    # Check if OpenAI API key is available
    if os.getenv("OPENAI_API_KEY"):
        print("OpenAI API key found - running full agent example")
        asyncio.run(main())
    else:
        print("OpenAI API key not found - running simple MCP demo")
        print("Set OPENAI_API_KEY environment variable to run the full agent example")
        asyncio.run(simple_mcp_demo())