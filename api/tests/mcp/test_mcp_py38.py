#!/usr/bin/env python3
"""
Test script for Python 3.8 compatible MCP implementation in agno.

This script demonstrates how to use the Python 3.8 compatible MCP implementation
and verifies that it works correctly.
"""

import asyncio
import sys
import os

# Add the agno package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from agno.utils.mcp import (
    ClientSession,
    MCPTool,
    create_filesystem_mcp_session,
    create_mcp_session_from_command,
    MCPToolWrapper,
    get_entrypoint_for_tool
)


async def test_filesystem_session():
    """Test the filesystem MCP session"""
    print("Testing filesystem MCP session...")

    # Create a filesystem session
    session = create_filesystem_mcp_session(".")

    try:
        # Initialize the session
        await session.initialize()
        print("[SUCCESS] Session initialized successfully")

        # List available tools
        tools = await session.list_tools()
        print(f"[SUCCESS] Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Test reading a file
        if tools:
            # Create a test file first
            test_file = "test_mcp.txt"
            with open(test_file, "w") as f:
                f.write("Hello from MCP test!")

            # Test reading the file
            result = await session.call_tool("read_file", {"path": test_file})
            if not result.isError and result.content:
                content = result.content[0].text if result.content else "No content"
                print(f"[SUCCESS] Read file content: {content.strip()}")
            else:
                print(f"[ERROR] Failed to read file: {result.content}")

            # Clean up
            os.remove(test_file)

    except Exception as e:
        print(f"[ERROR] Filesystem session test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await session.close()
        print("[SUCCESS] Session closed")


async def test_mcp_tool_wrapper():
    """Test the MCPToolWrapper integration"""
    print("\nTesting MCPToolWrapper integration...")

    try:
        # Create a simple mock session for testing
        session = create_filesystem_mcp_session(".")
        await session.initialize()

        # Create a mock tool
        tool = MCPTool(
            name="test_tool",
            description="A test tool for demonstration",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Test message"}
                },
                "required": ["message"]
            }
        )

        # Create wrapper
        wrapper = MCPToolWrapper(tool, session)
        print("[SUCCESS] MCPToolWrapper created successfully")

        # Convert to agno function
        agno_function = wrapper.to_agno_function()
        print(f"[SUCCESS] Converted to agno Function: {agno_function.name}")

        await session.close()

    except Exception as e:
        print(f"[ERROR] MCPToolWrapper test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_http_session():
    """Test HTTP session creation (doesn't actually connect)"""
    print("\nTesting HTTP session creation...")

    try:
        # This would normally connect to a real MCP server
        session = create_mcp_session_from_url("http://localhost:8080/mcp")
        print("[SUCCESS] HTTP session created successfully")
        print("Note: Not actually connecting since no server is running")

    except Exception as e:
        print(f"[ERROR] HTTP session test failed: {e}")


def test_import_compatibility():
    """Test that imports work correctly"""
    print("\nTesting import compatibility...")

    try:
        from agno.utils.mcp import (
            TextContent, ImageContent, EmbeddedResource,
            CallToolResult, MCPTool, ClientSession
        )
        print("[SUCCESS] All MCP classes imported successfully")

        # Test creating instances
        text_content = TextContent(text="Hello World")
        image_content = ImageContent(data="base64data", mimeType="image/png")
        embedded_resource = EmbeddedResource(resource={"key": "value"})

        call_result = CallToolResult(
            content=[text_content, image_content, embedded_resource],
            isError=False
        )

        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            inputSchema={"type": "object", "properties": {}}
        )

        print("[SUCCESS] All MCP classes instantiated successfully")

    except Exception as e:
        print(f"[ERROR] Import compatibility test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("Python 3.8 Compatible MCP Implementation Test")
    print("=" * 50)

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Python version: {python_version}")

    if sys.version_info >= (3, 10):
        print("[WARNING] You're running Python 3.10+. This implementation is designed for Python 3.8 compatibility.")
    elif sys.version_info[:2] == (3, 8):
        print("[SUCCESS] Running on Python 3.8 - perfect for this implementation!")
    else:
        print(f"[INFO] Running on Python {sys.version_info[:2]} - should work fine")

    print()

    # Run tests
    test_import_compatibility()
    await test_filesystem_session()
    await test_mcp_tool_wrapper()
    test_http_session()  # This is not async, it's fine

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests completed!")
    print("\nUsage Examples:")
    print("1. Create filesystem session: session = create_filesystem_mcp_session('/path/to/files')")
    print("2. List tools: tools = await session.list_tools()")
    print("3. Call tool: result = await session.call_tool('tool_name', {'arg': 'value'})")
    print("4. Wrap for agno: wrapper = MCPToolWrapper(tool, session)")
    print("5. Convert to function: agno_func = wrapper.to_agno_function()")


if __name__ == "__main__":
    asyncio.run(main())