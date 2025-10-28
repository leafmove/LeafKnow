# Python 3.8 Compatible MCP Implementation for Agno

This document describes the Python 3.8 compatible Model Context Protocol (MCP) implementation in the Agno library.

## Overview

The official MCP package requires Python 3.10+, but this implementation provides full MCP protocol compatibility while working on Python 3.8. It implements all the essential MCP classes and functionality needed for agno agents to interact with MCP servers.

## Key Features

- **Python 3.8+ Compatible**: Works on Python 3.8 and higher versions
- **Full MCP Protocol Support**: Implements core MCP protocol features
- **Multiple Communication Methods**: Supports both stdio and HTTP communication
- **Agno Integration**: Seamless integration with agno's Function and ToolResult systems
- **Built-in Filesystem Server**: Includes a basic filesystem MCP server for testing

## Installation

No additional dependencies required! The implementation is built into agno's `utils.mcp` module.

## Quick Start

### Basic Usage

```python
import asyncio
from agno.utils.mcp import create_filesystem_mcp_session

async def main():
    # Create a filesystem MCP session
    session = create_filesystem_mcp_session(".")

    try:
        # Initialize the session
        await session.initialize()

        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        # Call a tool
        result = await session.call_tool("read_file", {"path": "example.txt"})
        if not result.isError:
            content = result.content[0].text
            print(f"File content: {content}")

    finally:
        await session.close()

asyncio.run(main())
```

### Integration with Agno Agents

```python
from agno.agent import Agent
from agno.utils.mcp import create_filesystem_mcp_session, MCPToolWrapper

async def setup_agent_with_mcp():
    # Create MCP session
    session = create_filesystem_mcp_session(".")
    await session.initialize()

    # Get available tools
    tools = await session.list_tools()

    # Convert MCP tools to agno functions
    agno_functions = []
    for mcp_tool in tools:
        wrapper = MCPToolWrapper(mcp_tool, session)
        agno_func = wrapper.to_agno_function()
        agno_functions.append(agno_func)

    # Create agent with MCP tools
    agent = Agent(tools=agno_functions)
    return agent, session

# Usage
agent, session = await setup_agent_with_mcp()
try:
    result = await agent.arun("Read the contents of test.txt")
    print(result)
finally:
    await session.close()
```

## API Reference

### Core Classes

#### `ClientSession`

Main MCP client session for communicating with MCP servers.

```python
# Create session from command (stdio communication)
session = ClientSession(server_command=["python", "server.py"])

# Create session from URL (HTTP communication)
session = ClientSession(server_url="http://localhost:8080/mcp")
```

**Methods:**
- `await initialize()`: Initialize the session with the MCP server
- `await list_tools() -> List[MCPTool]`: Get list of available tools
- `await call_tool(name: str, arguments: dict) -> CallToolResult`: Call a tool
- `await close()`: Close the session and clean up resources

#### `MCPTool`

Represents an MCP tool with its metadata.

```python
tool = MCPTool(
    name="calculator",
    description="Basic calculator operations",
    inputSchema={
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        "required": ["operation", "a", "b"]
    }
)
```

#### `CallToolResult`

Result from calling an MCP tool.

```python
result = CallToolResult(
    content=[TextContent(text="Result: 42")],
    isError=False
)
```

#### Content Types

- `TextContent`: Text-based content
- `ImageContent`: Image data (base64 encoded)
- `EmbeddedResource`: Embedded resources

### Utility Functions

#### `create_filesystem_mcp_session(root_path: str = ".")`

Create a pre-configured filesystem MCP session.

```python
session = create_filesystem_mcp_session("/path/to/files")
```

**Available tools:**
- `read_file`: Read file contents
- `write_file`: Write content to file
- `list_directory`: List directory contents

#### `create_mcp_session_from_command(command: List[str])`

Create MCP session from command list.

```python
# Using Node.js MCP server
session = create_mcp_session_from_command([
    "npx", "-y", "@modelcontextprotocol/server-filesystem", "/path"
])
```

#### `create_mcp_session_from_url(url: str)`

Create MCP session from HTTP URL.

```python
session = create_mcp_session_from_url("http://localhost:8080/mcp")
```

#### `MCPToolWrapper`

Wrapper class to integrate MCP tools with agno's Function system.

```python
wrapper = MCPToolWrapper(mcp_tool, session)
agno_function = wrapper.to_agno_function()
```

## Server Compatibility

This implementation works with any MCP-compliant server, including:

