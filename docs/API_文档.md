# Sara二手商店 - RESTful API 文档

## 概述

Sara二手商店提供完整的RESTful API，支持产品管理、分类管理、库存查询等功能。API采用JSON格式进行数据交换，使用API Key进行认证。

### API版本
- **当前版本：** v1.0.0
- **基础URL：** `http://your-domain.com/api/v1`

### 认证方式

API使用API Key进行认证，支持两种方式提供：

1. **HTTP头部（推荐）：**
   ```
   X-API-Key: your_api_key_here
   ```

2. **查询参数：**
   ```
   ?api_key=your_api_key_here
   ```

### 响应格式

所有API响应都采用统一的JSON格式：

**成功响应：**
```json
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}
```

**错误响应：**
```json
{
    "success": false,
    "error": "ERROR_CODE",
    "message": "错误描述"
}
```

### 速率限制

- **默认限制：** 每小时100次请求
- **高频端点：** 部分查询端点支持更高频率（如库存检查：500次/小时）
- **批量操作：** 限制更严格（如批量创建：10次/小时）

## API端点

### 1. 通用端点

#### 健康检查
- **端点：** `GET /api/v1/health`
- **认证：** 无需认证
- **描述：** 检查API服务状态

**响应示例：**
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Sara Secondhand Shop API"
    }
}
```

#### API信息
- **端点：** `GET /api/v1/info`
- **认证：** 需要API Key
- **描述：** 获取API基本信息和端点列表

### 2. 产品API

#### 获取产品列表
- **端点：** `GET /api/v1/products`
- **认证：** 需要API Key
- **限制：** 200次/小时

**查询参数：**
- `page` (int): 页码，默认1
- `per_page` (int): 每页数量，默认20，最大100
- `category` (string): 分类筛选
- `status` (string): 状态筛选
- `search` (string): 搜索关键词
- `available_only` (boolean): 仅显示可用商品

**响应示例：**
```json
{
    "success": true,
    "data": {
        "products": [
            {
                "id": 1,
                "name": "9成新笔记本电脑",
                "description": "多角度实拍，性能优良...",
                "price": 650.00,
                "category": "electronics",
                "category_display": "电子产品",
                "condition": "9成新",
                "stock_status": "available",
                "quantity": 1,
                "images": ["https://..."],
                "specifications": {...},
                "created_at": "2025-06-25T10:00:00",
                "updated_at": "2025-06-25T10:00:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 50,
            "pages": 3,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

#### 获取产品详情
- **端点：** `GET /api/v1/products/{id}`
- **认证：** 需要API Key
- **限制：** 500次/小时

#### 创建产品
- **端点：** `POST /api/v1/products`
- **认证：** 需要API Key
- **限制：** 50次/小时
- **内容类型：** `application/json` 或 `multipart/form-data`

**请求体：**
```json
{
    "name": "产品名称",
    "description": "产品描述",
    "price": 100.00,
    "category": "electronics",
    "condition": "9成新",
    "stock_status": "available",
    "quantity": 1,
    "low_stock_threshold": 1,
    "track_inventory": true,
    "face_to_face_only": false,
    "image_urls": ["https://..."],
    "specifications": {
        "brand": "Dell",
        "model": "Inspiron"
    }
}
```

#### 更新产品
- **端点：** `PUT /api/v1/products/{id}`
- **认证：** 需要API Key
- **限制：** 50次/小时

**查询参数：**
- `update_images` (boolean): 是否更新图片
- `keep_existing_images` (boolean): 是否保留现有图片

#### 删除产品
- **端点：** `DELETE /api/v1/products/{id}`
- **认证：** 需要API Key
- **限制：** 30次/小时

#### 上传产品图片
- **端点：** `POST /api/v1/products/{id}/images`
- **认证：** 需要API Key
- **限制：** 50次/小时
- **内容类型：** `multipart/form-data`

**请求参数：**
- `images` (file[]): 图片文件列表

#### 更新产品库存
- **端点：** `PATCH /api/v1/products/{id}/inventory`
- **认证：** 需要API Key
- **限制：** 100次/小时

**请求体：**
```json
{
    "action": "set|add|reduce",
    "quantity": 10
}
```

### 3. 分类API

#### 获取分类列表
- **端点：** `GET /api/v1/categories`
- **认证：** 需要API Key
- **限制：** 200次/小时

**查询参数：**
- `active_only` (boolean): 仅显示激活的分类，默认true
- `include_products` (boolean): 包含产品列表，默认false

#### 获取分类详情
- **端点：** `GET /api/v1/categories/{id}`
- **认证：** 需要API Key
- **限制：** 300次/小时

#### 创建分类
- **端点：** `POST /api/v1/categories`
- **认证：** 需要API Key
- **限制：** 30次/小时

**请求体：**
```json
{
    "name": "electronics",
    "display_name": "电子产品",
    "description": "包括电脑、手机等",
    "slug": "electronics",
    "icon": "fas fa-laptop",
    "sort_order": 1,
    "is_active": true
}
```

#### 更新分类
- **端点：** `PUT /api/v1/categories/{id}`
- **认证：** 需要API Key
- **限制：** 50次/小时

#### 删除分类
- **端点：** `DELETE /api/v1/categories/{id}`
- **认证：** 需要API Key
- **限制：** 20次/小时

#### 切换分类状态
- **端点：** `PATCH /api/v1/categories/{id}/toggle`
- **认证：** 需要API Key
- **限制：** 100次/小时

#### 批量创建分类
- **端点：** `POST /api/v1/categories/batch`
- **认证：** 需要API Key
- **限制：** 10次/小时

**请求体：**
```json
{
    "categories": [
        {
            "name": "books",
            "display_name": "图书",
            "description": "各类书籍"
        },
        {
            "name": "toys",
            "display_name": "玩具",
            "description": "儿童玩具"
        }
    ]
}
```

#### 搜索分类
- **端点：** `GET /api/v1/categories/search`
- **认证：** 需要API Key
- **限制：** 200次/小时

**查询参数：**
- `q` (string): 搜索关键词
- `active_only` (boolean): 仅搜索激活的分类

### 4. 库存API

#### 获取库存统计
- **端点：** `GET /api/v1/inventory/stats`
- **认证：** 需要API Key
- **限制：** 100次/小时

**响应示例：**
```json
{
    "success": true,
    "data": {
        "overview": {
            "total_products": 50,
            "available_products": 45,
            "total_quantity": 120,
            "low_stock_count": 5,
            "out_of_stock_count": 2
        },
        "by_category": [
            {
                "category_id": 1,
                "category_name": "electronics",
                "category_display_name": "电子产品",
                "total_products": 20,
                "available_products": 18,
                "total_quantity": 50
            }
        ],
        "trend": [...],
        "generated_at": "2025-06-25T10:00:00"
    }
}
```

#### 获取低库存商品
- **端点：** `GET /api/v1/inventory/low-stock`
- **认证：** 需要API Key
- **限制：** 100次/小时

**查询参数：**
- `limit` (int): 限制数量，默认50，最大200
- `category` (string): 分类筛选

#### 获取缺货商品
- **端点：** `GET /api/v1/inventory/out-of-stock`
- **认证：** 需要API Key
- **限制：** 100次/小时

#### 检查单个产品库存
- **端点：** `GET /api/v1/inventory/check/{product_id}`
- **认证：** 需要API Key
- **限制：** 500次/小时

#### 批量检查库存
- **端点：** `POST /api/v1/inventory/bulk-check`
- **认证：** 需要API Key
- **限制：** 50次/小时

**请求体：**
```json
{
    "product_ids": [1, 2, 3, 4, 5]
}
```

#### 获取库存警报
- **端点：** `GET /api/v1/inventory/alerts`
- **认证：** 需要API Key
- **限制：** 100次/小时

#### 生成库存报告
- **端点：** `GET /api/v1/inventory/report`
- **认证：** 需要API Key
- **限制：** 20次/小时

**查询参数：**
- `format` (string): 报告格式，summary|detailed
- `category` (string): 分类筛选
- `include_images` (boolean): 包含图片信息

## 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| API_NOT_CONFIGURED | 503 | API Key未配置 |
| MISSING_API_KEY | 401 | 缺少API Key |
| INVALID_API_KEY | 403 | API Key无效 |
| RATE_LIMIT_EXCEEDED | 429 | 超过速率限制 |
| VALIDATION_FAILED | 400 | 数据验证失败 |
| NOT_FOUND | 404 | 资源不存在 |
| INVALID_CONTENT_TYPE | 400 | 无效的内容类型 |
| MISSING_DATA | 400 | 请求数据为空 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

## 使用示例

### JavaScript (Fetch API)

```javascript
// 获取产品列表
const response = await fetch('/api/v1/products?page=1&per_page=10', {
    headers: {
        'X-API-Key': 'your_api_key_here',
        'Content-Type': 'application/json'
    }
});

const data = await response.json();
if (data.success) {
    console.log('产品列表:', data.data.products);
} else {
    console.error('错误:', data.message);
}

// 创建产品
const newProduct = {
    name: '测试产品',
    price: 100.00,
    category: 'electronics',
    condition: '9成新'
};

const createResponse = await fetch('/api/v1/products', {
    method: 'POST',
    headers: {
        'X-API-Key': 'your_api_key_here',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(newProduct)
});

const createData = await createResponse.json();
```

### Python (requests)

```python
import requests

# API配置
API_BASE_URL = 'http://your-domain.com/api/v1'
API_KEY = 'your_api_key_here'

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

# 获取产品列表
response = requests.get(f'{API_BASE_URL}/products', headers=headers)
data = response.json()

if data['success']:
    products = data['data']['products']
    print(f'找到 {len(products)} 个产品')
else:
    print(f'错误: {data["message"]}')

# 创建产品
new_product = {
    'name': '测试产品',
    'price': 100.00,
    'category': 'electronics',
    'condition': '9成新'
}

response = requests.post(f'{API_BASE_URL}/products', 
                        headers=headers, 
                        json=new_product)
```

### cURL

```bash
# 获取产品列表
curl -X GET "http://your-domain.com/api/v1/products" \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json"

# 创建产品
curl -X POST "http://your-domain.com/api/v1/products" \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
         "name": "测试产品",
         "price": 100.00,
         "category": "electronics",
         "condition": "9成新"
     }'

# 上传图片
curl -X POST "http://your-domain.com/api/v1/products/1/images" \
     -H "X-API-Key: your_api_key_here" \
     -F "images=@image1.jpg" \
     -F "images=@image2.jpg"
```

## 管理和配置

### API Key管理

1. 登录管理后台
2. 导航到"API管理"页面
3. 生成新的API Key或管理现有的Key
4. 保存API Key到安全位置

### 监控和日志

API调用会被记录到系统日志中，包括：
- 请求时间
- API Key（部分显示）
- 请求端点
- 响应状态

### 安全建议

1. **保护API Key：** 不要在客户端代码中硬编码API Key
2. **使用HTTPS：** 生产环境必须使用HTTPS
3. **定期轮换：** 定期更新API Key
4. **监控使用：** 监控API调用频率和模式
5. **限制访问：** 根据需要限制API访问权限

---

**文档版本：** 1.0.0  
**创建时间：** 2025-06-25  
**最后更新：** 2025-06-25