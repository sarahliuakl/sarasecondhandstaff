#!/usr/bin/env python3
"""
MCP Server CRUD操作测试

测试产品和分类的增删改查功能
注意：需要API服务器运行在localhost:5000
"""

import asyncio
import json
import sys
import base64
from pathlib import Path

# 确保可以导入server模块
sys.path.insert(0, str(Path(__file__).parent))

from server import EcommerceMCPServer


async def test_crud_operations():
    """测试CRUD操作"""
    print("🧪 开始测试 E-commerce API MCP Server CRUD操作")
    print("=" * 60)
    
    # 创建服务器实例
    server = EcommerceMCPServer()
    
    # 配置API连接
    print("1️⃣ 配置API连接")
    config_result = await server._configure_api({
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "test_api_key_12345"  # 使用测试API密钥
    })
    print(f"   {config_result.content[0].text}")
    print()
    
    try:
        # 测试分类CRUD操作
        print("2️⃣ 测试分类CRUD操作")
        print("=" * 40)
        
        # 创建分类
        print("📝 创建新分类...")
        create_category_result = await server._create_category({
            "name": "test_electronics",
            "display_name": "测试电子产品",
            "description": "用于测试的电子产品分类",
            "icon": "fas fa-laptop",
            "sort_order": 1,
            "is_active": True
        })
        print(f"   结果: {create_category_result.content[0].text[:200]}...")
        print()
        
        # 获取分类列表
        print("📋 获取分类列表...")
        get_categories_result = await server._get_categories({
            "active_only": True,
            "include_products": False
        })
        print(f"   结果: {get_categories_result.content[0].text[:200]}...")
        print()
        
        # 尝试获取刚创建的分类详情（假设ID为1）
        print("🔍 获取分类详情...")
        get_category_result = await server._get_category({"category_id": 1})
        print(f"   结果: {get_category_result.content[0].text[:200]}...")
        print()
        
        # 更新分类
        print("✏️ 更新分类...")
        update_category_result = await server._update_category({
            "category_id": 1,
            "display_name": "更新后的测试电子产品",
            "description": "已更新的分类描述"
        })
        print(f"   结果: {update_category_result.content[0].text[:200]}...")
        print()
        
        # 测试产品CRUD操作
        print("3️⃣ 测试产品CRUD操作")
        print("=" * 40)
        
        # 创建产品
        print("📝 创建新产品...")
        create_product_result = await server._create_product({
            "name": "测试笔记本电脑",
            "description": "用于测试的笔记本电脑",
            "price": 1200.00,
            "category": "test_electronics",
            "condition": "9成新",
            "stock_status": "available",
            "quantity": 1,
            "specifications": {
                "brand": "Test Brand",
                "model": "Test Model",
                "cpu": "Intel i7",
                "ram": "16GB"
            }
        })
        print(f"   结果: {create_product_result.content[0].text[:200]}...")
        print()
        
        # 获取产品列表
        print("📋 获取产品列表...")
        get_products_result = await server._get_products({
            "page": 1,
            "per_page": 10,
            "available_only": True
        })
        print(f"   结果: {get_products_result.content[0].text[:200]}...")
        print()
        
        # 获取产品详情（假设ID为1）
        print("🔍 获取产品详情...")
        get_product_result = await server._get_product({"product_id": 1})
        print(f"   结果: {get_product_result.content[0].text[:200]}...")
        print()
        
        # 更新产品
        print("✏️ 更新产品...")
        update_product_result = await server._update_product({
            "product_id": 1,
            "price": 1100.00,
            "description": "已降价的测试笔记本电脑",
            "condition": "8成新"
        })
        print(f"   结果: {update_product_result.content[0].text[:200]}...")
        print()
        
        # 测试图片上传
        print("4️⃣ 测试图片上传")
        print("=" * 40)
        
        # 创建一个小的测试图片数据（1x1像素的PNG）
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        print("📸 上传产品图片...")
        upload_images_result = await server._upload_product_images({
            "product_id": 1,
            "images": [
                {
                    "filename": "test_image.png",
                    "content": test_image_base64,
                    "mime_type": "image/png"
                }
            ]
        })
        print(f"   结果: {upload_images_result.content[0].text[:200]}...")
        print()
        
        # 测试搜索功能
        print("5️⃣ 测试搜索功能")
        print("=" * 40)
        
        print("🔎 搜索产品...")
        search_products_result = await server._get_products({
            "search": "笔记本",
            "available_only": True
        })
        print(f"   结果: {search_products_result.content[0].text[:200]}...")
        print()
        
        # 测试批量操作
        print("6️⃣ 测试批量操作")
        print("=" * 40)
        
        print("📦 批量创建分类...")
        batch_create_result = await server._batch_create_categories({
            "categories": [
                {
                    "name": "test_books",
                    "display_name": "测试图书",
                    "description": "用于测试的图书分类"
                },
                {
                    "name": "test_toys",
                    "display_name": "测试玩具",
                    "description": "用于测试的玩具分类"
                }
            ]
        })
        print(f"   结果: {batch_create_result.content[0].text[:200]}...")
        print()
        
        print("🎉 所有CRUD操作测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        await server.cleanup()


async def test_error_handling():
    """测试错误处理"""
    print("\n7️⃣ 测试错误处理")
    print("=" * 40)
    
    server = EcommerceMCPServer()
    
    # 配置API连接
    await server._configure_api({
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "invalid_api_key"  # 使用无效的API密钥
    })
    
    try:
        # 尝试获取产品列表（应该失败）
        print("🚫 测试无效API密钥...")
        result = await server._get_products({})
        print(f"   结果: {result.content[0].text[:200]}...")
        
        # 尝试获取不存在的产品
        print("🚫 测试获取不存在的产品...")
        result = await server._get_product({"product_id": 99999})
        print(f"   结果: {result.content[0].text[:200]}...")
        
        # 尝试创建无效的产品
        print("🚫 测试创建无效产品...")
        result = await server._create_product({
            "name": "",  # 空名称
            "price": -100  # 负价格
        })
        print(f"   结果: {result.content[0].text[:200]}...")
        
    except Exception as e:
        print(f"   错误处理测试: {str(e)}")
    
    finally:
        await server.cleanup()


async def main():
    """主测试函数"""
    print("🚀 E-commerce API MCP Server CRUD测试套件")
    print("🔗 需要API服务器运行在 http://localhost:5000")
    print("🔑 确保已配置有效的API密钥")
    print("=" * 80)
    
    # 运行CRUD操作测试
    await test_crud_operations()
    
    # 运行错误处理测试
    await test_error_handling()
    
    print("\n" + "=" * 80)
    print("📊 测试完成")
    print("💡 提示：如果看到连接错误，请确保API服务器正在运行")
    print("💡 提示：如果看到认证错误，请检查API密钥是否正确")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
    except Exception as e:
        print(f"❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()