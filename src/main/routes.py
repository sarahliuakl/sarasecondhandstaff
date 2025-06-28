from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_babel import _, get_locale
from . import main
from ..models import Product, Order, Message, db, get_all_site_info_data
from ..i18n import set_language, LANGUAGES

def validate_and_set_language(lang):
    """验证并设置语言"""
    # 兼容 zh 自动切换为 zh_CN
    if lang == 'zh':
        lang = 'zh_CN'
    if lang and lang in LANGUAGES:
        set_language(lang)
    elif lang and lang not in LANGUAGES:
        # 如果语言不支持，重定向到默认语言
        return redirect(url_for(request.endpoint, lang='en', **{k: v for k, v in request.view_args.items() if k != 'lang'}))
    return None

@main.route('/<lang>/')
def index(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    # 获取最新的几个产品显示在首页
    products = Product.query.filter(Product.stock_status == 'available').order_by(Product.created_at.desc()).limit(6).all()
    return render_template('index.html', products=products)

@main.route('/<lang>/products')
def products(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
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

@main.route('/<lang>/product/<int:product_id>')
def product_detail(product_id, lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/<lang>/cart')
def cart(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    return render_template('cart.html')

@main.route('/<lang>/order/confirm', methods=['GET', 'POST'])
def order_confirm(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    return render_template('order_confirm.html')

@main.route('/<lang>/order/success')
def order_success(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    return render_template('order_success.html')

@main.route('/<lang>/order/query', methods=['GET', 'POST'])
def order_query(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        # 处理订单查询请求
        contact = request.form.get('contact', '').strip()
        
        if not contact:
            flash(_('Please enter your contact information'), 'error')
            return render_template('order_query.html')
        
        try:
            # 查询订单
            from ..models import get_orders_by_contact
            orders = get_orders_by_contact(contact)
            
            # 直接渲染结果页面，不使用session
            return render_template('order_results.html', 
                                 orders=orders,
                                 contact_info=contact,
                                 orders_count=len(orders))
            
        except Exception as e:
            flash(_('Query failed, please try again later'), 'error')
            return render_template('order_query.html')
    
    return render_template('order_query.html')


@main.route('/<lang>/info', methods=['GET', 'POST'])
def info(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        # 处理联系表单提交
        name = request.form.get('name')
        contact = request.form.get('contact')
        message = request.form.get('message')
        
        if name and contact and message:
            # 保存消息到数据库
            try:
                message_obj = Message(name=name, contact=contact, message=message)
                db.session.add(message_obj)
                db.session.commit()
                flash(_('消息发送成功！我会在2小时内回复您。'), 'success')
            except Exception as e:
                db.session.rollback()
                flash(_('发送失败，请稍后重试'), 'error')
        else:
            flash(_('请填写完整信息'), 'error')
        
        current_lang = get_locale().language if get_locale() else 'en'
        return redirect(url_for('main.info', lang=current_lang) + '#contact')
    
    # 获取当前语言
    current_lang = get_locale().language if get_locale() else 'en'
    # 将 zh_CN 转换为 zh
    if current_lang == 'zh_CN':
        current_lang = 'zh'
    
    # 获取站点信息数据
    try:
        site_info_data = get_all_site_info_data(current_lang)
    except Exception as e:
        # 如果获取数据失败，使用空字典
        site_info_data = {}
    
    return render_template('info.html', site_info_data=site_info_data)

@main.route('/<lang>/contact', methods=['GET', 'POST'])
def contact(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    # 重定向到新的info页面
    current_lang = get_locale().language if get_locale() else 'en'
    return redirect(url_for('main.info', lang=current_lang) + '#contact')

@main.route('/<lang>/about')
def about(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    # 重定向到新的info页面
    current_lang = get_locale().language if get_locale() else 'en'
    return redirect(url_for('main.info', lang=current_lang) + '#about')

@main.route('/<lang>/help')
def help(lang):
    # 验证并设置语言
    redirect_response = validate_and_set_language(lang)
    if redirect_response:
        return redirect_response
    
    # 重定向到新的info页面
    current_lang = get_locale().language if get_locale() else 'en'
    return redirect(url_for('main.info', lang=current_lang) + '#rules')

@main.route('/set_language/<language>')
def set_language_route(language):
    """语言切换路由"""
    from ..i18n import set_language
    # 处理语言设置，包括兼容性映射
    if language in LANGUAGES:
        set_language(language)
    elif language == 'zh':
        set_language('zh_CN')
    
    # 重定向到用户之前访问的页面或首页
    referrer = request.referrer
    if referrer:
        # 解析URL并替换语言前缀
        from urllib.parse import urlparse
        parsed = urlparse(referrer)
        path_parts = parsed.path.strip('/').split('/')

        # 移除第一个语言前缀（如果存在）
        # 包括兼容性处理：'zh' 映射到 'zh_CN'
        if path_parts and (path_parts[0] in LANGUAGES or path_parts[0] == 'zh'):
            path_parts.pop(0)
        
        # 构建新的路径
        new_path = '/' + language
        if path_parts:
            new_path += '/' + '/'.join(path_parts)
        return redirect(new_path)
    
    # 如果没有referrer，重定向到首页
    return redirect(url_for('main.index', lang=language))
