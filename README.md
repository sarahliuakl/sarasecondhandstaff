# Sarah's Garage Sale 的源代码

[项目GitHub仓库（sarasecondhandstaff）](https://github.com/sarahliuakl/sarasecondhandstaff)

> 新西兰奥克兰个人二手物品售卖平台 Sarah's Garage Sale

## 项目简介

这是一个专为新西兰地区打造的个人二手物品售卖网站，帮助Sarah将家中的优质二手物品出售给有需要的人。网站支持面交和邮寄两种交付方式，提供多种安全的支付选择。

## 主要功能

### 🛍️ 商品展示与管理
- **产品分类**：电子产品、服装、动漫周边、家电用品等多种分类
- **详细信息**：支持图片上传、多角度展示、成色描述、规格参数
- **智能搜索**：多关键词搜索、搜索建议、搜索历史、相关性排序
- **库存管理**：精确库存跟踪、低库存警告、自动状态更新
- **仅见面交易**：贵重物品（如电脑、手机）支持仅见面交易模式

### 🛒 完整购物流程
- **智能购物车**：本地存储、数量管理、实时价格计算
- **订单确认**：完整的订单信息确认页面
- **支付集成**：多种支付方式、动态邮费计算
- **订单成功**：订单详情展示、打印功能
- **交付方式**：当面交易（奥克兰地区）、邮寄（全新西兰）

### 📞 客户服务与沟通
- **在线留言**：客户咨询、问题反馈、管理员回复系统
- **订单查询**：通过邮箱或电话查询订单状态和详情
- **邮件通知**：自动发送订单确认邮件给客户和管理员
- **实时响应**：承诺2小时内回复客户咨询

### 🔧 管理后台系统
- **管理员认证**：安全的登录系统、密码修改
- **产品管理**：完整的CRUD操作、图片上传、库存管理
- **订单管理**：状态更新、邮件通知、订单统计
- **客户服务**：留言管理、回复系统、归档功能
- **销售分析**：销售统计、趋势图表、热门产品分析
- **网站设置**：网站信息配置、联系方式管理

### 🔒 安全与性能
- **CSRF保护**：全站CSRF令牌保护
- **输入验证**：严格的数据验证和清理
- **日志系统**：完整的操作日志记录
- **数据库优化**：支持SQLite和PostgreSQL、连接池优化
- **SEO优化**：完整的meta标签、sitemap、结构化数据

## 技术架构

### 后端技术栈
- **Web框架**：Flask 2.3.3 + Blueprint模块化架构
- **数据库**：SQLite (开发) / PostgreSQL (生产) + SQLAlchemy ORM
- **安全认证**：Flask-Login + Flask-WTF CSRF保护
- **邮件服务**：Resend API邮件发送服务
- **文件上传**：支持图片上传、压缩、缩略图生成
- **日志系统**：完整的日志记录和轮转
- **配置管理**：环境变量 + 多环境配置支持

### 前端技术栈
- **CSS框架**：Tailwind CSS 响应式设计
- **JavaScript**：原生ES6+、AJAX交互
- **图表库**：Chart.js 数据可视化
- **用户体验**：实时搜索建议、本地存储购物车
- **移动端**：完全响应式设计、触屏优化

### 数据库架构
- **产品表 (products)**：商品信息、库存管理、图片存储
- **订单表 (orders)**：完整订单流程、状态跟踪
- **留言表 (messages)**：客户服务、回复管理
- **管理员表 (admins)**：后台用户管理
- **网站设置表 (site_settings)**：系统配置管理
- **邮件队列表 (email_queue)**：异步邮件发送

### 开发与测试
- **单元测试**：pytest测试框架、覆盖模型和视图
- **代码规范**：PEP 8 Python代码规范
- **版本控制**：Git + GitHub仓库管理
- **环境隔离**：Python虚拟环境 + 依赖管理

## 项目结构

```
sarasecondhandstaff/
├── 核心应用文件
│   ├── app.py                 # Flask主应用入口
│   ├── models.py              # SQLAlchemy数据库模型
│   ├── admin_routes.py        # 管理后台路由模块
│   ├── config.py              # 多环境配置管理
│   ├── utils.py               # 工具函数库
│   ├── file_upload.py         # 图片上传处理
│   └── email_service.py       # 邮件发送服务
│
├── 数据库相关
│   ├── init_db.py            # 数据库初始化脚本
│   ├── migrate_db.py         # SQLite到PostgreSQL迁移
│   ├── switch_db.py          # 数据库切换工具
│   ├── db_monitor.py         # 连接池监控工具
│   └── sara_shop.db          # SQLite数据库文件
│
├── 模板文件
│   ├── templates/
│   │   ├── base.html         # 基础布局模板
│   │   ├── index.html        # 首页
│   │   ├── products.html     # 产品列表页
│   │   ├── product_detail.html # 产品详情页
│   │   ├── cart.html         # 购物车页面
│   │   ├── order_confirm.html # 订单确认页
│   │   ├── order_success.html # 订单成功页
│   │   ├── order_query.html  # 订单查询页
│   │   ├── contact.html      # 联系页面
│   │   ├── about.html        # 关于页面
│   │   ├── help.html         # 帮助页面
│   │   └── admin/           # 管理后台模板
│   │       ├── dashboard.html    # 管理首页
│   │       ├── products.html     # 产品管理
│   │       ├── orders.html       # 订单管理
│   │       ├── messages.html     # 留言管理
│   │       ├── analytics.html    # 销售分析
│   │       └── profile.html      # 个人设置
│
├── 静态资源
│   └── static/
│       ├── uploads/          # 用户上传图片
│       ├── sitemap.xml       # SEO网站地图
│       └── robots.txt        # 搜索引擎规则
│
├── 测试文件
│   ├── tests/
│   │   ├── conftest.py       # pytest配置
│   │   ├── test_models.py    # 模型测试
│   │   ├── test_views.py     # 视图测试
│   │   └── test_utils.py     # 工具函数测试
│   ├── pytest.ini           # pytest配置文件
│   └── run_tests.py          # 测试运行脚本
│
├── 日志文件
│   └── logs/
│       ├── sara_shop.log     # 应用日志
│       └── sara_shop_dev.log # 开发日志
│
├── 环境与配置
│   ├── venv/                 # Python虚拟环境
│   ├── requirements.txt      # Python依赖包
│   ├── .env.example          # 环境变量示例
│   └── .gitignore           # Git忽略文件
│
└── 项目文档
    ├── README.md            # 项目说明文档
    ├── todolist.md          # 任务管理列表
    ├── 数据库设计.md          # 数据库设计文档
    ├── 网站改版计划.md        # 项目规划文档
    └── 部署说明.md           # 部署指南文档
```

## 快速开始

### 1. 环境要求
- Python 3.8+
- pip包管理器

### 2. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 3. 环境配置
```bash
# 复制环境变量配置文件
cp .env.example .env

# 编辑配置文件，设置必要的API密钥
# 至少需要设置 SECRET_KEY 和 RESEND_API_KEY
vim .env
```

### 4. 初始化数据库
```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库并导入示例数据
python init_db.py

# 创建管理员账户（可选）
python -c "from models import Admin, db; from app import app; app.app_context().push(); admin = Admin(username='admin', email='admin@example.com'); admin.set_password('admin123'); db.session.add(admin); db.session.commit(); print('管理员创建成功')"
```

### 5. 启动应用
```bash
# 启动Flask开发服务器
python app.py

# 或使用调试模式
FLASK_ENV=development python app.py
```

访问 http://127.0.0.1:5000 查看网站

## 示例数据

数据库初始化后将包含：
- **示例产品**：涵盖电子产品、服装等分类，支持图片上传
- **示例订单**：展示完整的订单流程和状态管理
- **示例留言**：客户咨询和管理员回复功能演示
- **管理员账户**：用于访问后台管理系统

## 主要页面

### 首页 (/)
- 网站介绍和特色
- 最新上架商品展示
- 奥克兰天气信息

### 产品列表 (/products)
- 所有商品展示
- 分类筛选功能
- 搜索功能
- 分页浏览

### 产品详情 (/product/<id>)
- 商品详细信息
- 多图展示
- 规格参数
- 购买选项

### 联系我 (/contact)
- 联系方式展示
- 在线留言表单
- 快速咨询通道

### 关于我 (/about)
- 个人介绍
- 交易保障说明
- 信任建立

## API接口文档

### 前端API
- `POST /api/cart` - 添加商品到购物车（CSRF豁免）
- `GET /api/search/suggestions` - 获取搜索建议
- `GET /sitemap.xml` - SEO网站地图
- `GET /robots.txt` - 搜索引擎爬虫规则

### 管理后台API
- `POST /admin/product/<id>/delete` - 删除产品
- `POST /admin/order/<id>/update-status` - 更新订单状态
- `POST /admin/message/<id>/reply` - 回复客户留言
- `POST /admin/product/<id>/inventory` - 更新产品库存
- `GET /admin/analytics/api/stats` - 获取销售统计数据
- `GET /admin/analytics/api/trends` - 获取销售趋势数据

### 订单系统
- `GET /order/query` - 订单查询页面
- `POST /order/search` - 订单搜索处理
- `POST /order/confirm` - 订单确认提交
- `GET /order/success/<order_number>` - 订单成功页面

## 部署说明

### 开发环境
已在WSL2 Ubuntu环境下测试通过

### 数据库部署
```bash
# 切换到PostgreSQL（生产环境推荐）
python switch_db.py postgres

# 从SQLite迁移数据到PostgreSQL
python migrate_db.py

# 监控数据库连接池状态
python db_monitor.py status
```

### 生产环境建议
- **Web服务器**：Gunicorn + Nginx 反向代理
- **HTTPS配置**：Let's Encrypt SSL证书
- **数据库**：PostgreSQL + 连接池优化
- **邮件服务**：Resend API（已集成）
- **文件存储**：本地存储或云存储
- **日志管理**：日志轮转和监控系统
- **备份策略**：定期数据库备份和验证

## 商品信息

根据项目需求，网站包含以下类型的二手物品：
- **电子产品**：笔记本电脑、3D打印机、显卡、手机壳等
- **衣物**：保暖大衣、夏日长裙等
- **动漫周边**：角色扮演服装、假发、小勋章等

所有商品均为真实物品信息，包含详细的成色描述和规格参数。


## 交付和支付

### 交付方式
1. **当面交易**：奥克兰地区推荐，安全地点见面
2. **邮寄**：新西兰全国，邮费约15纽币

### 支付方式
1. **ANZ银行转账**：即时到账，当日发货
2. **跨行转账**：需提前1-2天，确认到账后发货
3. **当面支付**：现金、微信、支付宝

## 开发团队

- **系统设计与开发**：Claude Code Assistant
- **项目规划**：基于用户需求文档
- **开发时间**：2025年6月24日

## 版本历史

### v1.0 (2025-06-24) - 核心功能
- ✅ 完整的产品展示和搜索功能
- ✅ 用户留言和咨询系统
- ✅ 响应式设计和移动端适配
- ✅ 购物车基础功能
- ✅ 数据库驱动的动态内容

### v1.5 (2025-06-25) - 功能完善
- ✅ 完整的购物车和订单流程
- ✅ 管理后台系统
- ✅ 邮件通知功能
- ✅ 库存管理系统
- ✅ 图片上传功能

### v2.0 (2025-06-25) - 企业级特性
- ✅ CSRF安全保护
- ✅ 多数据库支持（SQLite/PostgreSQL）
- ✅ SEO优化和网站地图
- ✅ 销售分析和数据可视化
- ✅ 单元测试框架
- ✅ 日志系统和性能监控

### 当前状态
- ✅ **生产就绪**：功能完整，安全可靠
- ✅ **技术栈现代化**：Flask + SQLAlchemy + PostgreSQL
- ✅ **用户体验优化**：响应式设计，智能搜索
- ✅ **管理后台完整**：产品、订单、客户服务一体化
- ✅ **企业级安全**：CSRF保护，输入验证，日志审计

## 许可证

本项目为个人商用项目，版权归Sara所有。

---

**开发环境地址**：http://127.0.0.1:5000  
**管理后台地址**：http://127.0.0.1:5000/admin  
**最后更新**：2025-06-25  
**开发状态**：✅ 生产就绪，功能完整

**核心数据统计**：
- 📦 **21个Python模块**：完整的MVC架构
- 🎨 **25个HTML模板**：响应式用户界面
- 🧪 **完整测试覆盖**：pytest单元测试框架
- 📊 **数据分析功能**：Chart.js可视化图表
- 🔐 **企业级安全**：CSRF保护，日志审计
- 📧 **邮件系统**：Resend API自动通知
- 🗄️ **双数据库支持**：SQLite开发，PostgreSQL生产