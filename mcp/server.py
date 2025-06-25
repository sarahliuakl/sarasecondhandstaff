#!/usr/bin/env python3
"""
Sara Secondhand Shop MCP Server

A Model Context Protocol server that provides tools to interact with 
the Sara Secondhand Shop API for product and category management.
"""

import asyncio
import json
import base64
from typing import Any, Dict, List, Optional
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Role,
)
import os
from pathlib import Path


class SaraShopMCPServer:
    """MCP Server for Sara Secondhand Shop API integration"""
    
    def __init__(self):
        self.server = Server("sara-shop")
        self.base_url = "http://localhost:5000/api/v1"  # Default local development URL
        self.api_key = None
        self.client = None
        
        # Setup server handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        # List available tools
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools"""
            return [
                # Product management tools
                Tool(
                    name="get_products",
                    description="获取产品列表，支持分页、搜索和筛选",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer", "description": "页码，默认1"},
                            "per_page": {"type": "integer", "description": "每页数量，默认20，最大100"},
                            "category": {"type": "string", "description": "分类筛选"},
                            "status": {"type": "string", "description": "状态筛选"},
                            "search": {"type": "string", "description": "搜索关键词"},
                            "available_only": {"type": "boolean", "description": "仅显示可用商品"}
                        }
                    }
                ),
                Tool(
                    name="get_product",
                    description="获取单个产品的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"}
                        },
                        "required": ["product_id"]
                    }
                ),
                Tool(
                    name="create_product",
                    description="创建新产品",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "产品名称"},
                            "description": {"type": "string", "description": "产品描述"},
                            "price": {"type": "number", "description": "价格"},
                            "category": {"type": "string", "description": "分类"},
                            "condition": {"type": "string", "description": "成色"},
                            "stock_status": {"type": "string", "description": "库存状态", "default": "available"},
                            "quantity": {"type": "integer", "description": "数量", "default": 1},
                            "low_stock_threshold": {"type": "integer", "description": "低库存阈值", "default": 1},
                            "track_inventory": {"type": "boolean", "description": "跟踪库存", "default": True},
                            "face_to_face_only": {"type": "boolean", "description": "仅见面交易", "default": False},
                            "image_urls": {"type": "array", "items": {"type": "string"}, "description": "图片URL列表"},
                            "specifications": {"type": "object", "description": "产品规格"}
                        },
                        "required": ["name", "price", "category"]
                    }
                ),
                Tool(
                    name="update_product",
                    description="更新产品信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "name": {"type": "string", "description": "产品名称"},
                            "description": {"type": "string", "description": "产品描述"},
                            "price": {"type": "number", "description": "价格"},
                            "category": {"type": "string", "description": "分类"},
                            "condition": {"type": "string", "description": "成色"},
                            "stock_status": {"type": "string", "description": "库存状态"},
                            "quantity": {"type": "integer", "description": "数量"},
                            "low_stock_threshold": {"type": "integer", "description": "低库存阈值"},
                            "track_inventory": {"type": "boolean", "description": "跟踪库存"},
                            "face_to_face_only": {"type": "boolean", "description": "仅见面交易"},
                            "image_urls": {"type": "array", "items": {"type": "string"}, "description": "图片URL列表"},
                            "specifications": {"type": "object", "description": "产品规格"},
                            "update_images": {"type": "boolean", "description": "是否更新图片", "default": False},
                            "keep_existing_images": {"type": "boolean", "description": "是否保留现有图片", "default": True}
                        },
                        "required": ["product_id"]
                    }
                ),
                Tool(
                    name="delete_product",
                    description="删除产品",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"}
                        },
                        "required": ["product_id"]
                    }
                ),
                Tool(
                    name="upload_product_images",
                    description="为产品上传图片（Base64编码）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "images": {
                                "type": "array", 
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "filename": {"type": "string", "description": "文件名"},
                                        "content": {"type": "string", "description": "Base64编码的图片内容"},
                                        "mime_type": {"type": "string", "description": "MIME类型", "default": "image/jpeg"}
                                    },
                                    "required": ["filename", "content"]
                                },
                                "description": "图片文件列表"
                            }
                        },
                        "required": ["product_id", "images"]
                    }
                ),
                # Category management tools
                Tool(
                    name="get_categories",
                    description="获取分类列表",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active_only": {"type": "boolean", "description": "仅显示激活的分类", "default": True},
                            "include_products": {"type": "boolean", "description": "包含产品列表", "default": False}
                        }
                    }
                ),
                Tool(
                    name="get_category",
                    description="获取单个分类的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category_id": {"type": "integer", "description": "分类ID"}
                        },
                        "required": ["category_id"]
                    }
                ),
                Tool(
                    name="create_category",
                    description="创建新分类",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "分类名称"},
                            "display_name": {"type": "string", "description": "显示名称"},
                            "description": {"type": "string", "description": "分类描述"},
                            "slug": {"type": "string", "description": "URL别名"},
                            "icon": {"type": "string", "description": "图标"},
                            "sort_order": {"type": "integer", "description": "排序", "default": 0},
                            "is_active": {"type": "boolean", "description": "是否激活", "default": True}
                        },
                        "required": ["name", "display_name"]
                    }
                ),
                Tool(
                    name="update_category",
                    description="更新分类信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category_id": {"type": "integer", "description": "分类ID"},
                            "name": {"type": "string", "description": "分类名称"},
                            "display_name": {"type": "string", "description": "显示名称"},
                            "description": {"type": "string", "description": "分类描述"},
                            "slug": {"type": "string", "description": "URL别名"},
                            "icon": {"type": "string", "description": "图标"},
                            "sort_order": {"type": "integer", "description": "排序"},
                            "is_active": {"type": "boolean", "description": "是否激活"}
                        },
                        "required": ["category_id"]
                    }
                ),
                Tool(
                    name="delete_category",
                    description="删除分类",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category_id": {"type": "integer", "description": "分类ID"}
                        },
                        "required": ["category_id"]
                    }
                ),
                Tool(
                    name="toggle_category",
                    description="切换分类状态（激活/停用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category_id": {"type": "integer", "description": "分类ID"}
                        },
                        "required": ["category_id"]
                    }
                ),
                Tool(
                    name="batch_create_categories",
                    description="批量创建分类",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "分类名称"},
                                        "display_name": {"type": "string", "description": "显示名称"},
                                        "description": {"type": "string", "description": "分类描述"},
                                        "slug": {"type": "string", "description": "URL别名"},
                                        "icon": {"type": "string", "description": "图标"},
                                        "sort_order": {"type": "integer", "description": "排序", "default": 0},
                                        "is_active": {"type": "boolean", "description": "是否激活", "default": True}
                                    },
                                    "required": ["name", "display_name"]
                                },
                                "description": "分类列表"
                            }
                        },
                        "required": ["categories"]
                    }
                ),
                # Configuration tool
                Tool(
                    name="configure_api",
                    description="配置API连接信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_url": {"type": "string", "description": "API基础URL"},
                            "api_key": {"type": "string", "description": "API密钥"}
                        },
                        "required": ["base_url", "api_key"]
                    }
                )
            ]
        
        # Handle tool calls
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool execution"""
            try:
                if name == "configure_api":
                    return await self._configure_api(arguments)
                
                # Check if API is configured
                if not self.api_key:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="错误：请先使用configure_api工具配置API连接信息"
                        )]
                    )
                
                # Ensure HTTP client is initialized
                if not self.client:
                    self.client = httpx.AsyncClient(timeout=30.0)
                
                # Product management tools
                if name == "get_products":
                    return await self._get_products(arguments)
                elif name == "get_product":
                    return await self._get_product(arguments)
                elif name == "create_product":
                    return await self._create_product(arguments)
                elif name == "update_product":
                    return await self._update_product(arguments)
                elif name == "delete_product":
                    return await self._delete_product(arguments)
                elif name == "upload_product_images":
                    return await self._upload_product_images(arguments)
                
                # Category management tools
                elif name == "get_categories":
                    return await self._get_categories(arguments)
                elif name == "get_category":
                    return await self._get_category(arguments)
                elif name == "create_category":
                    return await self._create_category(arguments)
                elif name == "update_category":
                    return await self._update_category(arguments)
                elif name == "delete_category":
                    return await self._delete_category(arguments)
                elif name == "toggle_category":
                    return await self._toggle_category(arguments)
                elif name == "batch_create_categories":
                    return await self._batch_create_categories(arguments)
                
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"未知工具: {name}"
                        )]
                    )
                    
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"工具执行失败: {str(e)}"
                    )]
                )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with API key"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _configure_api(self, args: Dict[str, Any]) -> CallToolResult:
        """Configure API connection"""
        self.base_url = args["base_url"].rstrip("/")
        self.api_key = args["api_key"]
        
        # Initialize HTTP client
        if self.client:
            await self.client.aclose()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"API配置成功！\n基础URL: {self.base_url}\nAPI Key: {self.api_key[:8]}..."
            )]
        )
    
    # Product management methods
    async def _get_products(self, args: Dict[str, Any]) -> CallToolResult:
        """Get products list"""
        params = {k: v for k, v in args.items() if v is not None}
        
        response = await self.client.get(
            f"{self.base_url}/products",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功获取产品列表\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"获取产品列表失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _get_product(self, args: Dict[str, Any]) -> CallToolResult:
        """Get single product"""
        product_id = args["product_id"]
        
        response = await self.client.get(
            f"{self.base_url}/products/{product_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功获取产品详情\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"获取产品详情失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _create_product(self, args: Dict[str, Any]) -> CallToolResult:
        """Create new product"""
        # Remove None values
        product_data = {k: v for k, v in args.items() if v is not None}
        
        response = await self.client.post(
            f"{self.base_url}/products",
            headers=self._get_headers(),
            json=product_data
        )
        
        if response.status_code == 201:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功创建产品\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"创建产品失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _update_product(self, args: Dict[str, Any]) -> CallToolResult:
        """Update product"""
        product_id = args.pop("product_id")
        update_data = {k: v for k, v in args.items() if v is not None}
        
        params = {}
        if "update_images" in update_data:
            params["update_images"] = update_data.pop("update_images")
        if "keep_existing_images" in update_data:
            params["keep_existing_images"] = update_data.pop("keep_existing_images")
        
        response = await self.client.put(
            f"{self.base_url}/products/{product_id}",
            headers=self._get_headers(),
            json=update_data,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功更新产品\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"更新产品失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _delete_product(self, args: Dict[str, Any]) -> CallToolResult:
        """Delete product"""
        product_id = args["product_id"]
        
        response = await self.client.delete(
            f"{self.base_url}/products/{product_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功删除产品\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"删除产品失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _upload_product_images(self, args: Dict[str, Any]) -> CallToolResult:
        """Upload product images"""
        product_id = args["product_id"]
        images = args["images"]
        
        # Prepare multipart form data
        files = []
        for img in images:
            # Decode base64 content
            try:
                content = base64.b64decode(img["content"])
                files.append(("images", (img["filename"], content, img.get("mime_type", "image/jpeg"))))
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"图片解码失败: {str(e)}"
                    )]
                )
        
        # Upload using multipart/form-data
        headers = {"X-API-Key": self.api_key}  # Don't set Content-Type for multipart
        
        response = await self.client.post(
            f"{self.base_url}/products/{product_id}/images",
            headers=headers,
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功上传产品图片\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"上传产品图片失败: {response.status_code} - {response.text}"
                )]
            )
    
    # Category management methods
    async def _get_categories(self, args: Dict[str, Any]) -> CallToolResult:
        """Get categories list"""
        params = {k: v for k, v in args.items() if v is not None}
        
        response = await self.client.get(
            f"{self.base_url}/categories",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功获取分类列表\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"获取分类列表失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _get_category(self, args: Dict[str, Any]) -> CallToolResult:
        """Get single category"""
        category_id = args["category_id"]
        
        response = await self.client.get(
            f"{self.base_url}/categories/{category_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功获取分类详情\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"获取分类详情失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _create_category(self, args: Dict[str, Any]) -> CallToolResult:
        """Create new category"""
        category_data = {k: v for k, v in args.items() if v is not None}
        
        response = await self.client.post(
            f"{self.base_url}/categories",
            headers=self._get_headers(),
            json=category_data
        )
        
        if response.status_code == 201:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功创建分类\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"创建分类失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _update_category(self, args: Dict[str, Any]) -> CallToolResult:
        """Update category"""
        category_id = args.pop("category_id")
        update_data = {k: v for k, v in args.items() if v is not None}
        
        response = await self.client.put(
            f"{self.base_url}/categories/{category_id}",
            headers=self._get_headers(),
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功更新分类\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"更新分类失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _delete_category(self, args: Dict[str, Any]) -> CallToolResult:
        """Delete category"""
        category_id = args["category_id"]
        
        response = await self.client.delete(
            f"{self.base_url}/categories/{category_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功删除分类\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"删除分类失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _toggle_category(self, args: Dict[str, Any]) -> CallToolResult:
        """Toggle category status"""
        category_id = args["category_id"]
        
        response = await self.client.patch(
            f"{self.base_url}/categories/{category_id}/toggle",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功切换分类状态\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"切换分类状态失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def _batch_create_categories(self, args: Dict[str, Any]) -> CallToolResult:
        """Batch create categories"""
        categories_data = {"categories": args["categories"]}
        
        response = await self.client.post(
            f"{self.base_url}/categories/batch",
            headers=self._get_headers(),
            json=categories_data
        )
        
        if response.status_code == 201:
            data = response.json()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"成功批量创建分类\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"批量创建分类失败: {response.status_code} - {response.text}"
                )]
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()


async def main():
    """Main entry point"""
    server_instance = SaraShopMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        try:
            await server_instance.server.run(
                read_stream,
                write_stream,
                server_instance.server.create_initialization_options()
            )
        finally:
            await server_instance.cleanup()


if __name__ == "__main__":
    asyncio.run(main())