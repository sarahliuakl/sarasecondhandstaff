# E-commerce API MCP Server

一个Model Context Protocol (MCP) 服务器，用于与电商API进行交互，提供产品和分类管理功能。

## 功能特性

### 产品管理
- ✅ 获取产品列表（支持分页、搜索、筛选）
- ✅ 获取单个产品详情
- ✅ 创建新产品
- ✅ 更新产品信息
- ✅ 删除产品
- ✅ 上传产品图片（Base64编码）

### 分类管理
- ✅ 获取分类列表
- ✅ 获取单个分类详情
- ✅ 创建新分类
- ✅ 更新分类信息
- ✅ 删除分类
- ✅ 切换分类状态
- ✅ 批量创建分类

## 安装和使用

### 1. 安装依赖

```bash
cd mcp
pip install -r requirements.txt
```

### 2. 配置API连接

编辑 `config.json` 文件，设置你的API基础URL和API密钥：

```json
{
  "base_url": "http://your-domain.com/api/v1",
  "api_key": "your_actual_api_key_here"
}
```

### 3. 运行MCP Server

```bash
python server.py
```

### 4. 在支持MCP的应用中使用

将此MCP服务器添加到支持MCP的应用（如Claude Desktop）中：

#### Claude Desktop配置

在Claude Desktop的配置文件中添加：

```json
{
  "mcpServers": {
    "ecommerce-api": {
      "command": "python",
      "args": ["/path/to/ecommerce/mcp/start.py"],
      "env": {
        "ECOMMERCE_API_BASE_URL": "http://localhost:5000/api/v1",
        "ECOMMERCE_API_KEY": "your_actual_api_key_here"
      },
      "description": "E-commerce API MCP Server - 产品和分类管理工具"
    }
  }
}
```

**配置说明：**
- `ECOMMERCE_API_BASE_URL`: 你的API基础URL
- `ECOMMERCE_API_KEY`: 你的实际API密钥
- 这样配置后无需修改config.json文件

## 工具说明

### 配置工具

#### `configure_api`
配置API连接信息（当环境变量未设置时使用）

**参数：**
- `base_url`: API基础URL
- `api_key`: API密钥

**示例：**
```
使用configure_api工具配置连接到http://localhost:5000/api/v1，API密钥为你的实际密钥
```

**注意：** 如果在Claude Desktop中设置了环境变量，将优先使用环境变量配置，无需调用此工具。

### 产品管理工具

#### `get_products`
获取产品列表，支持分页和筛选

**参数：**
- `page` (可选): 页码，默认1
- `per_page` (可选): 每页数量，默认20，最大100
- `category` (可选): 分类筛选
- `status` (可选): 状态筛选
- `search` (可选): 搜索关键词
- `available_only` (可选): 仅显示可用商品

#### `get_product`
获取单个产品详情

**参数：**
- `product_id`: 产品ID

#### `create_product`
创建新产品

**必需参数：**
- `name`: 产品名称
- `price`: 价格
- `category`: 分类

**可选参数：**
- `description`: 产品描述
- `condition`: 成色
- `stock_status`: 库存状态
- `quantity`: 数量
- `specifications`: 产品规格
- 等等

#### `update_product`
更新产品信息

**必需参数：**
- `product_id`: 产品ID

**可选参数：** 任何需要更新的产品字段

#### `delete_product`
删除产品

**参数：**
- `product_id`: 产品ID

#### `upload_product_images`
为产品上传图片

**参数：**
- `product_id`: 产品ID
- `images`: 图片文件列表，每个包含：
  - `filename`: 文件名
  - `content`: Base64编码的图片内容
  - `mime_type` (可选): MIME类型

**图片上传示例：**
```
使用upload_product_images为产品ID 1上传图片，图片列表包含一个文件：
- filename: "product.jpg"
- content: "/9j/4AAQSkZJRgABAQEA..." (Base64编码)
- mime_type: "image/jpeg"
```

### 分类管理工具

#### `get_categories`
获取分类列表

**参数：**
- `active_only` (可选): 仅显示激活的分类，默认true
- `include_products` (可选): 包含产品列表，默认false

#### `get_category`
获取单个分类详情

**参数：**
- `category_id`: 分类ID

#### `create_category`
创建新分类

**必需参数：**
- `name`: 分类名称
- `display_name`: 显示名称

**可选参数：**
- `description`: 分类描述
- `slug`: URL别名
- `icon`: 图标
- `sort_order`: 排序
- `is_active`: 是否激活

#### `update_category`
更新分类信息

**必需参数：**
- `category_id`: 分类ID

**可选参数：** 任何需要更新的分类字段

#### `delete_category`
删除分类

**参数：**
- `category_id`: 分类ID

#### `toggle_category`
切换分类状态（激活/停用）

**参数：**
- `category_id`: 分类ID

#### `batch_create_categories`
批量创建分类

**参数：**
- `categories`: 分类列表，每个包含分类信息

## 使用示例

### 1. 配置API连接

```
请使用configure_api工具设置API连接：
- base_url: http://localhost:5000/api/v1
- api_key: sk-abcd1234...
```

### 2. 获取产品列表

```
使用get_products获取第一页的产品列表，每页显示10个产品，只显示可用商品
```

### 3. 创建新产品

```
使用create_product创建一个新产品：
- name: "9成新iPhone 13"
- description: "功能完好，外观良好"
- price: 800
- category: "electronics"
- condition: "9成新"
- quantity: 1
```

### 4. 上传产品图片

```
为产品ID 1上传图片，需要将图片文件转换为Base64编码
```

### 5. 创建分类

```
使用create_category创建新分类：
- name: "smartphones"
- display_name: "智能手机"
- description: "各种品牌智能手机"
- icon: "fas fa-mobile-alt"
```

### 6. 批量创建分类

```
使用batch_create_categories批量创建分类：
- 分类1: name="laptops", display_name="笔记本电脑"
- 分类2: name="tablets", display_name="平板电脑"
```

## 图片处理

### 图片上传的Base64编码

由于MCP协议的限制，图片需要通过Base64编码传输。你可以：

1. **使用在线Base64编码工具**：
   - 访问在线Base64编码网站
   - 上传图片文件
   - 复制生成的Base64字符串

2. **使用命令行工具**：
   ```bash
   # Linux/Mac
   base64 -i image.jpg
   
   # Windows (PowerShell)
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("image.jpg"))
   ```

3. **使用Python脚本**：
   ```python
   import base64
   
   with open("image.jpg", "rb") as f:
       encoded = base64.b64encode(f.read()).decode()
       print(encoded)
   ```

### 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

## 错误处理

MCP服务器会返回详细的错误信息，包括：

- API连接错误
- 认证失败
- 数据验证错误
- 服务器内部错误
- 图片处理错误

## 日志和调试

服务器运行时会输出详细的日志信息，帮助调试问题。

## 技术细节

- **协议**: Model Context Protocol (MCP)
- **HTTP客户端**: httpx (异步)
- **认证**: API Key
- **图片传输**: Base64编码
- **错误处理**: 统一错误响应格式

## 许可证

与Sara二手商店项目保持一致。

## 支持

如有问题或建议，请联系开发团队。