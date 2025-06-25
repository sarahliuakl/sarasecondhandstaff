"""
视图测试
"""
import pytest
import json
from models import db, Product, Order, Message


class TestPublicViews:
    """公开页面视图测试"""
    
    def test_index_page(self, client):
        """测试首页"""
        response = client.get('/')
        assert response.status_code == 200
        assert '欢迎来到Sara的二手售卖网站' in response.get_data(as_text=True)
    
    def test_products_page(self, client):
        """测试产品列表页"""
        response = client.get('/products')
        assert response.status_code == 200
        assert '全部商品' in response.get_data(as_text=True)
    
    def test_contact_page_get(self, client):
        """测试联系页面GET请求"""
        response = client.get('/contact')
        assert response.status_code == 200
        assert '联系我' in response.get_data(as_text=True)
    
    def test_contact_page_post(self, client):
        """测试联系页面POST请求"""
        response = client.post('/contact', data={
            'name': '测试用户',
            'contact': 'test@example.com',
            'message': '这是一条测试留言'
        })
        assert response.status_code == 302  # 重定向
        
        # 验证留言已保存
        with client.application.app_context():
            message = Message.query.filter_by(name='测试用户').first()
            assert message is not None
            assert message.message == '这是一条测试留言'
    
    def test_about_page(self, client):
        """测试关于页面"""
        response = client.get('/about')
        assert response.status_code == 200
    
    def test_help_page(self, client):
        """测试帮助页面"""
        response = client.get('/help')
        assert response.status_code == 200


class TestProductViews:
    """产品相关视图测试"""
    
    def test_product_detail_valid(self, client, sample_product):
        """测试有效产品详情页"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
            product_id = sample_product.id
        
        response = client.get(f'/product/{product_id}')
        assert response.status_code == 200
        assert '测试笔记本电脑' in response.get_data(as_text=True)
    
    def test_product_detail_invalid(self, client):
        """测试无效产品详情页"""
        response = client.get('/product/99999')
        assert response.status_code == 404
    
    def test_add_to_cart_api(self, client, sample_product):
        """测试添加到购物车API"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
            product_id = sample_product.id
        
        response = client.post('/api/cart', 
                             data=json.dumps({
                                 'product_id': product_id,
                                 'quantity': 1
                             }),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert data['success'] == True
        assert data['product']['name'] == '测试笔记本电脑'
    
    def test_search_products(self, client, sample_product):
        """测试产品搜索"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
        
        response = client.get('/products?search=笔记本')
        assert response.status_code == 200
        assert '测试笔记本电脑' in response.get_data(as_text=True)
    
    def test_search_suggestions_api(self, client, sample_product):
        """测试搜索建议API"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
        
        response = client.get('/api/search/suggestions?q=笔记本')
        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert len(data) > 0
        assert data[0]['text'] == '测试笔记本电脑'


class TestOrderViews:
    """订单相关视图测试"""
    
    def test_cart_page(self, client):
        """测试购物车页面"""
        response = client.get('/cart')
        assert response.status_code == 200
    
    def test_order_confirm_get(self, client):
        """测试订单确认页面GET请求"""
        response = client.get('/order/confirm')
        assert response.status_code == 200
    
    def test_order_confirm_post(self, client, sample_product):
        """测试订单确认页面POST请求"""
        with client.application.app_context():
            db.session.add(sample_product)
            db.session.commit()
            
            cart_data = json.dumps([{
                'id': sample_product.id,
                'name': sample_product.name,
                'price': float(sample_product.price),
                'quantity': 1
            }])
        
        response = client.post('/order/confirm', data={
            'customer_name': '测试用户',
            'customer_email': 'test@example.com',
            'customer_phone': '021234567',
            'delivery_method': 'shipping',
            'payment_method': 'anz_transfer',
            'customer_address': '123 Test Street',
            'cart_data': cart_data
        })
        
        assert response.status_code == 302  # 重定向到成功页面
        
        # 验证订单已创建
        with client.application.app_context():
            order = Order.query.filter_by(customer_email='test@example.com').first()
            assert order is not None
            assert order.customer_name == '测试用户'
    
    def test_order_query_page(self, client):
        """测试订单查询页面"""
        response = client.get('/order/query')
        assert response.status_code == 200


class TestSEOFeatures:
    """SEO功能测试"""
    
    def test_sitemap_xml(self, client):
        """测试sitemap.xml"""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert response.content_type == 'application/xml; charset=utf-8'
        assert '<?xml version="1.0" encoding="UTF-8"?>' in response.get_data(as_text=True)
    
    def test_robots_txt(self, client):
        """测试robots.txt"""
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert response.content_type == 'text/plain; charset=utf-8'
        data = response.get_data(as_text=True)
        assert 'User-agent: *' in data
        assert 'Sitemap:' in data


class TestAdminViews:
    """管理后台视图测试"""
    
    def test_admin_login_page(self, client):
        """测试管理员登录页面"""
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert '管理员登录' in response.get_data(as_text=True)
    
    def test_admin_login_valid(self, client, sample_admin):
        """测试有效管理员登录"""
        with client.application.app_context():
            db.session.add(sample_admin)
            db.session.commit()
        
        response = client.post('/admin/login', data={
            'username': 'testadmin',
            'password': 'testpassword'
        })
        assert response.status_code == 302  # 重定向到仪表板
    
    def test_admin_login_invalid(self, client):
        """测试无效管理员登录"""
        response = client.post('/admin/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 200  # 返回登录页面
    
    def test_admin_dashboard_requires_auth(self, client):
        """测试仪表板需要认证"""
        response = client.get('/admin/dashboard')
        assert response.status_code == 302  # 重定向到登录
    
    def test_admin_dashboard_authenticated(self, client, auth_admin):
        """测试已认证的仪表板访问"""
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert '管理后台' in response.get_data(as_text=True)
    
    def test_admin_products_page(self, client, auth_admin):
        """测试管理产品页面"""
        response = client.get('/admin/products')
        assert response.status_code == 200
        assert '产品管理' in response.get_data(as_text=True)
    
    def test_admin_orders_page(self, client, auth_admin):
        """测试管理订单页面"""
        response = client.get('/admin/orders')
        assert response.status_code == 200
        assert '订单管理' in response.get_data(as_text=True)
    
    def test_admin_analytics_page(self, client, auth_admin):
        """测试销售分析页面"""
        response = client.get('/admin/analytics')
        assert response.status_code == 200
        assert '销售分析' in response.get_data(as_text=True)