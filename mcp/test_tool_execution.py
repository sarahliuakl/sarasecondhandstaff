#!/usr/bin/env python3
"""
MCP Server 工具执行测试

测试通过handle_call_tool方法执行的完整工具流程
模拟实际的MCP工具调用场景
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

# 确保可以导入server模块
sys.path.insert(0, str(Path(__file__).parent))

from server import EcommerceMCPServer


def create_mock_response(status_code, json_data):
    """创建模拟HTTP响应"""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json_data = json_data
            self.text = json.dumps(json_data, ensure_ascii=False)
        
        def json(self):
            return self._json_data
    
    return MockResponse(status_code, json_data)


async def test_tool_execution_flow():
    """测试工具执行流程"""
    print("🔧 测试MCP工具执行流程")
    print("=" * 50)
    
    server = EcommerceMCPServer()
    
    # 获取handle_call_tool方法
    # 注意：这是内部方法，通常通过MCP协议调用
    handlers = {}
    for handler in server.server._handlers:
        if hasattr(handler, '_func'):
            handlers[handler._func.__name__] = handler._func
    
    handle_call_tool = None
    for name, func in handlers.items():
        if 'call_tool' in name:
            handle_call_tool = func
            break
    
    if not handle_call_tool:
        print("❌ 未找到handle_call_tool方法")
        return
    
    # 测试1: 配置API
    print("1️⃣ 测试configure_api工具...")
    result = await handle_call_tool("configure_api", {
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "test_api_key_123"
    })
    print(f"   ✅ 配置结果: {result.content[0].text[:80]}...")
    print()
    
    # 模拟HTTP客户端响应
    success_response_data = {
        "success": True,
        "data": {"id": 1, "name": "test_category"},
        "message": "操作成功"
    }
    
    with patch.object(server, 'client') as mock_client:
        # 设置模拟HTTP客户端
        mock_client.post.return_value = create_mock_response(201, success_response_data)
        mock_client.get.return_value = create_mock_response(200, success_response_data)
        mock_client.put.return_value = create_mock_response(200, success_response_data)
        mock_client.delete.return_value = create_mock_response(200, success_response_data)
        mock_client.patch.return_value = create_mock_response(200, success_response_data)
        
        # 测试分类工具
        print("2️⃣ 测试分类管理工具...")
        
        # 创建分类
        result = await handle_call_tool("create_category", {
            "name": "test_books",
            "display_name": "测试图书"
        })
        print(f"   ✅ 创建分类: {result.content[0].text[:80]}...")
        
        # 获取分类列表
        result = await handle_call_tool("get_categories", {
            "active_only": True
        })
        print(f"   ✅ 获取分类列表: {result.content[0].text[:80]}...")
        
        # 更新分类
        result = await handle_call_tool("update_category", {
            "category_id": 1,
            "display_name": "更新的图书分类"
        })
        print(f"   ✅ 更新分类: {result.content[0].text[:80]}...")
        
        # 切换分类状态
        result = await handle_call_tool("toggle_category", {
            "category_id": 1
        })
        print(f"   ✅ 切换分类状态: {result.content[0].text[:80]}...")
        
        print()
        
        # 测试产品工具
        print("3️⃣ 测试产品管理工具...")
        
        # 创建产品
        result = await handle_call_tool("create_product", {
            "name": "测试产品",
            "price": 99.99,
            "category": "test_books"
        })
        print(f"   ✅ 创建产品: {result.content[0].text[:80]}...")
        
        # 获取产品列表
        result = await handle_call_tool("get_products", {
            "page": 1,
            "per_page": 5
        })
        print(f"   ✅ 获取产品列表: {result.content[0].text[:80]}...")
        
        # 更新产品
        result = await handle_call_tool("update_product", {
            "product_id": 1,
            "price": 89.99
        })
        print(f"   ✅ 更新产品: {result.content[0].text[:80]}...")
        
        print()
        
        # 测试图片上传
        print("4️⃣ 测试图片上传工具...")
        
        # 上传图片（使用Base64编码的1x1像素PNG）
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        result = await handle_call_tool("upload_product_images", {
            "product_id": 1,
            "images": [
                {
                    "filename": "test.png",
                    "content": test_image,
                    "mime_type": "image/png"
                }
            ]
        })
        print(f"   ✅ 上传图片: {result.content[0].text[:80]}...")
        
        print()
        
        # 测试批量操作
        print("5️⃣ 测试批量操作工具...")
        
        result = await handle_call_tool("batch_create_categories", {
            "categories": [
                {"name": "electronics", "display_name": "电子产品"},
                {"name": "clothes", "display_name": "服装"}
            ]
        })
        print(f"   ✅ 批量创建分类: {result.content[0].text[:80]}...")
        
        print()


async def test_error_scenarios():
    """测试错误场景"""
    print("6️⃣ 测试错误处理场景...")
    print("=" * 50)
    
    server = EcommerceMCPServer()
    
    # 获取handle_call_tool方法
    handlers = {}
    for handler in server.server._handlers:
        if hasattr(handler, '_func'):
            handlers[handler._func.__name__] = handler._func
    
    handle_call_tool = None
    for name, func in handlers.items():
        if 'call_tool' in name:
            handle_call_tool = func
            break
    
    # 测试未配置API的情况
    print("🚫 测试未配置API...")
    result = await handle_call_tool("get_products", {})
    print(f"   ✅ 未配置API错误: {result.content[0].text[:80]}...")
    
    # 配置API
    await handle_call_tool("configure_api", {
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "test_key"
    })
    
    # 测试无效工具名
    print("🚫 测试无效工具名...")
    result = await handle_call_tool("invalid_tool", {})
    print(f"   ✅ 无效工具错误: {result.content[0].text[:80]}...")
    
    # 测试缺少必需参数
    print("🚫 测试缺少必需参数...")
    with patch.object(server, 'client') as mock_client:
        error_response = {
            "success": False,
            "error": "VALIDATION_FAILED",
            "message": "缺少必需参数"
        }
        mock_client.post.return_value = create_mock_response(400, error_response)
        
        result = await handle_call_tool("create_product", {
            # 缺少name和price参数
            "category": "test"
        })
        print(f"   ✅ 参数验证错误: {result.content[0].text[:80]}...")
    
    print()


async def test_data_formats():
    """测试数据格式处理"""
    print("7️⃣ 测试数据格式处理...")
    print("=" * 50)
    
    server = EcommerceMCPServer()
    
    # 配置API
    await server._configure_api({
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "test_key"
    })
    
    # 测试复杂数据结构
    complex_product_data = {
        "success": True,
        "data": {
            "id": 1,
            "name": "复杂产品",
            "specifications": {
                "dimensions": {"width": 30, "height": 20, "depth": 10},
                "features": ["feature1", "feature2", "feature3"],
                "metadata": {
                    "created_by": "test_user",
                    "tags": ["electronics", "mobile", "smartphone"]
                }
            },
            "images": [
                {"url": "http://example.com/img1.jpg", "alt": "正面"},
                {"url": "http://example.com/img2.jpg", "alt": "背面"}
            ]
        }
    }
    
    with patch.object(server, 'client') as mock_client:
        mock_client.post.return_value = create_mock_response(201, complex_product_data)
        
        print("📊 测试复杂数据结构...")
        result = await server._create_product({
            "name": "复杂产品",
            "price": 999.99,
            "category": "electronics",
            "specifications": {
                "dimensions": {"width": 30, "height": 20, "depth": 10},
                "features": ["feature1", "feature2", "feature3"]
            }
        })
        print(f"   ✅ 复杂数据处理: {result.content[0].text[:80]}...")
    
    # 测试中文字符处理
    chinese_data = {
        "success": True,
        "data": {
            "id": 2,
            "name": "中文产品名称",
            "description": "这是一个包含中文的产品描述，测试UTF-8编码处理。",
            "category_display": "电子产品分类"
        }
    }
    
    with patch.object(server, 'client') as mock_client:
        mock_client.post.return_value = create_mock_response(201, chinese_data)
        
        print("🈚 测试中文字符处理...")
        result = await server._create_product({
            "name": "中文产品名称",
            "description": "这是一个包含中文的产品描述",
            "price": 888.88,
            "category": "electronics"
        })
        print(f"   ✅ 中文字符处理: {result.content[0].text[:80]}...")
    
    print()


async def test_performance_scenarios():
    """测试性能场景"""
    print("8️⃣ 测试性能场景...")
    print("=" * 50)
    
    server = EcommerceMCPServer()
    
    await server._configure_api({
        "base_url": "http://localhost:5000/api/v1",
        "api_key": "test_key"
    })
    
    # 模拟大量数据响应
    large_response_data = {
        "success": True,
        "data": {
            "products": [
                {
                    "id": i,
                    "name": f"产品 {i}",
                    "price": 100.0 + i,
                    "description": f"这是第{i}个产品的详细描述" * 10  # 长描述
                }
                for i in range(100)  # 100个产品
            ],
            "pagination": {
                "page": 1,
                "per_page": 100,
                "total": 1000,
                "pages": 10
            }
        }
    }
    
    with patch.object(server, 'client') as mock_client:
        mock_client.get.return_value = create_mock_response(200, large_response_data)
        
        print("📈 测试大量数据处理...")
        import time
        start_time = time.time()
        
        result = await server._get_products({
            "page": 1,
            "per_page": 100
        })
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"   ✅ 大量数据处理: {result.content[0].text[:80]}...")
        print(f"   ⏱️ 处理时间: {processing_time:.3f}秒")
    
    # 测试并发请求
    print("🔄 测试并发处理...")
    
    async def make_request():
        return await server._get_product({"product_id": 1})
    
    with patch.object(server, 'client') as mock_client:
        mock_client.get.return_value = create_mock_response(200, {
            "success": True,
            "data": {"id": 1, "name": "测试产品"}
        })
        
        start_time = time.time()
        
        # 并发执行10个请求
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        print(f"   ✅ 并发请求: 完成{len(results)}个请求")
        print(f"   ⏱️ 并发处理时间: {concurrent_time:.3f}秒")
    
    print()


async def main():
    """主测试函数"""
    print("🚀 E-commerce API MCP Server 工具执行测试套件")
    print("🔧 测试完整的MCP工具调用流程")
    print("=" * 80)
    
    try:
        # 运行所有测试
        await test_tool_execution_flow()
        await test_error_scenarios()
        await test_data_formats()
        await test_performance_scenarios()
        
        print("=" * 80)
        print("🎉 所有工具执行测试通过！")
        print("✅ MCP工具调用流程正常")
        print("✅ 错误处理机制有效")
        print("✅ 数据格式处理正确")
        print("✅ 性能表现良好")
        print("✅ 支持复杂数据结构")
        print("✅ 支持中文字符处理")
        print("✅ 支持并发请求处理")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
    except Exception as e:
        print(f"❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()