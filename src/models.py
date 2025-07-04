"""
Sara二手售卖网站 - 数据库模型
包含产品、订单、留言等核心数据模型
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json
import uuid
from datetime import datetime

db = SQLAlchemy()


class Category(db.Model):
    """产品分类模型 - 存储产品分类信息"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(100), nullable=False, unique=True)  # URL友好的分类标识
    icon = db.Column(db.String(50))  # 图标类名
    sort_order = db.Column(db.Integer, default=0)  # 排序权重
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联产品
    products = db.relationship('Product', backref='category_obj', lazy='dynamic')
    
    def get_product_count(self):
        """获取该分类下的产品数量"""
        return self.products.filter(Product.stock_status == Product.STATUS_AVAILABLE).count()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'slug': self.slug,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'product_count': self.get_product_count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Category {self.name}: {self.display_name}>'


class Admin(UserMixin, db.Model):
    """管理员模型 - 管理后台用户管理"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_super_admin': self.is_super_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class SiteSettings(db.Model):
    """网站设置模型 - 存储网站配置信息"""
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SiteSettings {self.key}>'


class Product(db.Model):
    """产品模型 - 存储二手商品信息"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # 新的分类关联
    category = db.Column(db.String(50), nullable=False)  # 保留旧字段以兼容现有数据
    condition = db.Column(db.String(20), nullable=False)
    stock_status = db.Column(db.String(20), default='available')
    face_to_face_only = db.Column(db.Boolean, default=False, nullable=False)  # 是否仅支持见面交易
    # 库存管理字段
    quantity = db.Column(db.Integer, default=1, nullable=False)  # 库存数量
    low_stock_threshold = db.Column(db.Integer, default=1, nullable=False)  # 低库存警告阈值
    track_inventory = db.Column(db.Boolean, default=True, nullable=False)  # 是否启用库存跟踪
    images = db.Column(db.Text)  # JSON格式存储图片URL列表
    cover_image = db.Column(db.String(500))  # 封面图片URL
    specifications = db.Column(db.Text)  # JSON格式存储商品规格
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 分类常量
    CATEGORY_ELECTRONICS = 'electronics'
    CATEGORY_CLOTHING = 'clothing'
    CATEGORY_ANIME = 'anime'
    CATEGORY_APPLIANCES = 'appliances'
    CATEGORY_OTHER = 'other'
    
    CATEGORIES = [
        (CATEGORY_ELECTRONICS, '电子产品'),
        (CATEGORY_CLOTHING, '衣物'),
        (CATEGORY_ANIME, '动漫周边'),
        (CATEGORY_APPLIANCES, '家电用品'),
        (CATEGORY_OTHER, '其他')
    ]
    
    # 库存状态常量
    STATUS_AVAILABLE = 'available'
    STATUS_SOLD = 'sold'
    STATUS_RESERVED = 'reserved'
    
    STOCK_STATUSES = [
        (STATUS_AVAILABLE, '有货'),
        (STATUS_SOLD, '已售出'),
        (STATUS_RESERVED, '已预订')
    ]
    
    # 图片相关常量
    MAX_IMAGES = 9  # 最大图片数量
    
    def get_images(self):
        """获取图片URL列表"""
        if self.images:
            try:
                return json.loads(self.images)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_images(self, image_list):
        """设置图片URL列表 - 限制最大数量"""
        if isinstance(image_list, list):
            # 限制图片数量不超过最大值
            limited_images = image_list[:self.MAX_IMAGES]
            self.images = json.dumps(limited_images)
            
            # 如果没有设置封面图片且有图片，自动设置第一张为封面
            if limited_images and not self.cover_image:
                self.cover_image = limited_images[0]
        else:
            self.images = json.dumps([])
    
    def get_specifications(self):
        """获取商品规格信息"""
        if self.specifications:
            try:
                return json.loads(self.specifications)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_specifications(self, spec_dict):
        """设置商品规格信息"""
        if isinstance(spec_dict, dict):
            self.specifications = json.dumps(spec_dict, ensure_ascii=False)
        else:
            self.specifications = json.dumps({})
    
    def get_cover_image(self):
        """获取封面图片URL"""
        if self.cover_image:
            return self.cover_image
        # 如果没有设置封面图片，返回第一张图片
        images = self.get_images()
        return images[0] if images else None
    
    def set_cover_image(self, image_url):
        """设置封面图片"""
        images = self.get_images()
        if image_url in images:
            self.cover_image = image_url
            return True
        return False
    
    def get_image_count(self):
        """获取图片数量"""
        return len(self.get_images())
    
    def can_add_more_images(self):
        """检查是否可以添加更多图片"""
        return self.get_image_count() < self.MAX_IMAGES
    
    def add_image(self, image_url):
        """添加单张图片"""
        if not self.can_add_more_images():
            return False, f"最多只能上传{self.MAX_IMAGES}张图片"
        
        images = self.get_images()
        if image_url not in images:
            images.append(image_url)
            self.set_images(images)
            return True, "图片添加成功"
        return False, "图片已存在"
    
    def remove_image(self, image_url):
        """删除指定图片"""
        images = self.get_images()
        if image_url in images:
            images.remove(image_url)
            self.set_images(images)
            
            # 如果删除的是封面图片，重新设置封面
            if self.cover_image == image_url:
                self.cover_image = images[0] if images else None
            
            return True, "图片删除成功"
        return False, "图片不存在"
    
    def get_category_display(self):
        """获取分类显示名称"""
        # 优先使用新的分类关联
        if self.category_obj:
            return self.category_obj.display_name
        # 兼容旧的分类常量
        category_dict = dict(self.CATEGORIES)
        return category_dict.get(self.category, self.category)
    
    def get_status_display(self):
        """获取库存状态显示名称"""
        status_dict = dict(self.STOCK_STATUSES)
        return status_dict.get(self.stock_status, self.stock_status)
    
    def is_available(self):
        """检查商品是否可购买"""
        if self.track_inventory:
            return self.stock_status == self.STATUS_AVAILABLE and self.quantity > 0
        else:
            return self.stock_status == self.STATUS_AVAILABLE
    
    def is_low_stock(self):
        """检查是否低库存"""
        if not self.track_inventory:
            return False
        return self.quantity <= self.low_stock_threshold
    
    def is_out_of_stock(self):
        """检查是否缺货"""
        if not self.track_inventory:
            return self.stock_status == self.STATUS_SOLD
        return self.quantity <= 0
    
    def reduce_stock(self, quantity=1):
        """减少库存"""
        if not self.track_inventory:
            # 如果不跟踪库存，直接标记为已售出
            self.stock_status = self.STATUS_SOLD
            return True
        
        if self.quantity >= quantity:
            self.quantity -= quantity
            # 如果库存为0，自动更新状态为已售出
            if self.quantity == 0:
                self.stock_status = self.STATUS_SOLD
            return True
        return False
    
    def increase_stock(self, quantity=1):
        """增加库存"""
        if not self.track_inventory:
            # 如果不跟踪库存，恢复为可用状态
            self.stock_status = self.STATUS_AVAILABLE
            return True
        
        self.quantity += quantity
        # 如果之前是已售出状态且现在有库存，恢复为可用状态
        if self.stock_status == self.STATUS_SOLD and self.quantity > 0:
            self.stock_status = self.STATUS_AVAILABLE
        return True
    
    def set_stock_quantity(self, quantity):
        """设置库存数量"""
        if not self.track_inventory:
            # 如果不跟踪库存，根据数量设置状态
            if quantity > 0:
                self.stock_status = self.STATUS_AVAILABLE
            else:
                self.stock_status = self.STATUS_SOLD
            return True
        
        self.quantity = max(0, quantity)
        # 根据库存数量自动更新状态
        if self.quantity == 0:
            self.stock_status = self.STATUS_SOLD
        elif self.stock_status == self.STATUS_SOLD and self.quantity > 0:
            self.stock_status = self.STATUS_AVAILABLE
        return True
    
    def get_inventory_status(self):
        """获取库存状态信息"""
        if not self.track_inventory:
            return {
                'tracking_enabled': False,
                'status': self.get_status_display(),
                'available': self.stock_status == self.STATUS_AVAILABLE
            }
        
        return {
            'tracking_enabled': True,
            'quantity': self.quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'status': self.get_status_display(),
            'is_low_stock': self.is_low_stock(),
            'is_out_of_stock': self.is_out_of_stock(),
            'available': self.is_available()
        }
    
    def to_dict(self):
        """转换为字典格式，用于JSON序列化"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'category': self.category,
            'category_display': self.get_category_display(),
            'condition': self.condition,
            'stock_status': self.stock_status,
            'status_display': self.get_status_display(),
            'face_to_face_only': self.face_to_face_only,
            'images': self.get_images(),
            'cover_image': self.get_cover_image(),
            'image_count': self.get_image_count(),
            'specifications': self.get_specifications(),
            'is_available': self.is_available(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Product {self.id}: {self.name}>'


def get_low_stock_products():
    """获取低库存商品列表"""
    return Product.query.filter(
        Product.track_inventory == True,
        Product.quantity <= Product.low_stock_threshold,
        Product.quantity > 0
    ).all()


def get_out_of_stock_products():
    """获取缺货商品列表"""
    return Product.query.filter(
        db.or_(
            db.and_(Product.track_inventory == True, Product.quantity <= 0),
            db.and_(Product.track_inventory == False, Product.stock_status == Product.STATUS_SOLD)
        )
    ).all()


def get_inventory_stats():
    """获取库存统计信息"""
    total_products = Product.query.count()
    available_products = Product.query.filter(Product.stock_status == Product.STATUS_AVAILABLE).count()
    low_stock_count = len(get_low_stock_products())
    out_of_stock_count = len(get_out_of_stock_products())
    
    # 计算总库存值
    total_inventory_value = db.session.query(
        db.func.sum(Product.price * Product.quantity)
    ).filter(
        Product.track_inventory == True,
        Product.quantity > 0
    ).scalar() or 0
    
    return {
        'total_products': total_products,
        'available_products': available_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_inventory_value': float(total_inventory_value)
    }


class Order(db.Model):
    """订单模型 - 存储客户订单信息"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(50))
    items = db.Column(db.Text, nullable=False)  # JSON格式存储订单商品
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_method = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='pending')
    customer_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 交付方式常量
    DELIVERY_PICKUP = 'pickup'
    DELIVERY_SHIPPING = 'shipping'
    
    DELIVERY_METHODS = [
        (DELIVERY_PICKUP, '当面交易'),
        (DELIVERY_SHIPPING, '邮寄')
    ]
    
    # 支付方式常量
    PAYMENT_ANZ_TRANSFER = 'anz_transfer'
    PAYMENT_BANK_TRANSFER = 'bank_transfer'
    PAYMENT_CASH = 'cash'
    PAYMENT_WECHAT_ALIPAY = 'wechat_alipay'
    
    PAYMENT_METHODS = [
        (PAYMENT_ANZ_TRANSFER, 'ANZ银行转账'),
        (PAYMENT_BANK_TRANSFER, '跨行转账'),
        (PAYMENT_CASH, '现金支付'),
        (PAYMENT_WECHAT_ALIPAY, '微信/支付宝')
    ]
    
    # 订单状态常量
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    ORDER_STATUSES = [
        (STATUS_PENDING, '待支付'),
        (STATUS_PAID, '已支付'),
        (STATUS_SHIPPED, '已发货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消')
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self._generate_order_number()
    
    def _generate_order_number(self):
        """生成唯一订单号"""
        import time
        timestamp = str(int(time.time()))[-8:]  # 取时间戳后8位
        random_part = str(uuid.uuid4())[:4].upper()  # 取UUID前4位并转大写
        return f"SR{timestamp}{random_part}"
    
    def get_items(self):
        """获取订单商品列表"""
        if self.items:
            try:
                return json.loads(self.items)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_items(self, items_list):
        """设置订单商品列表"""
        if isinstance(items_list, list):
            self.items = json.dumps(items_list, ensure_ascii=False)
        else:
            self.items = json.dumps([])
    
    def get_delivery_display(self):
        """获取交付方式显示名称"""
        delivery_dict = dict(self.DELIVERY_METHODS)
        return delivery_dict.get(self.delivery_method, self.delivery_method)
    
    def get_payment_display(self):
        """获取支付方式显示名称"""
        payment_dict = dict(self.PAYMENT_METHODS)
        return payment_dict.get(self.payment_method, self.payment_method)
    
    def get_status_display(self):
        """获取订单状态显示名称"""
        status_dict = dict(self.ORDER_STATUSES)
        return status_dict.get(self.status, self.status)
    
    def get_items_display(self):
        """获取订单商品详细信息用于显示"""
        items = self.get_items()
        if not items:
            return []
        
        display_items = []
        for item in items:
            display_items.append({
                'id': item.get('id'),
                'name': item.get('name', ''),
                'price': float(item.get('price', 0)),
                'quantity': int(item.get('quantity', 1)),
                'condition': item.get('condition', ''),
                'image': item.get('image', ''),
                'total': float(item.get('price', 0)) * int(item.get('quantity', 1))
            })
        
        return display_items
    
    def get_subtotal(self):
        """获取商品小计（不含邮费）"""
        items = self.get_items()
        if not items:
            return 0
        
        subtotal = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)
        return subtotal
    
    def get_shipping_fee(self):
        """获取邮费"""
        if self.delivery_method == 'shipping':
            return 15.00
        return 0.00
    
    def calculate_shipping_fee(self):
        """计算邮费（如果是邮寄）"""
        if self.delivery_method == self.DELIVERY_SHIPPING:
            # 简单的邮费计算逻辑
            total_items = len(self.get_items())
            if total_items <= 1:
                return 15.00  # 单个商品邮费
            else:
                return 15.00 + (total_items - 1) * 5.00  # 额外商品每个5元
        return 0.00
    
    def is_payment_required(self):
        """判断是否需要预付款（邮寄订单需要预付款）"""
        if self.delivery_method == 'shipping':
            return True  # 邮寄订单都需要预付款
        return self.payment_method in ['anz_transfer', 'bank_transfer', 'wechat_alipay']
    
    def can_cancel(self):
        """判断订单是否可以取消"""
        return self.status in ['pending', 'paid']
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'items': self.get_items(),
            'total_amount': float(self.total_amount),
            'delivery_method': self.delivery_method,
            'delivery_display': self.get_delivery_display(),
            'payment_method': self.payment_method,
            'payment_display': self.get_payment_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'customer_address': self.customer_address,
            'notes': self.notes,
            'shipping_fee': self.get_shipping_fee(),
            'subtotal': self.get_subtotal(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Order {self.id}: {self.customer_name}>'


class Message(db.Model):
    """留言模型 - 存储客户留言和咨询"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unread')
    reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    replied_at = db.Column(db.DateTime)
    
    # 留言状态常量
    STATUS_UNREAD = 'unread'
    STATUS_REPLIED = 'replied'
    STATUS_ARCHIVED = 'archived'
    
    MESSAGE_STATUSES = [
        (STATUS_UNREAD, '未读'),
        (STATUS_REPLIED, '已回复'),
        (STATUS_ARCHIVED, '已归档')
    ]
    
    def get_status_display(self):
        """获取状态显示名称"""
        status_dict = dict(self.MESSAGE_STATUSES)
        return status_dict.get(self.status, self.status)
    
    def mark_as_replied(self, reply_content):
        """标记为已回复"""
        self.reply = reply_content
        self.status = self.STATUS_REPLIED
        self.replied_at = datetime.utcnow()
    
    def is_replied(self):
        """检查是否已回复"""
        return self.status == self.STATUS_REPLIED and self.reply
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'message': self.message,
            'status': self.status,
            'status_display': self.get_status_display(),
            'reply': self.reply,
            'is_replied': self.is_replied(),
            'created_at': self.created_at.isoformat(),
            'replied_at': self.replied_at.isoformat() if self.replied_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.id}: {self.name}>'


# 辅助函数
def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()


def get_categories():
    """获取所有产品分类"""
    return Product.CATEGORIES


def get_product_by_id(product_id):
    """根据ID获取产品"""
    return Product.query.get(product_id)


def get_products_by_category(category=None, available_only=True):
    """根据分类获取产品列表"""
    query = Product.query
    
    if category:
        query = query.filter(Product.category == category)
    
    if available_only:
        query = query.filter(Product.stock_status == Product.STATUS_AVAILABLE)
    
    return query.order_by(Product.created_at.desc()).all()


def search_products(keyword):
    """搜索产品 - 改进的全文搜索"""
    if not keyword or not keyword.strip():
        return []
    
    # 清理和分割关键词
    keywords = [k.strip().lower() for k in keyword.split() if k.strip()]
    if not keywords:
        return []
    
    # 构建搜索查询
    query = Product.query.filter(Product.stock_status == Product.STATUS_AVAILABLE)
    
    # 为每个关键词构建搜索条件
    search_conditions = []
    for kw in keywords:
        # 搜索名称、描述、分类和规格
        condition = (
            db.func.lower(Product.name).contains(kw) |
            db.func.lower(Product.description).contains(kw) |
            db.func.lower(Product.category).contains(kw) |
            db.func.lower(Product.condition).contains(kw) |
            db.func.lower(Product.specifications).contains(kw)
        )
        search_conditions.append(condition)
    
    # 所有关键词都要匹配（AND逻辑）
    if search_conditions:
        final_condition = search_conditions[0]
        for condition in search_conditions[1:]:
            final_condition = final_condition & condition
        query = query.filter(final_condition)
    
    # 按相关性排序：优先显示名称匹配的结果
    results = query.all()
    
    # 简单的相关性排序
    def calculate_relevance(product):
        score = 0
        name_lower = product.name.lower()
        desc_lower = (product.description or '').lower()
        
        for kw in keywords:
            # 名称完全匹配加分最多
            if kw == name_lower:
                score += 100
            # 名称包含关键词
            elif kw in name_lower:
                score += 50
            # 描述包含关键词  
            elif kw in desc_lower:
                score += 20
            # 分类匹配
            elif kw in product.category.lower():
                score += 30
            # 规格匹配
            elif product.specifications and kw in product.specifications.lower():
                score += 15
        
        return score
    
    # 按相关性分数排序
    results.sort(key=calculate_relevance, reverse=True)
    
    return results


def get_order_by_number(order_number):
    """根据订单号获取订单"""
    return Order.query.filter(Order.order_number == order_number).first()


def get_orders_by_contact(contact_info):
    """根据联系方式获取订单列表"""
    return Order.query.filter(
        (Order.customer_email == contact_info) | 
        (Order.customer_phone == contact_info)
    ).order_by(Order.created_at.desc()).all()


def get_admin_by_username(username):
    """根据用户名获取管理员"""
    return Admin.query.filter(Admin.username == username).first()


def get_admin_by_email(email):
    """根据邮箱获取管理员"""
    return Admin.query.filter(Admin.email == email).first()


def create_admin(username, email, password, is_super_admin=False):
    """创建新管理员"""
    admin = Admin(
        username=username,
        email=email,
        is_super_admin=is_super_admin
    )
    admin.set_password(password)
    return admin


def get_site_setting(key, default_value=None):
    """获取网站设置"""
    setting = SiteSettings.query.filter(SiteSettings.key == key).first()
    return setting.value if setting else default_value


def set_site_setting(key, value, description=None):
    """设置网站配置"""
    setting = SiteSettings.query.filter(SiteSettings.key == key).first()
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = SiteSettings(key=key, value=value, description=description)
        db.session.add(setting)
    return setting


# 销售分析相关函数
def get_sales_stats(start_date=None, end_date=None):
    """获取销售统计数据"""
    from sqlalchemy import func, extract
    
    # 基础查询
    query = Order.query
    
    # 日期过滤
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    
    # 完成的订单
    completed_orders = query.filter(Order.status.in_(['completed', 'paid'])).all()
    
    # 计算统计数据
    total_orders = len(completed_orders)
    total_revenue = sum(float(order.total_amount) for order in completed_orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # 按状态统计
    status_stats = {}
    for status_code, status_name in Order.ORDER_STATUSES:
        count = query.filter(Order.status == status_code).count()
        status_stats[status_name] = count
    
    # 按分类统计销售额
    category_stats = {}
    for order in completed_orders:
        items = order.get_items()
        for item in items:
            # 从产品获取分类信息
            product = Product.query.get(item.get('id'))
            if product:
                category = product.get_category_display()
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'revenue': 0}
                category_stats[category]['count'] += item.get('quantity', 1)
                category_stats[category]['revenue'] += float(item.get('price', 0)) * item.get('quantity', 1)
    
    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'status_stats': status_stats,
        'category_stats': category_stats
    }


def get_monthly_sales_trend(months=12):
    """获取月度销售趋势"""
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # 按月分组的订单统计
    monthly_stats = db.session.query(
        extract('year', Order.created_at).label('year'),
        extract('month', Order.created_at).label('month'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        Order.created_at >= start_date,
        Order.status.in_(['completed', 'paid'])
    ).group_by(
        extract('year', Order.created_at),
        extract('month', Order.created_at)
    ).order_by(
        extract('year', Order.created_at),
        extract('month', Order.created_at)
    ).all()
    
    # 格式化结果
    trend_data = []
    for stat in monthly_stats:
        trend_data.append({
            'year': int(stat.year),
            'month': int(stat.month),
            'month_name': f"{int(stat.year)}年{int(stat.month)}月",
            'order_count': stat.order_count,
            'revenue': float(stat.revenue) if stat.revenue else 0
        })
    
    return trend_data


def get_popular_products(limit=10):
    """获取热门产品排行"""
    # 从订单中统计产品销量
    product_sales = {}
    
    completed_orders = Order.query.filter(Order.status.in_(['completed', 'paid'])).all()
    
    for order in completed_orders:
        items = order.get_items()
        for item in items:
            product_id = item.get('id')
            quantity = item.get('quantity', 1)
            
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'product_id': product_id,
                    'name': item.get('name', ''),
                    'total_sold': 0,
                    'total_revenue': 0
                }
            
            product_sales[product_id]['total_sold'] += quantity
            product_sales[product_id]['total_revenue'] += float(item.get('price', 0)) * quantity
    
    # 排序并返回前N个
    sorted_products = sorted(
        product_sales.values(),
        key=lambda x: x['total_sold'],
        reverse=True
    )
    
    return sorted_products[:limit]


def get_customer_stats():
    """获取客户统计数据"""
    # 按邮箱统计客户
    customer_stats = {}
    
    orders = Order.query.all()
    for order in orders:
        email = order.customer_email
        if email not in customer_stats:
            customer_stats[email] = {
                'customer_email': email,
                'customer_name': order.customer_name,
                'order_count': 0,
                'total_spent': 0,
                'first_order': order.created_at,
                'last_order': order.created_at
            }
        
        customer_stats[email]['order_count'] += 1
        if order.status in ['completed', 'paid']:
            customer_stats[email]['total_spent'] += float(order.total_amount)
        
        # 更新首次和最后订单时间
        if order.created_at < customer_stats[email]['first_order']:
            customer_stats[email]['first_order'] = order.created_at
        if order.created_at > customer_stats[email]['last_order']:
            customer_stats[email]['last_order'] = order.created_at
    
    # 客户分析
    total_customers = len(customer_stats)
    repeat_customers = len([c for c in customer_stats.values() if c['order_count'] > 1])
    avg_orders_per_customer = sum(c['order_count'] for c in customer_stats.values()) / total_customers if total_customers > 0 else 0
    
    # 按消费额排序的VIP客户
    vip_customers = sorted(
        customer_stats.values(),
        key=lambda x: x['total_spent'],
        reverse=True
    )[:10]
    
    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'repeat_rate': repeat_customers / total_customers * 100 if total_customers > 0 else 0,
        'avg_orders_per_customer': avg_orders_per_customer,
        'vip_customers': vip_customers
    }


# 分类管理相关函数
def get_all_categories(active_only=True):
    """获取所有分类"""
    query = Category.query
    if active_only:
        query = query.filter(Category.is_active == True)
    return query.order_by(Category.sort_order, Category.created_at).all()


def get_category_by_id(category_id):
    """根据ID获取分类"""
    return Category.query.get(category_id)


def get_category_by_slug(slug):
    """根据slug获取分类"""
    return Category.query.filter(Category.slug == slug).first()


def create_category(name, display_name, description=None, slug=None, icon=None, sort_order=0):
    """创建新分类"""
    if not slug:
        # 自动生成slug
        import re
        slug = re.sub(r'[^a-zA-Z0-9\-_]', '', name.lower().replace(' ', '-'))
    
    category = Category(
        name=name,
        display_name=display_name,
        description=description,
        slug=slug,
        icon=icon,
        sort_order=sort_order
    )
    return category


def init_default_categories():
    """初始化默认分类数据"""
    default_categories = [
        {
            'name': 'electronics',
            'display_name': '电子产品',
            'description': '包括电脑、手机、相机等电子设备',
            'slug': 'electronics',
            'icon': 'fas fa-laptop',
            'sort_order': 1
        },
        {
            'name': 'clothing',
            'display_name': '衣物',
            'description': '各种服装、鞋帽配饰',
            'slug': 'clothing',
            'icon': 'fas fa-tshirt',
            'sort_order': 2
        },
        {
            'name': 'anime',
            'display_name': '动漫周边',
            'description': '动漫相关商品、手办、cosplay用品',
            'slug': 'anime',
            'icon': 'fas fa-star',
            'sort_order': 3
        },
        {
            'name': 'appliances',
            'display_name': '家电用品',
            'description': '生活家电、厨房用品等',
            'slug': 'appliances',
            'icon': 'fas fa-blender',
            'sort_order': 4
        },
        {
            'name': 'other',
            'display_name': '其他',
            'description': '其他未分类商品',
            'slug': 'other',
            'icon': 'fas fa-cube',
            'sort_order': 5
        }
    ]
    
    for cat_data in default_categories:
        existing = Category.query.filter(Category.name == cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"初始化默认分类失败: {str(e)}")
        return False


class APIUsageLog(db.Model):
    """API使用日志模型 - 记录API请求和使用情况"""
    __tablename__ = 'api_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(200), nullable=False)  # API端点
    method = db.Column(db.String(10), nullable=False)  # HTTP方法
    ip_address = db.Column(db.String(45))  # 客户端IP地址 (支持IPv6)
    user_agent = db.Column(db.Text)  # 用户代理字符串
    api_key_hash = db.Column(db.String(64))  # API密钥哈希(部分显示)
    request_data = db.Column(db.Text)  # 请求数据(JSON格式)
    response_status = db.Column(db.Integer)  # 响应状态码
    response_size = db.Column(db.Integer)  # 响应大小(字节)
    processing_time = db.Column(db.Float)  # 处理时间(毫秒)
    error_message = db.Column(db.Text)  # 错误信息
    success = db.Column(db.Boolean, default=True)  # 请求是否成功
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'method': self.method,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'api_key_hash': self.api_key_hash,
            'request_data': self.request_data,
            'response_status': self.response_status,
            'response_size': self.response_size,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'success': self.success,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def log_api_request(cls, endpoint, method, ip_address, user_agent=None, 
                       api_key_hash=None, request_data=None, response_status=200, 
                       response_size=0, processing_time=0.0, error_message=None, success=True):
        """记录API请求日志"""
        log_entry = cls(
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            api_key_hash=api_key_hash,
            request_data=json.dumps(request_data) if request_data else None,
            response_status=response_status,
            response_size=response_size,
            processing_time=processing_time,
            error_message=error_message,
            success=success
        )
        
        try:
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            print(f"记录API日志失败: {str(e)}")
            return None
    
    def __repr__(self):
        return f'<APIUsageLog {self.method} {self.endpoint} - {self.created_at}>'


def get_api_usage_stats():
    """获取API使用统计数据"""
    try:
        # 最近30天的统计
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 总请求数
        total_requests = APIUsageLog.query.filter(
            APIUsageLog.created_at >= thirty_days_ago
        ).count()
        
        # 成功请求数
        successful_requests = APIUsageLog.query.filter(
            APIUsageLog.created_at >= thirty_days_ago,
            APIUsageLog.success == True
        ).count()
        
        # 失败请求数
        failed_requests = total_requests - successful_requests
        
        # 今天的请求数
        today = datetime.utcnow().date()
        today_requests = APIUsageLog.query.filter(
            db.func.date(APIUsageLog.created_at) == today
        ).count()
        
        # 平均响应时间
        avg_response_time = db.session.query(
            db.func.avg(APIUsageLog.processing_time)
        ).filter(
            APIUsageLog.created_at >= thirty_days_ago,
            APIUsageLog.success == True
        ).scalar() or 0.0
        
        # 最常用的端点
        popular_endpoints = db.session.query(
            APIUsageLog.endpoint,
            db.func.count(APIUsageLog.id).label('count')
        ).filter(
            APIUsageLog.created_at >= thirty_days_ago
        ).group_by(APIUsageLog.endpoint).order_by(
            db.func.count(APIUsageLog.id).desc()
        ).limit(5).all()
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'today_requests': today_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'avg_response_time': round(avg_response_time, 2),
            'popular_endpoints': [{'endpoint': ep, 'count': count} for ep, count in popular_endpoints]
        }
    except Exception as e:
        print(f"获取API统计数据失败: {str(e)}")
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'today_requests': 0,
            'success_rate': 0,
            'avg_response_time': 0,
            'popular_endpoints': []
        }


def get_recent_api_logs(limit=10):
    """获取最近的API使用日志"""
    try:
        logs = APIUsageLog.query.order_by(
            APIUsageLog.created_at.desc()
        ).limit(limit).all()
        return logs
    except Exception as e:
        print(f"获取API日志失败: {str(e)}")
        return []


class SiteInfoSection(db.Model):
    """站点信息部分模型 - 存储信息页面的主要部分"""
    __tablename__ = 'site_info_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # 唯一标识符，如'about', 'policies'
    name = db.Column(db.String(100), nullable=False)  # 部分名称
    description = db.Column(db.Text)  # 部分描述
    icon = db.Column(db.String(50))  # 图标类名
    sort_order = db.Column(db.Integer, default=0)  # 排序权重
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联信息项
    items = db.relationship('SiteInfoItem', backref='section', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_active_items(self):
        """获取启用的信息项"""
        return self.items.filter(SiteInfoItem.is_active == True).order_by(SiteInfoItem.sort_order).all()
    
    def to_dict(self, include_items=False, lang='zh'):
        """转换为字典格式"""
        result = {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_items:
            result['items'] = [item.to_dict(lang=lang) for item in self.get_active_items()]
        
        return result
    
    def __repr__(self):
        return f'<SiteInfoSection {self.key}: {self.name}>'


class SiteInfoItem(db.Model):
    """站点信息项模型 - 存储具体的信息项"""
    __tablename__ = 'site_info_items'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('site_info_sections.id'), nullable=False)
    key = db.Column(db.String(50), nullable=False)  # 项目标识符
    item_type = db.Column(db.String(20), nullable=False)  # 项目类型
    content = db.Column(db.Text)  # 内容（JSON格式存储复杂数据）
    sort_order = db.Column(db.Integer, default=0)  # 排序权重
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 项目类型常量
    TYPE_TEXT = 'text'  # 普通文本
    TYPE_HTML = 'html'  # HTML内容
    TYPE_LIST = 'list'  # 列表项
    TYPE_FAQ = 'faq'  # 问答
    TYPE_CONTACT = 'contact'  # 联系信息
    TYPE_FEATURE = 'feature'  # 特性/功能点
    
    ITEM_TYPES = [
        (TYPE_TEXT, '文本'),
        (TYPE_HTML, 'HTML内容'),
        (TYPE_LIST, '列表项'),
        (TYPE_FAQ, '问答'),
        (TYPE_CONTACT, '联系信息'),
        (TYPE_FEATURE, '特性功能')
    ]
    
    # 关联翻译
    translations = db.relationship('SiteInfoTranslation', backref='item', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_content(self):
        """获取内容数据"""
        if self.content:
            try:
                return json.loads(self.content)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_content(self, content_data):
        """设置内容数据"""
        if isinstance(content_data, (dict, list)):
            self.content = json.dumps(content_data, ensure_ascii=False)
        else:
            self.content = json.dumps({})
    
    def get_translation(self, lang='zh'):
        """获取指定语言的翻译"""
        translation = self.translations.filter(SiteInfoTranslation.language == lang).first()
        return translation
    
    def get_translated_content(self, lang='zh'):
        """获取翻译内容"""
        translation = self.get_translation(lang)
        if translation:
            return translation.get_content()
        return {}
    
    def get_type_display(self):
        """获取类型显示名称"""
        type_dict = dict(self.ITEM_TYPES)
        return type_dict.get(self.item_type, self.item_type)
    
    def to_dict(self, lang='zh'):
        """转换为字典格式"""
        # 获取翻译内容，如果没有则使用默认内容
        translated_content = self.get_translated_content(lang)
        default_content = self.get_content()
        
        # 合并翻译内容和默认内容
        final_content = {**default_content, **translated_content}
        
        return {
            'id': self.id,
            'section_id': self.section_id,
            'key': self.key,
            'item_type': self.item_type,
            'type_display': self.get_type_display(),
            'content': final_content,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SiteInfoItem {self.key}: {self.item_type}>'


class SiteInfoTranslation(db.Model):
    """站点信息翻译模型 - 存储多语言翻译"""
    __tablename__ = 'site_info_translations'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('site_info_items.id'), nullable=False)
    language = db.Column(db.String(5), nullable=False)  # 语言代码，如'zh', 'en'
    content = db.Column(db.Text, nullable=False)  # 翻译内容（JSON格式）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加组合唯一索引
    __table_args__ = (
        db.UniqueConstraint('item_id', 'language', name='unique_item_language'),
    )
    
    def get_content(self):
        """获取翻译内容"""
        if self.content:
            try:
                return json.loads(self.content)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_content(self, content_data):
        """设置翻译内容"""
        if isinstance(content_data, (dict, list)):
            self.content = json.dumps(content_data, ensure_ascii=False)
        else:
            self.content = json.dumps({})
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'language': self.language,
            'content': self.get_content(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SiteInfoTranslation {self.item_id}-{self.language}>'


# 站点信息相关辅助函数
def get_site_info_sections(active_only=True):
    """获取所有信息部分"""
    query = SiteInfoSection.query
    if active_only:
        query = query.filter(SiteInfoSection.is_active == True)
    return query.order_by(SiteInfoSection.sort_order).all()


def get_site_info_section_by_key(key):
    """根据key获取信息部分"""
    return SiteInfoSection.query.filter(SiteInfoSection.key == key).first()


def get_site_info_items_by_section(section_key, active_only=True, lang='zh'):
    """获取指定部分的信息项"""
    section = get_site_info_section_by_key(section_key)
    if not section:
        return []
    
    query = section.items
    if active_only:
        query = query.filter(SiteInfoItem.is_active == True)
    
    items = query.order_by(SiteInfoItem.sort_order).all()
    return [item.to_dict(lang=lang) for item in items]


def get_all_site_info_data(lang='zh'):
    """获取所有站点信息数据"""
    sections = get_site_info_sections(active_only=True)
    result = {}
    
    for section in sections:
        result[section.key] = {
            'section': section.to_dict(),
            'items': [item.to_dict(lang=lang) for item in section.get_active_items()]
        }
    
    return result


def init_default_site_info():
    """初始化默认站点信息数据"""
    try:
        # 创建主要部分
        sections_data = [
            {
                'key': 'owner_info',
                'name': '店主信息',
                'description': '店主的基本信息和介绍',
                'icon': '👋',
                'sort_order': 1
            },
            {
                'key': 'security_features',
                'name': '交易保障',
                'description': '交易安全和信任保障',
                'icon': '🛡️',
                'sort_order': 2
            },
            {
                'key': 'policies',
                'name': '售后政策',
                'description': '售后服务政策',
                'icon': '📋',
                'sort_order': 3
            },
            {
                'key': 'payment_methods',
                'name': '支付方式',
                'description': '支持的支付方式',
                'icon': '💳',
                'sort_order': 4
            },
            {
                'key': 'faq',
                'name': '常见问题',
                'description': '客户常见问题解答',
                'icon': '❓',
                'sort_order': 5
            },
            {
                'key': 'contact_info',
                'name': '联系信息',
                'description': '联系方式和服务时间',
                'icon': '📞',
                'sort_order': 6
            }
        ]
        
        # 创建部分
        for section_data in sections_data:
            existing = SiteInfoSection.query.filter(SiteInfoSection.key == section_data['key']).first()
            if not existing:
                section = SiteInfoSection(**section_data)
                db.session.add(section)
                db.session.flush()  # 确保获得ID
                
                # 根据部分类型创建相应的信息项
                if section_data['key'] == 'owner_info':
                    # 店主信息
                    items = [
                        {
                            'key': 'name',
                            'item_type': 'contact',
                            'content': json.dumps({'value': 'Sara'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'phone',
                            'item_type': 'contact',
                            'content': json.dumps({'value': '0225255862'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'email',
                            'item_type': 'contact',
                            'content': json.dumps({'value': 'sarahliu.akl@gmail.com'}, ensure_ascii=False),
                            'sort_order': 3
                        },
                        {
                            'key': 'location',
                            'item_type': 'contact',
                            'content': json.dumps({'value': 'Auckland North Shore'}, ensure_ascii=False),
                            'sort_order': 4
                        },
                        {
                            'key': 'introduction',
                            'item_type': 'text',
                            'content': json.dumps({'value': '你好，欢迎来到Sara的小店！我是Sara，目前居住在奥克兰北岸，热爱生活，喜欢分享。希望通过这个温馨的小店，让我家中品质不错的二手物品找到新主人，也让更多朋友受益。'}, ensure_ascii=False),
                            'sort_order': 5
                        }
                    ]
                elif section_data['key'] == 'security_features':
                    # 交易保障
                    items = [
                        {
                            'key': 'authentic_photos',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '真实拍摄', 'description': '所有商品均为个人使用，实物拍摄，描述真实。'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'delivery_options',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '交付方式', 'description': '支持见面交易和邮寄，奥克兰地区优先见面交易。'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'payment_flexibility',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '支付方式', 'description': '多种支付方式，安全可靠。'}, ensure_ascii=False),
                            'sort_order': 3
                        },
                        {
                            'key': 'quick_response',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '响应时间', 'description': '承诺2小时内回复所有咨询，耐心解答售后问题。'}, ensure_ascii=False),
                            'sort_order': 4
                        }
                    ]
                elif section_data['key'] == 'policies':
                    # 售后政策
                    items = [
                        {
                            'key': 'return_policy',
                            'item_type': 'text',
                            'content': json.dumps({'value': '二手商品见面确认后不支持退换货。'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'after_sales',
                            'item_type': 'text',
                            'content': json.dumps({'value': '如有任何问题或售后问题，可以联系我们，Sara会耐心解答。'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'product_guarantee',
                            'item_type': 'text',
                            'content': json.dumps({'value': '所有商品均实物拍摄，保证描述真实。'}, ensure_ascii=False),
                            'sort_order': 3
                        }
                    ]
                elif section_data['key'] == 'payment_methods':
                    # 支付方式
                    items = [
                        {
                            'key': 'anz_transfer',
                            'item_type': 'feature',
                            'content': json.dumps({'title': 'ANZ银行转账', 'icon': '🏦'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'bank_transfer',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '跨行转账', 'icon': '🔄'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'wechat_alipay',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '微信/支付宝', 'icon': '📱'}, ensure_ascii=False),
                            'sort_order': 3
                        },
                        {
                            'key': 'cash',
                            'item_type': 'feature',
                            'content': json.dumps({'title': '现金支付', 'icon': '💵'}, ensure_ascii=False),
                            'sort_order': 4
                        }
                    ]
                elif section_data['key'] == 'faq':
                    # 常见问题
                    items = [
                        {
                            'key': 'shipping_areas',
                            'item_type': 'faq',
                            'content': json.dumps({'question': '新西兰哪些城市可以邮寄？', 'answer': '支持新西兰全国邮寄，奥克兰地区优先见面交易。'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'order_status',
                            'item_type': 'faq',
                            'content': json.dumps({'question': '如何查询订单状态？', 'answer': '可以通过邮件或电话联系Sara查询订单状态。'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'after_sales_service',
                            'item_type': 'faq',
                            'content': json.dumps({'question': '售后服务如何保障？', 'answer': '如有售后问题，Sara会在2小时内回复并协助解决。'}, ensure_ascii=False),
                            'sort_order': 3
                        },
                        {
                            'key': 'shipping_cost',
                            'item_type': 'faq',
                            'content': json.dumps({'question': '邮费如何计算？', 'answer': '邮费根据商品大小和重量计算，奥克兰地区建议见面交易。'}, ensure_ascii=False),
                            'sort_order': 4
                        }
                    ]
                elif section_data['key'] == 'contact_info':
                    # 联系信息
                    items = [
                        {
                            'key': 'working_hours',
                            'item_type': 'contact',
                            'content': json.dumps({'label': '工作时间', 'value': '9:00-21:00'}, ensure_ascii=False),
                            'sort_order': 1
                        },
                        {
                            'key': 'service_area',
                            'item_type': 'contact',
                            'content': json.dumps({'label': '服务区域', 'value': '奥克兰北岸'}, ensure_ascii=False),
                            'sort_order': 2
                        },
                        {
                            'key': 'response_time',
                            'item_type': 'contact',
                            'content': json.dumps({'label': '回复时间', 'value': '24小时内回复'}, ensure_ascii=False),
                            'sort_order': 3
                        }
                    ]
                else:
                    items = []
                
                # 添加信息项
                for item_data in items:
                    item = SiteInfoItem(section_id=section.id, **item_data)
                    db.session.add(item)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"初始化站点信息失败: {str(e)}")
        return False