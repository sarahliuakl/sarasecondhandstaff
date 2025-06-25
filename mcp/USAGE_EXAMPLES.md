# Sara Secondhand Shop MCP Server 使用示例

本文档提供了详细的使用示例，展示如何通过MCP Server与Sara二手商店API进行交互。

## 快速开始

### 1. 配置API连接

在使用任何其他工具之前，需要先配置API连接：

```
使用configure_api工具：
- base_url: http://localhost:5000/api/v1
- api_key: your_actual_api_key_here
```

### 2. 获取API密钥

API密钥可以通过管理后台获取：
1. 访问 http://localhost:5000/admin/login
2. 登录管理员账户
3. 访问"API管理"页面
4. 生成新的API密钥

## 产品管理示例

### 获取产品列表

```
使用get_products工具获取产品列表：
- page: 1
- per_page: 10
- available_only: true
```

预期响应：
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 1,
        "name": "9成新笔记本电脑",
        "price": 650.00,
        "category": "electronics",
        "condition": "9成新",
        "stock_status": "available"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 25,
      "pages": 3
    }
  }
}
```

### 搜索产品

```
使用get_products工具搜索产品：
- search: "笔记本"
- category: "electronics"
- available_only: true
```

### 创建新产品

```
使用create_product工具创建产品：
- name: "9成新iPhone 13"
- description: "功能完好，外观良好，配件齐全"
- price: 800
- category: "electronics"
- condition: "9成新"
- quantity: 1
- specifications: {"brand": "Apple", "model": "iPhone 13", "storage": "128GB"}
```

### 更新产品信息

```
使用update_product工具更新产品：
- product_id: 1
- price: 750
- description: "价格已调整，急售"
- stock_status: "available"
```

### 上传产品图片

首先需要将图片转换为Base64编码：

```bash
# 使用图片助手工具
python image_helper.py product_image.jpg
```

然后使用上传工具：

```
使用upload_product_images工具：
- product_id: 1
- images: [
    {
      "filename": "product_image.jpg",
      "content": "/9j/4AAQSkZJRgABAQEAYABgAAD...", 
      "mime_type": "image/jpeg"
    }
  ]
```

### 删除产品

```
使用delete_product工具：
- product_id: 1
```

## 分类管理示例

### 获取分类列表

```
使用get_categories工具：
- active_only: true
- include_products: false
```

### 创建新分类

```
使用create_category工具：
- name: "smartphones"
- display_name: "智能手机"
- description: "各种品牌的智能手机"
- icon: "fas fa-mobile-alt"
- sort_order: 1
- is_active: true
```

### 批量创建分类

```
使用batch_create_categories工具：
- categories: [
    {
      "name": "laptops",
      "display_name": "笔记本电脑",
      "description": "各品牌笔记本电脑"
    },
    {
      "name": "tablets", 
      "display_name": "平板电脑",
      "description": "iPad及其他平板设备"
    },
    {
      "name": "accessories",
      "display_name": "数码配件",
      "description": "充电器、数据线等配件"
    }
  ]
```

### 更新分类

```
使用update_category工具：
- category_id: 1
- display_name: "智能手机及配件"
- description: "包括手机和相关配件"
- is_active: true
```

### 切换分类状态

```
使用toggle_category工具：
- category_id: 1
```

### 删除分类

```
使用delete_category工具：
- category_id: 1
```

## 实际使用场景

### 场景1：批量上架新商品

1. **创建分类**（如果需要）：
```
使用create_category创建"游戏主机"分类
```

2. **批量创建产品**：
```
使用create_product分别创建：
- PlayStation 5 (condition: "9成新", price: 650)
- Xbox Series X (condition: "8成新", price: 580)
- Nintendo Switch (condition: "9成新", price: 380)
```

3. **上传产品图片**：
```bash
# 转换图片
python image_helper.py ps5_image.jpg ps5_base64.txt
python image_helper.py xbox_image.jpg xbox_base64.txt
python image_helper.py switch_image.jpg switch_base64.txt

