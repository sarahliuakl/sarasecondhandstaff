from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Product, Order, Message, get_products_by_category, get_product_by_id
import requests
import datetime
import os

app = Flask(__name__)

# 应用配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sara-secondhand-shop-2025'

# 初始化数据库
db.init_app(app)

@app.route("/")
def index():
    # 获取奥克兰天气
    api_key = "dc99157b60b2a5a2194a471c839050c9"
    weather = None
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
        # 处理留言表单提交
        name = request.form.get('name', '').strip()
        contact_info = request.form.get('contact', '').strip()
        message_content = request.form.get('message', '').strip()
        
        # 表单验证
        if not all([name, contact_info, message_content]):
            flash('请填写所有必填字段', 'error')
            return render_template("contact.html")
        
        # 保存留言到数据库
        message = Message(
            name=name,
            contact=contact_info,
            message=message_content
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            flash('留言已提交！我会在2小时内回复您。', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            db.session.rollback()
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
def add_to_cart():
    """添加商品到购物车（API接口）"""
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
            'condition': product.condition
        },
        'quantity': quantity
    })


@app.route("/order/query")
def order_query():
    """订单查询页面"""
    return render_template("order_query.html")


@app.route("/order/search", methods=['POST'])
def order_search():
    """订单查询处理"""
    contact_info = request.form.get('contact', '').strip()
    
    if not contact_info:
        flash('请输入邮箱或电话号码', 'error')
        return redirect(url_for('order_query'))
    
    from models import get_orders_by_contact
    orders = get_orders_by_contact(contact_info)
    
    return render_template("order_results.html", orders=orders, contact_info=contact_info)


@app.route("/order/confirm", methods=['GET', 'POST'])
def order_confirm():
    """订单确认页面"""
    if request.method == 'POST':
        # 处理订单提交
        customer_name = request.form.get('customer_name', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        delivery_method = request.form.get('delivery_method', '')
        payment_method = request.form.get('payment_method', '')
        customer_address = request.form.get('customer_address', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # 验证必填字段
        if not all([customer_name, customer_email, delivery_method, payment_method]):
            flash('请填写所有必填字段', 'error')
            return render_template("order_confirm.html")
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, customer_email):
            flash('请输入有效的邮箱地址', 'error')
            return render_template("order_confirm.html")
        
        # 如果选择邮寄，地址是必填的
        if delivery_method == 'shipping' and not customer_address:
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
            
            # 计算订单总金额
            subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
            shipping_fee = 15.00 if delivery_method == 'shipping' else 0.00
            total_amount = subtotal + shipping_fee
            
            # 创建订单
            order = Order(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                total_amount=total_amount,
                delivery_method=delivery_method,
                payment_method=payment_method,
                customer_address=customer_address,
                notes=notes,
                items=json.dumps(cart_items, ensure_ascii=False)  # 保存商品信息
            )
            
            db.session.add(order)
            db.session.commit()
            
            # 订单创建成功，清空购物车并跳转到成功页面
            flash('订单提交成功！我会在2小时内联系您确认详情。', 'success')
            return redirect(url_for('order_success', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
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
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == "__main__":
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)