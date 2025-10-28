#!/usr/bin/env python3
"""
Test script to verify that the agno.tools.mcp import works correctly
with the Python 3.8 compatible MCP implementation.
"""

import sys
import os

# Add the agno package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_import():
    """Test importing the MCP tools"""
    print("Testing agno.tools.mcp import...")

    try:
        from agno.tools.mcp import MCPTools, MultiMCPTools
        print("[SUCCESS] Imported MCPTools and MultiMCPTools")

        # Test creating an MCPTools instance
        from agno.utils.mcp import create_filesystem_mcp_session

        print("[SUCCESS] Imported create_filesystem_mcp_session")

        # Test basic instantiation
        toolkit = MCPTools(command="echo hello")
        print("[SUCCESS] Created MCPTools instance")

        print("All imports successful!")
        return True

    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)