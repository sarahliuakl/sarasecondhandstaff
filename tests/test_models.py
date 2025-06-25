"""
模型测试
"""
import pytest
from models import db, Product, Order, Message, Admin
from models import get_sales_stats, get_popular_products, get_customer_stats


class TestProduct:
    """产品模型测试"""
    
    def test_create_product(self, client, sample_product):
        """测试创建产品"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
            
            assert sample_product.id is not None
            assert sample_product.name == '测试笔记本电脑'
            assert sample_product.price == 800.00
            assert sample_product.is_available() == True
    
    def test_product_images(self, client, sample_product):
        """测试产品图片功能"""
        with client.application.app_context():
            images = ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
            sample_product.set_images(images)
            
            assert sample_product.get_images() == images
    
    def test_product_specifications(self, client, sample_product):
        """测试产品规格功能"""
        with client.application.app_context():
            specs = {'brand': 'TestBrand', 'model': 'TestModel'}
            sample_product.set_specifications(specs)
            
            assert sample_product.get_specifications() == specs
    
    def test_product_availability(self, client, sample_product):
        """测试产品可用性"""
        with client.application.app_context():
            # 测试有库存时
            assert sample_product.is_available() == True
            
            # 测试缺货时
            sample_product.stock_status = 'sold'
            assert sample_product.is_available() == False
    
    def test_stock_management(self, client, sample_product):
        """测试库存管理"""
        with client.application.app_context():
            # 初始库存
            assert sample_product.quantity == 1
            
            # 减少库存
            sample_product.reduce_stock(1)
            assert sample_product.quantity == 0
            assert sample_product.stock_status == 'sold'
            
            # 增加库存
            sample_product.increase_stock(2)
            assert sample_product.quantity == 2
            assert sample_product.stock_status == 'available'


class TestOrder:
    """订单模型测试"""
    
    def test_create_order(self, client, sample_order):
        """测试创建订单"""
        with client.application.app_context():
            db.session.add(sample_order)
            db.session.commit()
            
            assert sample_order.id is not None
            assert sample_order.order_number.startswith('SR')
            assert sample_order.customer_name == '测试用户'
            assert sample_order.total_amount == 815.00
    
    def test_order_items(self, client, sample_order):
        """测试订单商品"""
        with client.application.app_context():
            items = sample_order.get_items()
            assert len(items) == 1
            assert items[0]['name'] == '测试笔记本电脑'
            assert items[0]['price'] == 800.00
    
    def test_order_subtotal(self, client, sample_order):
        """测试订单小计"""
        with client.application.app_context():
            subtotal = sample_order.get_subtotal()
            assert subtotal == 800.00
    
    def test_shipping_fee(self, client, sample_order):
        """测试邮费计算"""
        with client.application.app_context():
            # 邮寄订单
            assert sample_order.get_shipping_fee() == 15.00
            
            # 当面交易订单
            sample_order.delivery_method = 'pickup'
            assert sample_order.get_shipping_fee() == 0.00
    
    def test_order_status_display(self, client, sample_order):
        """测试订单状态显示"""
        with client.application.app_context():
            assert sample_order.get_status_display() == '待支付'
            
            sample_order.status = 'completed'
            assert sample_order.get_status_display() == '已完成'


class TestMessage:
    """留言模型测试"""
    
    def test_create_message(self, client):
        """测试创建留言"""
        with client.application.app_context():
            message = Message(
                name='测试用户',
                contact='test@example.com',
                message='这是一条测试留言'
            )
            db.session.add(message)
            db.session.commit()
            
            assert message.id is not None
            assert message.name == '测试用户'
            assert message.status == 'unread'
            assert message.is_replied() == False
    
    def test_reply_message(self, client):
        """测试回复留言"""
        with client.application.app_context():
            message = Message(
                name='测试用户',
                contact='test@example.com',
                message='这是一条测试留言'
            )
            
            message.mark_as_replied('这是回复内容')
            assert message.status == 'replied'
            assert message.reply == '这是回复内容'
            assert message.is_replied() == True


class TestAdmin:
    """管理员模型测试"""
    
    def test_create_admin(self, client, sample_admin):
        """测试创建管理员"""
        with client.application.app_context():
            db.session.add(sample_admin)
            db.session.commit()
            
            assert sample_admin.id is not None
            assert sample_admin.username == 'testadmin'
            assert sample_admin.is_active == True
    
    def test_password_hash(self, client, sample_admin):
        """测试密码哈希"""
        with client.application.app_context():
            # 验证正确密码
            assert sample_admin.check_password('testpassword') == True
            
            # 验证错误密码
            assert sample_admin.check_password('wrongpassword') == False
    
    def test_update_last_login(self, client, sample_admin):
        """测试更新最后登录时间"""
        with client.application.app_context():
            original_time = sample_admin.last_login
            sample_admin.update_last_login()
            
            assert sample_admin.last_login != original_time


class TestAnalytics:
    """销售分析功能测试"""
    
    def test_empty_sales_stats(self, client):
        """测试空数据时的销售统计"""
        with client.application.app_context():
            stats = get_sales_stats()
            
            assert stats['total_orders'] == 0
            assert stats['total_revenue'] == 0
            assert stats['avg_order_value'] == 0
    
    def test_sales_stats_with_data(self, client, sample_product, sample_order):
        """测试有数据时的销售统计"""
        with client.application.app_context():
            # 添加测试数据
            db.session.add(sample_product)
            sample_order.status = 'completed'  # 设为已完成状态
            db.session.add(sample_order)
            db.session.commit()
            
            stats = get_sales_stats()
            
            assert stats['total_orders'] == 1
            assert stats['total_revenue'] == 815.00
            assert stats['avg_order_value'] == 815.00
    
    def test_popular_products_empty(self, client):
        """测试空数据时的热门产品"""
        with client.application.app_context():
            products = get_popular_products(5)
            assert len(products) == 0
    
    def test_customer_stats_empty(self, client):
        """测试空数据时的客户统计"""
        with client.application.app_context():
            stats = get_customer_stats()
            
            assert stats['total_customers'] == 0
            assert stats['repeat_customers'] == 0
            assert stats['repeat_rate'] == 0
    
    def test_customer_stats_with_data(self, client, sample_order):
        """测试有数据时的客户统计"""
        with client.application.app_context():
            db.session.add(sample_order)
            db.session.commit()
            
            stats = get_customer_stats()
            
            assert stats['total_customers'] == 1
            assert stats['repeat_customers'] == 0  # 只有一个订单，不算回购
            assert stats['avg_orders_per_customer'] == 1.0