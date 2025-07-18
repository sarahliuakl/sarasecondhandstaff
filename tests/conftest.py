"""
测试配置文件
"""
import pytest
import tempfile
import os
from src import create_app
from src.models import db, Product, Order, Message, Admin

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app('testing')

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_product():
    """创建示例产品"""
    product = Product(
        name='测试笔记本电脑',
        description='高性能测试用笔记本电脑',
        price=800.00,
        category='electronics',
        condition='9成新',
        stock_status='available'
    )
    product.set_images(['https://example.com/image1.jpg'])
    product.set_specifications({
        'brand': 'TestBrand',
        'model': 'TestModel',
        'ram': '8GB'
    })
    return product


@pytest.fixture
def sample_order():
    """创建示例订单"""
    order = Order(
        customer_name='测试用户',
        customer_email='test@example.com',
        customer_phone='021234567',
        total_amount=815.00,
        delivery_method='shipping',
        payment_method='anz_transfer',
        customer_address='123 Test Street, Auckland',
        notes='测试订单'
    )
    order.set_items([{
        'id': 1,
        'name': '测试笔记本电脑',
        'price': 800.00,
        'quantity': 1,
        'condition': '9成新'
    }])
    return order


@pytest.fixture
def sample_admin():
    """创建示例管理员"""
    admin = Admin(
        username='testadmin',
        email='admin@test.com',
        is_active=True,
        is_super_admin=False
    )
    admin.set_password('testpassword')
    return admin


@pytest.fixture
def auth_admin(client, sample_admin):
    """认证的管理员用户"""
    with client.application.app_context():
        db.session.add(sample_admin)
        db.session.commit()
    
    # 登录管理员
    client.post('/admin/login', data={
        'username': 'testadmin',
        'password': 'testpassword'
    })
    
    return sample_admin