# 上传图片
使用upload_product_images分别为每个产品上传图片
```

### 场景2：库存管理和价格调整

1. **查看现有产品**：
```
使用get_products获取所有产品列表
```

2. **批量价格调整**：
```
使用update_product为多个产品调整价格：
- 电子产品类：降价10%
- 家居用品类：降价5%
```

3. **更新产品状态**：
```
使用update_product将售出商品状态改为"sold"
```

### 场景3：分类重组

1. **创建新的分类结构**：
```
使用batch_create_categories创建：
- 电子产品主分类
- 家居用品主分类
- 服装配饰主分类
```

2. **更新现有产品分类**：
```
使用update_product将产品移动到新分类
```

3. **停用旧分类**：
```
使用toggle_category停用不再使用的分类
```

## 图片处理详细说明

### 支持的图片格式
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### 图片大小限制
- 最大文件大小：5MB
- 建议尺寸：800x600像素
- 建议格式：JPEG（文件较小）

### Base64编码工具使用

```bash
# 基本用法
python image_helper.py image.jpg

# 保存到文件
python image_helper.py image.jpg output.txt

# 批量处理
for file in *.jpg; do
    python image_helper.py "$file" "${file%.jpg}_base64.txt"
done
```

### 多图片上传示例

```
使用upload_product_images工具上传多张图片：
- product_id: 1
- images: [
    {
      "filename": "front_view.jpg",
      "content": "base64_content_1...",
      "mime_type": "image/jpeg"
    },
    {
      "filename": "side_view.jpg", 
      "content": "base64_content_2...",
      "mime_type": "image/jpeg"
    },
    {
      "filename": "detail_view.jpg",
      "content": "base64_content_3...",
      "mime_type": "image/jpeg"
    }
  ]
```

## 错误处理

### 常见错误及解决方案

#### 1. 认证错误
```
错误：403 - Invalid API Key
解决：检查API密钥是否正确，使用configure_api重新配置
```

#### 2. 资源不存在
```
错误：404 - Product not found
解决：检查产品ID是否存在，使用get_products确认
```

#### 3. 数据验证错误
```
错误：400 - Validation failed
解决：检查必填字段是否完整，数据格式是否正确
```

#### 4. 图片上传错误
```
错误：400 - Invalid image format
解决：确保图片格式支持，文件大小在限制内，Base64编码正确
```

#### 5. 速率限制
```
错误：429 - Rate limit exceeded
解决：降低请求频率，等待一段时间后重试
```

## 最佳实践

### 1. 数据备份
定期使用get_products和get_categories导出数据：
```
使用get_products导出所有产品数据
使用get_categories导出所有分类数据
```

### 2. 批量操作
对于大量数据操作，使用批量工具：
```
使用batch_create_categories而不是多次create_category
```

### 3. 图片优化
- 上传前压缩图片以减少传输时间
- 使用适当的图片格式（JPEG用于照片，PNG用于图标）
- 为每个产品提供多角度图片

### 4. 错误处理
- 始终检查API响应的success字段
- 记录错误信息以便调试
- 实现重试机制处理临时错误

### 5. 性能优化
- 使用分页避免一次加载太多数据
- 只在必要时包含产品详细信息
- 合理设置请求间隔避免触发速率限制

## 开发建议

### 1. 测试环境
在生产环境使用前，先在测试环境验证：
```bash
# 运行测试
python test_mcp.py
```

### 2. 日志记录
启用详细日志记录以便调试：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. 配置管理
使用配置文件管理不同环境的设置：
```json
{
  "development": {
    "base_url": "http://localhost:5000/api/v1",
    "api_key": "dev_key"
  },
  "production": {
    "base_url": "https://your-domain.com/api/v1", 
    "api_key": "prod_key"
  }
}
```

这些示例应该能帮助你快速上手使用Sara Secondhand Shop MCP Server。如有其他问题，请查看完整的API文档或联系开发团队。