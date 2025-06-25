from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from models import db, Product, Order, Message, Admin, get_products_by_category, get_product_by_id
from utils import sanitize_user_input, validate_form_data, validate_email_address
from email_service import email_service
from email_queue import email_queue
from admin_routes import admin_bp
from config import config
import requests
import datetime
import os
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# 根据环境变量选择配置
config_name = os.getenv('FLASK_ENV', 'development')
config_obj = config[config_name]()
app.config.from_object(config_obj)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化CSRF保护
csrf = CSRFProtect(app)

# 豁免API端点的CSRF检查 - 将在路由装饰器中使用@csrf.exempt

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message = '请先登录以访问管理后台'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return Admin.query.get(int(user_id))

# 配置日志
def setup_logging(app):
    """配置应用日志"""
    if not app.debug and not app.testing:
        # 生产环境日志配置
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # 设置日志文件轮转
        file_handler = RotatingFileHandler(
            'logs/sara_shop.log', 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sara Shop 启动')
    else:
        # 开发环境日志配置
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler(
            'logs/sara_shop_dev.log',
            maxBytes=1024000,  # 1MB
            backupCount=3
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.DEBUG)

# 设置日志
setup_logging(app)

# 初始化数据库
db.init_app(app)

# 设置邮件队列的应用实例
email_queue.app = app

# 注册管理后台蓝图
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    # 获取奥克兰天气
    api_key = os.getenv('OPENWEATHER_API_KEY')
    weather = None
    if api_key:
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": "Auckland,NZ",
                    "appid": api_key,
                    "units": "metric",
                    "lang": "zh_cn"
                },
                timeout=3
            )
            if resp.status_code == 200:
                data = resp.json()
                weather = {
                    "desc": data["weather"][0]["description"],
                    "temp": round(data["main"]["temp"]),
                    "icon": data["weather"][0]["icon"]
                }
        except Exception:
            weather = None

    # 当前本地时间
    local_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=12))).strftime("%Y-%m-%d %H:%M:%S")

    # 从数据库获取最新上架的产品（首页显示前9个）
    products = get_products_by_category(available_only=True)[:9]
    
    # 转换为模板需要的格式
    product_list = []
    for product in products:
        images = product.get_images()
        product_list.append({
            "id": product.id,
            "img": images[0] if images else "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80",
            "title": product.name,
            "desc": product.description[:50] + "..." if len(product.description) > 50 else product.description,
            "price": f"NZD ${product.price}",
            "condition": product.condition,
            "category_display": product.get_category_display()
        })
    
    products = product_list
    return render_template("index.html", products=products, weather=weather, local_time=local_time)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # 获取并清理用户输入
        form_data = {
            'name': request.form.get('name', ''),
            'contact': request.form.get('contact', ''),
            'message': request.form.get('message', '')
        }
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
        # 验证表单数据
        is_valid, errors = validate_form_data(clean_data, ['name', 'contact', 'message'])
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template("contact.html")
        
        # 保存留言到数据库
        message = Message(
            name=clean_data['name'],
            contact=clean_data['contact'],
            message=clean_data['message']
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            app.logger.info(f'新留言提交: {clean_data["name"]} - {clean_data["contact"]}')
            flash('留言已提交！我会在2小时内回复您。', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'留言提交失败: {str(e)}')
            flash('提交失败，请稍后重试', 'error')
            return render_template("contact.html")
    
    return render_template("contact.html")

@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/products")
def products():
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    
    # 获取所有分类用于筛选
    categories = Product.CATEGORIES
    
    # 根据筛选条件获取产品
    if search:
        from models import search_products
        product_list = search_products(search)
    else:
        product_list = get_products_by_category(category, available_only=True)
    
    return render_template("products.html", 
                         products=product_list, 
                         categories=categories,
                         current_category=category,
                         search_term=search)

# 新增路由

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """产品详情页"""
    product = get_product_by_id(product_id)
    if not product or not product.is_available():
        flash('商品不存在或已售出', 'error')
        return redirect(url_for('products'))
    
    return render_template("product_detail.html", product=product)


@app.route("/cart")
def cart():
    """购物车页面"""
    return render_template("cart.html")


@app.route("/api/cart", methods=['POST'])
@csrf.exempt
def add_to_cart():
    """添加商品到购物车（API接口）"""
    # 对于JSON API，暂时跳过CSRF检查
    # 在生产环境中应该使用其他方式验证，如JWT token
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = get_product_by_id(product_id)
    if not product or not product.is_available():
        return jsonify({'success': False, 'message': '商品不存在或已售出'})
    
    # 这里返回商品信息，前端用localStorage管理购物车
    return jsonify({
        'success': True, 
        'product': {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.get_images()[0] if product.get_images() else '',
            'condition': product.condition,
            'face_to_face_only': product.face_to_face_only
        },
        'quantity': quantity
    })


@app.route("/order/query")
def order_query():
    """订单查询页面"""
    return render_template("order_query.html")


@app.route("/api/search/suggestions")
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # 获取产品名称和分类的建议
    suggestions = []
    
    # 搜索产品名称
    products = Product.query.filter(
        db.func.lower(Product.name).contains(query.lower())
    ).filter(
        Product.stock_status == Product.STATUS_AVAILABLE
    ).limit(5).all()
    
    for product in products:
        suggestions.append({
            'text': product.name,
            'type': 'product',
            'category': product.category
        })
    
    # 添加分类建议
    categories = Product.CATEGORIES
    for category_code, category_name in categories:
        if query.lower() in category_name.lower() or query.lower() in category_code.lower():
            suggestions.append({
                'text': category_name,
                'type': 'category'
            })
    
    return jsonify(suggestions[:8])  # 限制最多8个建议


@app.route("/sitemap.xml")
def sitemap():
    """生成XML格式的网站地图"""
    try:
        # 获取所有可用产品
        products = get_products_by_category(available_only=True)
        
        # 构建sitemap XML
        sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
'''
        
        # 添加主要页面
        base_url = request.url_root.rstrip('/')
        main_pages = [
            ('', '1.0', 'daily'),  # 首页
            ('/products', '0.9', 'daily'),  # 产品列表
            ('/contact', '0.8', 'monthly'),  # 联系页面
            ('/about', '0.7', 'monthly'),  # 关于页面
            ('/help', '0.6', 'monthly'),  # 帮助页面
        ]
        
        for page, priority, changefreq in main_pages:
            sitemap_xml += f'''  <url>
    <loc>{base_url}{page}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
'''
        
        # 添加分类页面
        categories = Product.CATEGORIES
        for category_code, category_name in categories:
            sitemap_xml += f'''  <url>
    <loc>{base_url}/products?category={category_code}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
'''
        
        # 添加产品详情页
        for product in products:
            sitemap_xml += f'''  <url>
    <loc>{base_url}/product/{product.id}</loc>
    <lastmod>{product.updated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
'''
        
        sitemap_xml += '</urlset>'
        
        return Response(sitemap_xml, mimetype='application/xml')
        
    except Exception as e:
        app.logger.error(f'生成sitemap失败: {str(e)}')
        return Response('', status=500)


@app.route("/robots.txt")
def robots_txt():
    """生成robots.txt文件"""
    robots_content = f"""User-agent: *
Allow: /
Allow: /products
Allow: /product/*
Allow: /contact
Allow: /about
Allow: /help

Disallow: /admin/*
Disallow: /api/*
Disallow: /order/*
Disallow: /cart

Sitemap: {request.url_root}sitemap.xml
"""
    return Response(robots_content, mimetype='text/plain')


@app.route("/order/search", methods=['POST'])
def order_search():
    """订单查询处理"""
    form_data = {'contact': request.form.get('contact', '')}
    clean_data = sanitize_user_input(form_data)
    
    is_valid, errors = validate_form_data(clean_data, ['contact'])
    
    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('order_query'))
    
    from models import get_orders_by_contact
    orders = get_orders_by_contact(clean_data['contact'])
    
    app.logger.info(f'订单查询: {clean_data["contact"]} - 找到{len(orders)}个订单')
    
    return render_template("order_results.html", orders=orders, contact_info=clean_data['contact'])


@app.route("/order/confirm", methods=['GET', 'POST'])
def order_confirm():
    """订单确认页面"""
    if request.method == 'POST':
        # 获取并清理用户输入
        form_data = {
            'customer_name': request.form.get('customer_name', ''),
            'customer_email': request.form.get('customer_email', ''),
            'customer_phone': request.form.get('customer_phone', ''),
            'delivery_method': request.form.get('delivery_method', ''),
            'payment_method': request.form.get('payment_method', ''),
            'customer_address': request.form.get('customer_address', ''),
            'notes': request.form.get('notes', '')
        }
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
        # 验证必填字段
        required_fields = ['customer_name', 'customer_email', 'delivery_method', 'payment_method']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template("order_confirm.html")
        
        # 验证邮箱格式
        is_email_valid, normalized_email = validate_email_address(clean_data['customer_email'])
        if not is_email_valid:
            flash('请输入有效的邮箱地址', 'error')
            return render_template("order_confirm.html")
        
        # 如果选择邮寄，地址是必填的
        if clean_data['delivery_method'] == 'shipping' and not clean_data['customer_address']:
            flash('选择邮寄时必须填写详细地址', 'error')
            return render_template("order_confirm.html")
        
        # 获取购物车内容（从前端传来的JSON数据）
        cart_data = request.form.get('cart_data', '')
        if not cart_data:
            flash('购物车数据异常，请重试', 'error')
            return redirect(url_for('cart'))
        
        try:
            import json
            cart_items = json.loads(cart_data)
            if not cart_items:
                flash('购物车是空的', 'error')
                return redirect(url_for('cart'))
            
            # 检查是否有仅见面交易商品
            has_face_to_face_only = any(item.get('face_to_face_only', False) for item in cart_items)
            
            # 如果有仅见面交易商品但选择了邮寄，返回错误
            if has_face_to_face_only and clean_data['delivery_method'] == 'shipping':
                flash('购物车中包含仅见面交易商品，不能选择邮寄方式', 'error')
                return render_template("order_confirm.html")
            
            # 计算订单总金额
            subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
            # 如果有仅见面交易商品，邮费必须为0
            shipping_fee = 0.00 if has_face_to_face_only else (15.00 if clean_data['delivery_method'] == 'shipping' else 0.00)
            total_amount = subtotal + shipping_fee
            
            # 创建订单
            order = Order(
                customer_name=clean_data['customer_name'],
                customer_email=normalized_email,  # 使用规范化的邮箱
                customer_phone=clean_data['customer_phone'],
                total_amount=total_amount,
                delivery_method=clean_data['delivery_method'],
                payment_method=clean_data['payment_method'],
                customer_address=clean_data['customer_address'],
                notes=clean_data['notes'],
                items=json.dumps(cart_items, ensure_ascii=False)  # 保存商品信息
            )
            
            db.session.add(order)
            db.session.commit()
            
            app.logger.info(f'新订单创建: {order.order_number} - {normalized_email} - 总额: NZD ${total_amount}')
            
            # 将邮件添加到队列中异步发送
            try:
                # 添加客户确认邮件到队列
                email_queue.add_order_confirmation_email(order)
                
                # 添加管理员通知邮件到队列
                email_queue.add_admin_notification_email(order)
                
                app.logger.info(f'订单相关邮件已添加到发送队列: {order.order_number}')
                
            except Exception as e:
                app.logger.error(f'邮件队列添加失败: {order.order_number} - {str(e)}')
            
            # 订单创建成功，清空购物车并跳转到成功页面
            flash('订单提交成功！我会在2小时内联系您确认详情。', 'success')
            return redirect(url_for('order_success', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'订单创建失败: {str(e)} - 用户: {clean_data["customer_email"]}')
            flash('订单提交失败，请稍后重试', 'error')
            return render_template("order_confirm.html")
    
    return render_template("order_confirm.html")


@app.route("/order/success/<int:order_id>")
def order_success(order_id):
    """订单成功页面"""
    order = Order.query.get_or_404(order_id)
    return render_template("order_success.html", order=order)


# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f'404错误: {request.url} - IP: {request.remote_addr}')
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'500错误: {str(error)} - URL: {request.url} - IP: {request.remote_addr}')
    return render_template('500.html'), 500


# 请求日志记录
@app.before_request
def log_request_info():
    """记录请求信息"""
    if not app.debug:
        # 只在生产环境记录详细请求信息
        app.logger.debug(f'请求: {request.method} {request.url} - IP: {request.remote_addr} - UA: {request.headers.get("User-Agent")}')


if __name__ == "__main__":
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
    
    # 启动邮件队列工作线程
    email_queue.start_worker()
    
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("\n正在关闭应用...")
    finally:
        # 停止邮件队列工作线程
        email_queue.stop_worker()