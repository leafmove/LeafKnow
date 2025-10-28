import json
import subprocess
from functools import partial
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from dataclasses import dataclass

from agno.utils.log import log_debug, log_exception

# Python 3.8 compatible MCP implementation
# This replaces the official mcp package which requires Python 3.10+

try:
    from mcp import ClientSession
    from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent
    from mcp.types import Tool as MCPTool
    MCP_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    log_debug("Official mcp package not available, using Python 3.8 compatible implementation")
    MCP_AVAILABLE = False


from agno.media import Image
from agno.tools.function import ToolResult


# Python 3.8 Compatible MCP Implementation
if not MCP_AVAILABLE:

    @dataclass
    class TextContent:
        """MCP TextContent equivalent for Python 3.8"""
        type: str = "text"
        text: str = ""

        def __post_init__(self):
            if self.type != "text":
                raise ValueError("TextContent must have type 'text'")

    @dataclass
    class ImageContent:
        """MCP ImageContent equivalent for Python 3.8"""
        type: str = "image"
        data: str = ""
        mimeType: str = "image/png"
        url: Optional[str] = None

        def __post_init__(self):
            if self.type != "image":
                raise ValueError("ImageContent must have type 'image'")

    @dataclass
    class EmbeddedResource:
        """MCP EmbeddedResource equivalent for Python 3.8"""
        type: str = "resource"
        resource: Dict[str, Any] = None

        def __post_init__(self):
            if self.resource is None:
                self.resource = {}
            if self.type != "resource":
                raise ValueError("EmbeddedResource must have type 'resource'")

    @dataclass
    class CallToolResult:
        """MCP CallToolResult equivalent for Python 3.8"""
        content: List[Union[TextContent, ImageContent, EmbeddedResource]]
        isError: bool = False

        def __post_init__(self):
            if self.content is None:
                self.content = []

    @dataclass
    class MCPTool:
        """MCP Tool equivalent for Python 3.8"""
        name: str
        description: Optional[str] = None
        inputSchema: Optional[Dict[str, Any]] = None

        def __post_init__(self):
            if self.inputSchema is None:
                self.inputSchema = {"type": "object", "properties": {}}

    class ClientSession:
        """MCP ClientSession equivalent for Python 3.8

        This implementation provides compatibility with the MCP protocol
        while working on Python 3.8. It supports both stdio and HTTP
        communication with MCP servers.
        """

        def __init__(self, server_command: Optional[List[str]] = None, server_url: Optional[str] = None):
            """Initialize a client session

            Args:
                server_command: Command and arguments to start MCP server (for stdio communication)
                server_url: URL of MCP server (for HTTP communication)
            """
            self.server_command = server_command
            self.server_url = server_url
            self.process = None
            self.request_id = 0
            self._initialized = False

        async def initialize(self):
            """Initialize the session with the MCP server"""
            if self._initialized:
                return

            if self.server_command:
                await self._initialize_stdio()
            elif self.server_url:
                await self._initialize_http()
            else:
                raise ValueError("Either server_command or server_url must be provided")

            self._initialized = True
            log_debug("MCP ClientSession initialized successfully")

        async def _initialize_stdio(self):
            """Initialize stdio communication with MCP server"""
            try:
                self.process = subprocess.Popen(
                    self.server_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0
                )

                # Send initialize request
                init_request = {
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "clientInfo": {
                            "name": "agno-mcp-client",
                            "version": "1.0.0"
                        }
                    }
                }

                response = await self._send_request_stdio(init_request)
                if "error" in response:
                    raise Exception(f"MCP initialization failed: {response['error']}")

                log_debug("MCP stdio communication initialized")

            except Exception as e:
                log_exception(f"Failed to initialize stdio communication: {e}")
                raise

        async def _initialize_http(self):
            """Initialize HTTP communication with MCP server"""
            # For HTTP, we don't need persistent initialization
            # Each request will be sent independently
            log_debug("MCP HTTP communication initialized")

        async def _send_request_stdio(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """Send request via stdio and wait for response"""
            if not self.process:
                raise RuntimeError("MCP server process not started")

            try:
                # Send request
                request_json = json.dumps(request) + "\n"
                self.process.stdin.write(request_json)
                self.process.stdin.flush()

                # Read response
                response_line = self.process.stdout.readline()
                if not response_line:
                    raise RuntimeError("No response from MCP server")

                response = json.loads(response_line.strip())
                return response

            except Exception as e:
                log_exception(f"Failed to send stdio request: {e}")
                raise

        async def _send_request_http(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """Send request via HTTP and wait for response"""
            try:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.server_url,
                        json=request,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status != 200:
                            raise RuntimeError(f"HTTP error {response.status}: {await response.text()}")

                        result = await response.json()
                        return result

            except ImportError:
                raise RuntimeError("aiohttp is required for HTTP communication. Install with: pip install aiohttp")
            except Exception as e:
                log_exception(f"Failed to send HTTP request: {e}")
                raise

        def _next_id(self) -> int:
            """Get next request ID"""
            self.request_id += 1
            return self.request_id

        async def list_tools(self) -> List[MCPTool]:
            """List available tools from the MCP server"""
            await self.initialize()

            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/list",
                "params": {}
            }

            if self.server_command:
                response = await self._send_request_stdio(request)
            else:
                response = await self._send_request_http(request)

            if "error" in response:
                raise Exception(f"Failed to list tools: {response['error']}")

            tools_data = response.get("result", {}).get("tools", [])
            tools = []

            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description"),
                    inputSchema=tool_data.get("inputSchema")
                )
                tools.append(tool)

            return tools

        async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Call a tool on the MCP server

            Args:
                name: Name of the tool to call
                arguments: Arguments to pass to the tool

            Returns:
                CallToolResult with the tool's response
            """
            await self.initialize()

            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }

            log_debug(f"Calling MCP tool '{name}' with arguments: {arguments}")

            if self.server_command:
                response = await self._send_request_stdio(request)
            else:
                response = await self._send_request_http(request)

            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                log_debug(f"MCP tool '{name}' returned error: {error_msg}")

                # Return error result
                error_content = [TextContent(text=f"Error: {error_msg}")]
                return CallToolResult(content=error_content, isError=True)

            result_data = response.get("result", {})
            content_data = result_data.get("content", [])

            # Parse content into appropriate types
            content = []
            for item in content_data:
                content_type = item.get("type", "text")

                if content_type == "text":
                    text_content = TextContent(
                        type="text",
                        text=item.get("text", "")
                    )
                    content.append(text_content)

                elif content_type == "image":
                    image_content = ImageContent(
                        type="image",
                        data=item.get("data", ""),
                        mimeType=item.get("mimeType", "image/png"),
                        url=item.get("url")
                    )
                    content.append(image_content)

                elif content_type == "resource":
                    resource_content = EmbeddedResource(
                        type="resource",
                        resource=item.get("resource", {})
                    )
                    content.append(resource_content)

                else:
                    # Unknown type, include as text
                    unknown_content = TextContent(
                        type="text",
                        text=f"Unknown content type {content_type}: {json.dumps(item)}"
                    )
                    content.append(unknown_content)

            is_error = result_data.get("isError", False)
            return CallToolResult(content=content, isError=is_error)

        async def close(self):
            """Close the client session"""
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                except Exception as e:
                    log_exception(f"Error closing MCP process: {e}")
                finally:
                    self.process = None

            self._initialized = False
            log_debug("MCP ClientSession closed")


def get_entrypoint_for_tool(tool: MCPTool, session: ClientSession):
    """
    Return an entrypoint for an MCP tool.

    Args:
        tool: The MCP tool to create an entrypoint for
        session: The session to use

    Returns:
        Callable: The entrypoint function for the tool
    """
    from agno.agent import Agent

    async def call_tool(agent: Agent, tool_name: str, **kwargs) -> ToolResult:
        try:
            log_debug(f"Calling MCP Tool '{tool_name}' with args: {kwargs}")
            result: CallToolResult = await session.call_tool(tool_name, kwargs)  # type: ignore

            # Return an error if the tool call failed
            if result.isError:
                return ToolResult(content=f"Error from MCP tool '{tool_name}': {result.content}")

            # Process the result content
            response_str = ""
            images = []

            for content_item in result.content:
                if isinstance(content_item, TextContent):
                    text_content = content_item.text

                    # Parse as JSON to check for custom image format
                    try:
                        parsed_json = json.loads(text_content)
                        if (
                            isinstance(parsed_json, dict)
                            and parsed_json.get("type") == "image"
                            and "data" in parsed_json
                        ):
                            log_debug("Found custom JSON image format in TextContent")

                            # Extract image data
                            image_data = parsed_json.get("data")
                            mime_type = parsed_json.get("mimeType", "image/png")

                            if image_data and isinstance(image_data, str):
                                import base64

                                try:
                                    image_bytes = base64.b64decode(image_data)
                                except Exception as e:
                                    log_debug(f"Failed to decode base64 image data: {e}")
                                    image_bytes = None

                                if image_bytes:
                                    img_artifact = Image(
                                        id=str(uuid4()),
                                        url=None,
                                        content=image_bytes,
                                        mime_type=mime_type,
                                    )
                                    images.append(img_artifact)
                                    response_str += "Image has been generated and added to the response.\n"
                                    continue

                    except (json.JSONDecodeError, TypeError):
                        pass

                    response_str += text_content + "\n"

                elif isinstance(content_item, ImageContent):
                    # Handle standard MCP ImageContent
                    image_data = getattr(content_item, "data", None)

                    if image_data and isinstance(image_data, str):
                        import base64

                        try:
                            image_data = base64.b64decode(image_data)
                        except Exception as e:
                            log_debug(f"Failed to decode base64 image data: {e}")
                            image_data = None

                    img_artifact = Image(
                        id=str(uuid4()),
                        url=getattr(content_item, "url", None),
                        content=image_data,
                        mime_type=getattr(content_item, "mimeType", "image/png"),
                    )
                    images.append(img_artifact)
                    response_str += "Image has been generated and added to the response.\n"
                elif isinstance(content_item, EmbeddedResource):
                    # Handle embedded resources
                    if hasattr(content_item.resource, 'model_dump_json'):
                        resource_str = content_item.resource.model_dump_json()
                    else:
                        resource_str = json.dumps(content_item.resource)
                    response_str += f"[Embedded resource: {resource_str}]\n"
                else:
                    # Handle other content types
                    response_str += f"[Unsupported content type: {content_item.type}]\n"

            return ToolResult(
                content=response_str.strip(),
                images=images if images else None,
            )
        except Exception as e:
            log_exception(f"Failed to call MCP tool '{tool_name}': {e}")
            return ToolResult(content=f"Error: {e}")

    return partial(call_tool, tool_name=tool.name)


# Additional utility functions for Python 3.8 compatibility

def create_mcp_session_from_command(command: List[str]) -> ClientSession:
    """
    Create an MCP ClientSession from a command list.

    Args:
        command: List of command and arguments to start MCP server

    Returns:
        ClientSession instance
    """
    return ClientSession(server_command=command)


def create_mcp_session_from_url(url: str) -> ClientSession:
    """
    Create an MCP ClientSession from a URL.

    Args:
        url: URL of the MCP server (HTTP endpoint)

    Returns:
        ClientSession instance
    """
    return ClientSession(server_url=url)


class MCPToolWrapper:
    """
    Wrapper class that integrates MCP tools with agno's Function system.

    This class allows MCP tools to be used seamlessly with agno agents
    by providing the same interface as agno's native tools.
    """

    def __init__(self, tool: MCPTool, session: ClientSession):
        """Initialize the wrapper

        Args:
            tool: The MCP tool to wrap
            session: The MCP client session
        """
        self.tool = tool
        self.session = session
        self.entrypoint = get_entrypoint_for_tool(tool, session)

    def to_agno_function(self) -> 'Function':
        """Convert to agno Function

        Returns:
            agno Function instance
        """
        from agno.tools.function import Function

        return Function(
            name=self.tool.name,
            description=self.tool.description or f"MCP Tool: {self.tool.name}",
            parameters=self.tool.inputSchema or {"type": "object", "properties": {}},
            entrypoint=self.entrypoint
        )


# Convenience function for common MCP server configurations
def create_filesystem_mcp_session(root_path: str = ".") -> ClientSession:
    """
    Create a filesystem MCP session for file operations.

    Args:
        root_path: Root directory for file operations

    Returns:
        ClientSession configured for filesystem operations
    """
    # Create a simple filesystem server script
    server_script = f'''
import sys
import json
import os

# Basic filesystem server for MCP compatibility
root_path = "{root_path}"

def handle_request(request):
    method = request.get('method')
    params = request.get('params', {{}})

    if method == 'initialize':
        return {{
            'result': {{
                'protocolVersion': '2024-11-05',
                'capabilities': {{}},
                'serverInfo': {{'name': 'filesystem-server', 'version': '1.0.0'}}
            }}
        }}
    elif method == 'tools/list':
        return {{
            'result': {{
                'tools': [
                    {{
                        'name': 'read_file',
                        'description': 'Read a file',
                        'inputSchema': {{
                            'type': 'object',
                            'properties': {{
                                'path': {{'type': 'string', 'description': 'File path'}}
                            }},
                            'required': ['path']
                        }}
                    }},
                    {{
                        'name': 'write_file',
                        'description': 'Write to a file',
                        'inputSchema': {{
                            'type': 'object',
                            'properties': {{
                                'path': {{'type': 'string', 'description': 'File path'}},
                                'content': {{'type': 'string', 'description': 'File content'}}
                            }},
                            'required': ['path', 'content']
                        }}
                    }},
                    {{
                        'name': 'list_directory',
                        'description': 'List directory contents',
                        'inputSchema': {{
                            'type': 'object',
                            'properties': {{
                                'path': {{'type': 'string', 'description': 'Directory path'}}
                            }},
                            'required': ['path']
                        }}
                    }}
                ]
            }}
        }}
    elif method == 'tools/call':
        tool_name = params.get('name')
        arguments = params.get('arguments', {{}})

        try:
            if tool_name == 'read_file':
                path = os.path.join(root_path, arguments['path'])
                with open(path, 'r') as f:
                    content = f.read()
                return {{
                    'result': {{
                        'content': [{{'type': 'text', 'text': content}}]
                    }}
                }}
            elif tool_name == 'write_file':
                path = os.path.join(root_path, arguments['path'])
                with open(path, 'w') as f:
                    f.write(arguments['content'])
                return {{
                    'result': {{
                        'content': [{{'type': 'text', 'text': f"File written: {{arguments['path']}}"}}]
                    }}
                }}
            elif tool_name == 'list_directory':
                path = os.path.join(root_path, arguments['path'])
                items = os.listdir(path)
                return {{
                    'result': {{
                        'content': [{{'type': 'text', 'text': '\\n'.join(items)}}]
                    }}
                }}
            else:
                return {{
                    'error': {{'code': -32601, 'message': f"Unknown tool: {{tool_name}}"}}
                }}
        except Exception as e:
            return {{
                'error': {{'code': -32602, 'message': str(e)}}
            }}
    else:
        return {{
            'error': {{'code': -32601, 'message': f"Unknown method: {{method}}"}}
        }}

# Read JSON-RPC requests from stdin
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            request = json.loads(line)
            response = handle_request(request)
            response['id'] = request.get('id')
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {{
                'id': request.get('id') if 'request' in locals() else None,
                'error': {{'code': -32700, 'message': str(e)}}
            }}
            print(json.dumps(error_response))
            sys.stdout.flush()
'''

    return create_mcp_session_from_command(["python", "-c", server_script])