### Official MCP Servers
- `@modelcontextprotocol/server-filesystem`
- `@modelcontextprotocol/server-github`
- `@modelcontextprotocol/server-sqlite`
- `@modelcontextprotocol/server-postgres`
- `@modelcontextprotocol/server-playwright`

### Custom Servers
Any server implementing the MCP protocol (JSON-RPC 2.0) will work.

## Communication Methods

### Stdio Communication

Default method for Node.js-based MCP servers.

```python
session = ClientSession(server_command=[
    "npx", "-y", "@modelcontextprotocol/server-filesystem", "/path"
])
```

### HTTP Communication

For servers that provide HTTP endpoints.

```python
session = ClientSession(server_url="http://localhost:8080/mcp")

# Note: Requires aiohttp for HTTP communication
# Install with: pip install aiohttp
```

## Error Handling

The implementation includes robust error handling:

```python
try:
    result = await session.call_tool("invalid_tool", {})
except Exception as e:
    print(f"Tool call failed: {e}")

# Check result for errors
if result.isError:
    print(f"Tool returned error: {result.content}")
```

## Testing

Run the included test script to verify compatibility:

```bash
python test_mcp_py38.py
```

The test covers:
- Import compatibility
- Session initialization
- Tool listing and calling
- Agno integration
- Both stdio and HTTP communication

## Migration from Official MCP Package

If you're currently using the official MCP package:

1. **No code changes needed** - the API is compatible
2. **Just import from agno** instead of the mcp package
3. **All functionality preserved** - same protocol, same behavior

```python
# Before (requires Python 3.10+)
from mcp import ClientSession
from mcp.types import CallToolResult, TextContent

# After (Python 3.8+ compatible)
from agno.utils.mcp import ClientSession, CallToolResult, TextContent
```

## Performance Considerations

- **Stdio Communication**: Fast for local servers, minimal overhead
- **HTTP Communication**: Slightly higher overhead but more flexible
- **Built-in Filesystem Server**: Optimized for basic file operations
- **Session Reuse**: Reuse sessions when possible for better performance

## Troubleshooting

### Common Issues

1. **"MCP server not responding"**
   - Check server command is correct
   - Ensure server supports stdio communication
   - Verify server process starts successfully

2. **"Tool not found"**
   - Call `list_tools()` to see available tools
   - Check tool name spelling
   - Verify server provides the expected tools

3. **"HTTP communication failed"**
   - Install aiohttp: `pip install aiohttp`
   - Check server URL is correct
   - Verify server is running and accessible

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now MCP operations will log detailed information
session = create_filesystem_mcp_session(".")
await session.initialize()
```

## Examples

### Example 1: Simple File Operations

```python
import asyncio
from agno.utils.mcp import create_filesystem_mcp_session

async def file_operations_example():
    session = create_filesystem_mcp_session(".")
    await session.initialize()

    try:
        # Write a file
        await session.call_tool("write_file", {
            "path": "hello.txt",
            "content": "Hello, MCP!"
        })

        # Read the file back
        result = await session.call_tool("read_file", {"path": "hello.txt"})
        print(f"Content: {result.content[0].text}")

        # List directory
        result = await session.call_tool("list_directory", {"path": "."})
        print(f"Files: {result.content[0].text}")

    finally:
        await session.close()

asyncio.run(file_operations_example())
```

### Example 2: Custom Server Integration

```python
import asyncio
from agno.utils.mcp import ClientSession

async def custom_server_example():
    # Assuming you have a custom MCP server at custom_server.py
    session = ClientSession(server_command=["python", "custom_server.py"])

    try:
        await session.initialize()
        tools = await session.list_tools()

        for tool in tools:
            print(f"Tool: {tool.name} - {tool.description}")

            # Call the tool with sample arguments
            if tool.name == "my_tool":
                result = await session.call_tool("my_tool", {"param": "value"})
                print(f"Result: {result.content[0].text}")

    finally:
        await session.close()

asyncio.run(custom_server_example())
```

## Contributing

When contributing to this implementation:

1. **Maintain Python 3.8 compatibility** - avoid newer syntax features
2. **Follow MCP protocol specification** - ensure compatibility with official servers
3. **Add comprehensive tests** - test both success and error cases
4. **Document new features** - update this README for new functionality

## License

This implementation follows the same license as the Agno library.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Run the test script to verify compatibility
3. Open an issue on the Agno repository

---

**Note**: This implementation is designed to be a drop-in replacement for the official MCP package when Python 3.8 compatibility is required. It maintains full protocol compliance while providing the same API interface.