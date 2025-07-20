"""
MCP server implementation for the memory system.
"""

import json
import sys
from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from memory_mcp.mcp.tools import MemoryToolDefinitions
from memory_mcp.domains.manager import MemoryDomainManager


class MemoryMcpServer:
    """
    MCP server implementation for the memory system.
    
    This class sets up an MCP server that exposes memory-related tools
    and handles MCP protocol communication with Claude Desktop.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Memory MCP Server.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.domain_manager = MemoryDomainManager(config)
        self.app = Server("memory-mcp-server")
        self.tool_definitions = MemoryToolDefinitions(self.domain_manager)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register memory-related handlers with the MCP server."""
        
        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="store_memory",
                    description="Store new information in memory",
                    inputSchema=self.tool_definitions.store_memory_schema
                ),
                Tool(
                    name="retrieve_memory", 
                    description="Retrieve relevant memories based on query",
                    inputSchema=self.tool_definitions.retrieve_memory_schema
                ),
                Tool(
                    name="list_memories",
                    description="List available memories with filtering options", 
                    inputSchema=self.tool_definitions.list_memories_schema
                ),
                Tool(
                    name="update_memory",
                    description="Update existing memory entries",
                    inputSchema=self.tool_definitions.update_memory_schema
                ),
                Tool(
                    name="delete_memory",
                    description="Remove specific memories",
                    inputSchema=self.tool_definitions.delete_memory_schema
                ),
                Tool(
                    name="memory_stats",
                    description="Get statistics about the memory store",
                    inputSchema=self.tool_definitions.memory_stats_schema
                ),
            ]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "store_memory":
                    return await self._handle_store_memory(arguments)
                elif name == "retrieve_memory":
                    return await self._handle_retrieve_memory(arguments)
                elif name == "list_memories":
                    return await self._handle_list_memories(arguments)
                elif name == "update_memory":
                    return await self._handle_update_memory(arguments)
                elif name == "delete_memory":
                    return await self._handle_delete_memory(arguments)
                elif name == "memory_stats":
                    return await self._handle_memory_stats(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": f"Unknown tool: {name}"
                        })
                    )]
            except Exception as e:
                logger.error(f"Error in call_tool for {name}: {str(e)}")
                return [TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    })
                )]
    
    async def _handle_store_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle store_memory tool requests."""
        try:
            memory_id = await self.domain_manager.store_memory(
                memory_type=arguments["type"],
                content=arguments["content"],
                importance=arguments.get("importance", 0.5),
                metadata=arguments.get("metadata", {}),
                context=arguments.get("context", {})
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "memory_id": memory_id
                })
            )]
        except Exception as e:
            logger.error(f"Error in store_memory: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def _handle_retrieve_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle retrieve_memory tool requests."""
        try:
            query = arguments["query"]
            limit = arguments.get("limit", 5)
            memory_types = arguments.get("types", None)
            min_similarity = arguments.get("min_similarity", 0.6)
            include_metadata = arguments.get("include_metadata", False)
            
            memories = await self.domain_manager.retrieve_memories(
                query=query,
                limit=limit,
                memory_types=memory_types,
                min_similarity=min_similarity,
                include_metadata=include_metadata
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "memories": memories
                })
            )]
        except Exception as e:
            logger.error(f"Error in retrieve_memory: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def _handle_list_memories(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle list_memories tool requests."""
        try:
            memory_types = arguments.get("types", None)
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            tier = arguments.get("tier", None)
            include_content = arguments.get("include_content", False)
            
            memories = await self.domain_manager.list_memories(
                memory_types=memory_types,
                limit=limit,
                offset=offset,
                tier=tier,
                include_content=include_content
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "memories": memories
                })
            )]
        except Exception as e:
            logger.error(f"Error in list_memories: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def _handle_update_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle update_memory tool requests."""
        try:
            memory_id = arguments["memory_id"]
            updates = arguments["updates"]
            
            success = await self.domain_manager.update_memory(
                memory_id=memory_id,
                updates=updates
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": success
                })
            )]
        except Exception as e:
            logger.error(f"Error in update_memory: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def _handle_delete_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle delete_memory tool requests."""
        try:
            memory_ids = arguments["memory_ids"]
            
            success = await self.domain_manager.delete_memories(
                memory_ids=memory_ids
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": success
                })
            )]
        except Exception as e:
            logger.error(f"Error in delete_memory: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def _handle_memory_stats(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle memory_stats tool requests."""
        try:
            stats = await self.domain_manager.get_memory_stats()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "stats": stats
                })
            )]
        except Exception as e:
            logger.error(f"Error in memory_stats: {str(e)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    async def start(self) -> None:
        """Start the MCP server."""
        # Initialize the memory domain manager
        await self.domain_manager.initialize()
        
        logger.info("Starting Memory MCP Server using stdio transport")
        
        # Start the server using stdio transport
        async with stdio_server() as streams:
            await self.app.run(
                streams[0],
                streams[1],
                self.app.create_initialization_options()
            )