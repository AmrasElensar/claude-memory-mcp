"""
Command-line entry point for the Memory MCP Server
"""

import asyncio
import os
import sys
import logging
import argparse
from pathlib import Path

from loguru import logger

from memory_mcp.mcp.memory_server import MemoryMcpServer
from memory_mcp.utils.config import load_config


async def main() -> None:
    """Entry point for the Memory MCP Server."""
    parser = argparse.ArgumentParser(description="Memory MCP Server")
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--memory-file", 
        type=str, 
        help="Path to memory file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    
    # Load configuration
    config_path = args.config
    if not config_path:
        config_dir = os.environ.get("MCP_CONFIG_DIR", os.path.expanduser("~/.memory_mcp/config"))
        config_path = os.path.join(config_dir, "config.json")
    
    config = load_config(config_path)
    
    # Override memory file path if specified
    if args.memory_file:
        config["memory"]["file_path"] = args.memory_file
    elif "MEMORY_FILE_PATH" in os.environ:
        config["memory"]["file_path"] = os.environ["MEMORY_FILE_PATH"]
    
    memory_file_path = config["memory"]["file_path"]
    
    # Ensure memory file path exists
    memory_file_dir = os.path.dirname(memory_file_path)
    os.makedirs(memory_file_dir, exist_ok=True)
    
    logger.info(f"Starting Memory MCP Server")
    logger.info(f"Using configuration from {config_path}")
    logger.info(f"Using memory file: {memory_file_path}")
    
    # Start the server
    server = MemoryMcpServer(config)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
