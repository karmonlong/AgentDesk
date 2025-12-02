import asyncio
import os
import argparse
from mcp.server.fastmcp import FastMCP

# 创建 MCP Server
mcp = FastMCP("LocalFilesystem")

@mcp.tool()
def list_directory(path: str) -> str:
    """List files and directories in the specified path."""
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file."
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return "Error: Binary file or unknown encoding."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def get_file_info(path: str) -> str:
    """Get metadata about a file."""
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        stat = os.stat(path)
        return f"Size: {stat.st_size} bytes\nModified: {stat.st_mtime}"
    except Exception as e:
        return f"Error getting info: {str(e)}"

if __name__ == "__main__":
    # 这是一个标准的 MCP Server，可以通过 stdio 运行
    mcp.run()
