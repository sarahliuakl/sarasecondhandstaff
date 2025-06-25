"""
主路由模块
包含网站的主要页面路由（首页、关于、联系等）
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from models import db, Product, Order, Message, get_products_by_category, get_product_by_id, get_orders_by_contact, search_products
from utils import sanitize_user_input, validate_form_data, validate_email_address
from email_queue import email_queue
import requests
import datetime
import os
import logging
import json

logger = logging.getLogger(__name__)

# 创建主路由蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """首页"""
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

@main_bp.route("/about")
def about():
    """关于页面"""
    return render_template("about.html")

@main_bp.route("/contact", methods=['GET', 'POST'])
def contact():
    """联系页面"""
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
            logger.info(f'新留言提交: {clean_data["name"]} - {clean_data["contact"]}')
            flash('留言已提交！我会在2小时内回复您。', 'success')
            return redirect(url_for('.contact'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'留言提交失败: {str(e)}')
            flash('提交失败，请稍后重试', 'error')
            return render_template("contact.html")
    
    return render_template("contact.html")

@main_bp.route("/help")
def help_page():
    """帮助页面"""
    return render_template("help.html")

@main_bp.route("/products")
def products():
    """产品列表页面"""
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    
    # 获取所有分类用于筛选
    categories = Product.CATEGORIES
    
    # 根据筛选条件获取产品
    if search:
        product_list = search_products(search)
    else:
        product_list = get_products_by_category(category, available_only=True)
    
    return render_template("products.html", 
                         products=product_list, 
                         categories=categories,
                         current_category=category,
                         search_term=search)

@main_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    """产品详情页"""
    product = get_product_by_id(product_id)
    if not product or not product.is_available():
        flash('商品不存在或已售出', 'error')
        return redirect(url_for('.products'))
    
    return render_template("product_detail.html", product=product)

@main_bp.route("/cart")
def cart():
    """购物车页面"""
    return render_template("cart.html")

@main_bp.route("/order/query")
def order_query():
    """订单查询页面"""
    return render_template("order_query.html")

@main_bp.route("/order/search", methods=['POST'])
def order_search():
    """订单查询处理"""
    form_data = {'contact': request.form.get('contact', '')}
    clean_data = sanitize_user_input(form_data)
    
    is_valid, errors = validate_form_data(clean_data, ['contact'])
    
    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('.order_query'))
    
    orders = get_orders_by_contact(clean_data['contact'])
    
    logger.info(f'订单查询: {clean_data["contact"]} - 找到{len(orders)}个订单')
    
    return render_template("order_results.html", orders=orders, contact_info=clean_data['contact'])

@main_bp.route("/order/confirm", methods=['GET', 'POST'])
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
            return redirect(url_for('.cart'))
        
        try:
            cart_items = json.loads(cart_data)
            if not cart_items:
                flash('购物车是空的', 'error')
                return redirect(url_for('.cart'))
            
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
            
            logger.info(f'新订单创建: {order.order_number} - {normalized_email} - 总额: NZD ${total_amount}')
            
            # 将邮件添加到队列中异步发送
            try:
                # 添加客户确认邮件到队列
                email_queue.add_order_confirmation_email(order)
                
                # 添加管理员通知邮件到队列
                email_queue.add_admin_notification_email(order)
                
                logger.info(f'订单相关邮件已添加到发送队列: {order.order_number}')
                
            except Exception as e:
                logger.error(f'邮件队列添加失败: {order.order_number} - {str(e)}')
            
            # 订单创建成功，清空购物车并跳转到成功页面
            flash('订单提交成功！我会在2小时内联系您确认详情。', 'success')
            return redirect(url_for('.order_success', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'订单创建失败: {str(e)} - 用户: {clean_data["customer_email"]}')
            flash('订单提交失败，请稍后重试', 'error')
            return render_template("order_confirm.html")
    
    return render_template("order_confirm.html")

@main_bp.route("/order/success/<int:order_id>")
def order_success(order_id):
    """订单成功页面"""
    order = Order.query.get_or_404(order_id)
    return render_template("order_success.html", order=order)