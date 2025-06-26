from flask import render_template, request, redirect, url_for, flash, jsonify
from . import main
from ..models import Product, Order, Message, db

@main.route('/')
def index():
    # 获取最新的几个产品显示在首页
    products = Product.query.filter(Product.stock_status == 'available').order_by(Product.created_at.desc()).limit(6).all()
    return render_template('index.html', products=products)

@main.route('/products')
def products():
    # 获取搜索参数
    search_term = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    condition = request.args.get('condition', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')  # newest, oldest, price_asc, price_desc, name
    
    # 开始构建查询
    query = Product.query
    
    # 搜索条件
    if search_term:
        search_filter = db.or_(
            Product.name.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%'),
            Product.category.ilike(f'%{search_term}%')
        )
        query = query.filter(search_filter)
    
    # 分类筛选
    if category:
        query = query.filter(Product.category == category)
    
    # 成色筛选
    if condition:
        query = query.filter(Product.condition == condition)
    
    # 价格筛选
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # 只显示可用商品
    query = query.filter(Product.stock_status == Product.STATUS_AVAILABLE)
    
    # 排序
    if sort_by == 'oldest':
        query = query.order_by(Product.created_at.asc())
    elif sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    else:  # newest (default)
        query = query.order_by(Product.created_at.desc())
    
    # 执行查询
    products = query.all()
    
    # 获取分类列表用于筛选
    categories = Product.CATEGORIES
    
    # 获取成色选项
    conditions = ['全新', '9成新', '8成新', '7成新', '6成新及以下']
    
    return render_template('products.html', 
                         products=products,
                         categories=categories,
                         conditions=conditions,
                         search_term=search_term,
                         current_category=category,
                         current_condition=condition,
                         current_min_price=min_price,
                         current_max_price=max_price,
                         current_sort=sort_by)

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/cart')
def cart():
    return render_template('cart.html')

@main.route('/order/confirm', methods=['GET', 'POST'])
def order_confirm():
    return render_template('order_confirm.html')

@main.route('/order/success')
def order_success():
    return render_template('order_success.html')

@main.route('/order/query', methods=['GET', 'POST'])
def order_query():
    return render_template('order_query.html')

@main.route('/info', methods=['GET', 'POST'])
def info():
    if request.method == 'POST':
        # 处理联系表单提交
        name = request.form.get('name')
        contact = request.form.get('contact')
        message = request.form.get('message')
        
        if name and contact and message:
            # 这里可以添加保存消息到数据库的逻辑
            # message_obj = Message(name=name, contact=contact, message=message)
            # db.session.add(message_obj)
            # db.session.commit()
            
            flash('消息发送成功！我会在2小时内回复您。', 'success')
        else:
            flash('请填写完整信息', 'error')
        
        return redirect(url_for('main.info') + '#contact')
    
    return render_template('info.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    # 重定向到新的info页面
    return redirect(url_for('main.info') + '#contact')

@main.route('/about')
def about():
    # 重定向到新的info页面
    return redirect(url_for('main.info') + '#about')

@main.route('/help')
def help():
    # 重定向到新的info页面
    return redirect(url_for('main.info') + '#rules')
