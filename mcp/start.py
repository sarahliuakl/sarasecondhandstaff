#!/usr/bin/env python3
"""
启动脚本 - Sara Secondhand Shop MCP Server

简化的启动脚本，支持从配置文件读取设置
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 确保可以导入server模块
sys.path.insert(0, str(Path(__file__).parent))

from server import EcommerceMCPServer
from mcp.server.stdio import stdio_server


async def main():
    """主启动函数"""
    print("🚀 启动 E-commerce API MCP Server...")
    
    # 创建服务器实例
    server_instance = EcommerceMCPServer()
    
    # 优先从环境变量读取配置（支持Claude Desktop配置）
    base_url = os.getenv('ECOMMERCE_API_BASE_URL')
    api_key = os.getenv('ECOMMERCE_API_KEY')
    
    if base_url and api_key:
        server_instance.base_url = base_url.rstrip("/")
        server_instance.api_key = api_key
        print(f"✅ 已从环境变量配置API: {server_instance.base_url}")
        print(f"   API Key: {server_instance.api_key[:8]}..." if server_instance.api_key else "   API Key: 未设置")
    else:
        # 回退到配置文件
        config_path = Path(__file__).parent / "config.json"
        config = {}
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 已加载配置文件: {config_path}")
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
        else:
            print(f"⚠️  配置文件不存在: {config_path}")
        
        # 如果配置文件中有API设置，自动配置
        if config.get("base_url") and config.get("api_key"):
            server_instance.base_url = config["base_url"].rstrip("/")
            server_instance.api_key = config["api_key"]
            print(f"✅ 已从配置文件配置API: {server_instance.base_url}")
            print(f"   API Key: {server_instance.api_key[:8]}..." if server_instance.api_key else "   API Key: 未设置")
        else:
            print("⚠️  API未配置，请在Claude Desktop配置中设置环境变量或使用configure_api工具")
    
    print("📡 MCP Server 准备就绪，等待连接...")
    print("💡 提示：在支持MCP的应用中连接此服务器")
    print("---")
    
    # 启动MCP服务器
    async with stdio_server() as (read_stream, write_stream):
        try:
            await server_instance.server.run(
                read_stream,
                write_stream,
                server_instance.server.create_initialization_options()
            )
        except KeyboardInterrupt:
            print("\n🛑 收到中断信号，正在关闭服务器...")
        except Exception as e:
            print(f"❌ 服务器运行错误: {e}")
        finally:
            await server_instance.cleanup()
            print("✅ 服务器已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)