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
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    stock_status = db.Column(db.String(20), default='available')
    face_to_face_only = db.Column(db.Boolean, default=False, nullable=False)  # 是否仅支持见面交易
    images = db.Column(db.Text)  # JSON格式存储图片URL列表
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
    
    def get_images(self):
        """获取图片URL列表"""
        if self.images:
            try:
                return json.loads(self.images)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_images(self, image_list):
        """设置图片URL列表"""
        if isinstance(image_list, list):
            self.images = json.dumps(image_list)
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
    
    def get_category_display(self):
        """获取分类显示名称"""
        category_dict = dict(self.CATEGORIES)
        return category_dict.get(self.category, self.category)
    
    def get_status_display(self):
        """获取库存状态显示名称"""
        status_dict = dict(self.STOCK_STATUSES)
        return status_dict.get(self.stock_status, self.stock_status)
    
    def is_available(self):
        """检查商品是否可购买"""
        return self.stock_status == self.STATUS_AVAILABLE
    
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
            'specifications': self.get_specifications(),
            'is_available': self.is_available(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Product {self.id}: {self.name}>'


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
    """搜索产品"""
    return Product.query.filter(
        Product.name.contains(keyword) | 
        Product.description.contains(keyword)
    ).filter(
        Product.stock_status == Product.STATUS_AVAILABLE
    ).order_by(Product.created_at.desc()).all()


def get_order_by_number(order_number):
    """根据订单号获取订单"""
    return Order.query.filter(Order.order_number == order_number).first()


def get_orders_by_contact(contact_info):
    """根据联系方式获取订单列表"""
    return Order.query.filter(
        (Order.customer_email == contact_info) | 
        (Order.customer_contact == contact_info)
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