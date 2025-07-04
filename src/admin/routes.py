"""
Sara二手售卖网站 - 管理后台路由
包含管理员登录、产品管理、订单管理等功能
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from ..models import db, Admin, Product, Order, Message, SiteSettings, Category
from ..models import SiteInfoSection, SiteInfoItem, SiteInfoTranslation
from ..models import get_admin_by_username, create_admin, get_site_setting, set_site_setting
from ..models import get_low_stock_products, get_out_of_stock_products, get_inventory_stats
from ..models import get_sales_stats, get_monthly_sales_trend, get_popular_products, get_customer_stats
from ..models import get_all_categories, get_category_by_id, create_category
from ..models import get_api_usage_stats, get_recent_api_logs
from ..models import get_site_info_sections, get_site_info_section_by_key, get_all_site_info_data
from ..utils import sanitize_user_input, sanitize_rich_text, validate_form_data, validate_email_address
from ..file_upload import upload_image, delete_image, get_image_url
from ..api_auth import APIKeyManager
import logging
logger = logging.getLogger(__name__)
from . import admin




@admin.route('/')
def index():
    """管理后台首页 - 重定向到仪表板"""
    return redirect(url_for('admin.dashboard'))


@admin.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        form_data = {
            'username': request.form.get('username', ''),
            'password': request.form.get('password', '')
        }
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
        # 验证表单数据
        is_valid, errors = validate_form_data(clean_data, ['username', 'password'])
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/login.html')
        
        # 验证管理员凭据
        admin = get_admin_by_username(clean_data['username'])
        if admin and admin.check_password(clean_data['password']) and admin.is_active:
            # 更新最后登录时间
            admin.update_last_login()
            db.session.commit()
            
            # 登录用户
            login_user(admin, remember=True)
            
            logger.info(f'管理员登录成功: {admin.username}')
            
            # 获取下一页URL
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('admin.dashboard')
            
            return redirect(next_page)
        else:
            flash('用户名或密码错误', 'error')
            logger.warning(f'管理员登录失败: {clean_data["username"]}')
    
    return render_template('admin/login.html')


@admin.route('/logout')
@login_required
def logout():
    """管理员登出"""
    logger.info(f'管理员登出: {current_user.username}')
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('admin.login'))


@admin.route('/dashboard')
@login_required
def dashboard():
    """管理后台首页"""
    # 获取基础统计数据
    stats = {
        'total_products': Product.query.count(),
        'available_products': Product.query.filter(Product.stock_status == 'available').count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter(Order.status == 'pending').count(),
        'unread_messages': Message.query.filter(Message.status == 'unread').count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.status.in_(['paid', 'completed'])
        ).scalar() or 0
    }
    
    # 获取库存统计数据
    inventory_stats = get_inventory_stats()
    stats.update(inventory_stats)
    
    # 获取低库存和缺货产品
    low_stock_products = get_low_stock_products()
    out_of_stock_products = get_out_of_stock_products()
    
    # 获取最近的订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # 获取未读留言
    unread_messages = Message.query.filter(Message.status == 'unread').limit(5).all()
    
    # 获取API使用统计数据
    api_stats = get_api_usage_stats()
    
    # 获取最近的API使用日志
    recent_api_logs = get_recent_api_logs(10)
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         unread_messages=unread_messages,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products,
                         api_stats=api_stats,
                         recent_api_logs=recent_api_logs)


@admin.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """管理员个人资料页面"""
    if request.method == 'POST':
        form_data = {
            'username': request.form.get('username', ''),
            'email': request.form.get('email', '')
        }
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
        # 验证表单数据
        is_valid, errors = validate_form_data(clean_data, ['username', 'email'])
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/profile.html', admin=current_user)
        
        # 验证邮箱格式
        is_email_valid, normalized_email = validate_email_address(clean_data['email'])
        if not is_email_valid:
            flash('请输入有效的邮箱地址', 'error')
            return render_template('admin/profile.html', admin=current_user)
        
        # 检查用户名是否已存在（排除当前用户）
        existing_admin = Admin.query.filter(
            Admin.username == clean_data['username'],
            Admin.id != current_user.id
        ).first()
        if existing_admin:
            flash('用户名已存在', 'error')
            return render_template('admin/profile.html', admin=current_user)
        
        # 检查邮箱是否已存在（排除当前用户）
        existing_email = Admin.query.filter(
            Admin.email == normalized_email,
            Admin.id != current_user.id
        ).first()
        if existing_email:
            flash('邮箱已存在', 'error')
            return render_template('admin/profile.html', admin=current_user)
        
        try:
            # 更新管理员信息
            current_user.username = clean_data['username']
            current_user.email = normalized_email
            db.session.commit()
            
            logger.info(f'管理员资料更新: {current_user.username}')
            flash('个人资料更新成功', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'更新管理员资料失败: {str(e)}')
            flash('更新失败，请稍后重试', 'error')
    
    return render_template('admin/profile.html', admin=current_user)


@admin.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        form_data = {
            'current_password': request.form.get('current_password', ''),
            'new_password': request.form.get('new_password', ''),
            'confirm_password': request.form.get('confirm_password', '')
        }
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
        # 验证表单数据
        is_valid, errors = validate_form_data(clean_data, ['current_password', 'new_password', 'confirm_password'])
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/change_password.html')
        
        # 验证当前密码
        if not current_user.check_password(clean_data['current_password']):
            flash('当前密码错误', 'error')
            return render_template('admin/change_password.html')
        
        # 验证新密码长度
        if len(clean_data['new_password']) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('admin/change_password.html')
        
        # 验证密码确认
        if clean_data['new_password'] != clean_data['confirm_password']:
            flash('两次输入的密码不一致', 'error')
            return render_template('admin/change_password.html')
        
        try:
            # 更新密码
            current_user.set_password(clean_data['new_password'])
            db.session.commit()
            
            logger.info(f'管理员密码修改: {current_user.username}')
            flash('密码修改成功', 'success')
            return redirect(url_for('admin.profile'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'修改密码失败: {str(e)}')
            flash('修改失败，请稍后重试', 'error')
    
    return render_template('admin/change_password.html')


@admin.route('/site-settings', methods=['GET', 'POST'])
@login_required
def site_settings():
    """网站设置页面"""
    if request.method == 'POST':
        # 获取所有表单数据
        site_name = request.form.get('site_name', '')
        site_description = request.form.get('site_description', '')
        contact_email = request.form.get('contact_email', '')
        contact_phone = request.form.get('contact_phone', '')
        
        try:
            # 更新网站设置
            set_site_setting('site_name', site_name, '网站名称')
            set_site_setting('site_description', site_description, '网站描述')
            set_site_setting('contact_email', contact_email, '联系邮箱')
            set_site_setting('contact_phone', contact_phone, '联系电话')
            
            db.session.commit()
            
            logger.info(f'网站设置更新: {current_user.username}')
            flash('网站设置更新成功', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'更新网站设置失败: {str(e)}')
            flash('更新失败，请稍后重试', 'error')
    
    # 获取当前设置
    settings = {
        'site_name': get_site_setting('site_name', 'Sara二手商店'),
        'site_description': get_site_setting('site_description', '新西兰优质二手商品交易平台'),
        'contact_email': get_site_setting('contact_email', 'sara@sarasecondhand.com'),
        'contact_phone': get_site_setting('contact_phone', '+64 21 123 4567')
    }
    
    return render_template('admin/site_settings.html', settings=settings)


@admin.route('/products')
@login_required
def products():
    """产品管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取筛选参数
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    
    # 构建查询
    query = Product.query
    
    if category:
        query = query.filter(Product.category == category)
    
    if status:
        query = query.filter(Product.stock_status == status)
    
    if search:
        query = query.filter(
            Product.name.contains(search) | 
            Product.description.contains(search)
        )
    
    # 分页查询
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/products.html', 
                         products=products,
                         categories=Product.CATEGORIES,
                         statuses=Product.STOCK_STATUSES,
                         current_category=category,
                         current_status=status,
                         search_term=search)


@admin.route('/orders')
@login_required
def orders():
    """订单管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取筛选参数
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    
    # 构建查询
    query = Order.query
    
    if status:
        query = query.filter(Order.status == status)
    
    if search:
        query = query.filter(
            Order.order_number.contains(search) |
            Order.customer_name.contains(search) |
            Order.customer_email.contains(search)
        )
    
    # 分页查询
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/orders.html',
                         orders=orders,
                         statuses=Order.ORDER_STATUSES,
                         current_status=status,
                         search_term=search)


@admin.route('/messages')
@login_required
def messages():
    """留言管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取筛选参数
    status = request.args.get('status')
    
    # 构建查询
    query = Message.query
    
    if status:
        query = query.filter(Message.status == status)
    
    # 分页查询
    messages = query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/messages.html',
                         messages=messages,
                         statuses=Message.MESSAGE_STATUSES,
                         current_status=status)


@admin.route('/product/create', methods=['GET', 'POST'])
@login_required
def product_create():
    """创建产品页面"""
    if request.method == 'POST':
        # 获取表单数据
        form_data = {
            'name': request.form.get('name', ''),
            'description': request.form.get('description', ''),
            'price': request.form.get('price', ''),
            'category': request.form.get('category', ''),
            'condition': request.form.get('condition', ''),
            'stock_status': request.form.get('stock_status', ''),
            'face_to_face_only': request.form.get('face_to_face_only') == '1',
            'quantity': request.form.get('quantity', '1'),
            'low_stock_threshold': request.form.get('low_stock_threshold', '1'),
            'track_inventory': request.form.get('track_inventory') == '1'
        }
        
        # 清理用户输入 - 单独处理描述字段
        description = form_data.pop('description', '')  # 先取出描述字段
        clean_data = sanitize_user_input(form_data)     # 清理其他字段
        clean_data['description'] = sanitize_rich_text(description)  # 单独处理描述字段
        
        # 验证必填字段
        required_fields = ['name', 'price', 'category', 'condition', 'stock_status']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/product_form.html',
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证价格
        try:
            price = float(clean_data['price'])
            if price <= 0:
                flash('价格必须大于0', 'error')
                return render_template('admin/product_form.html',
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('价格格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证库存数量
        try:
            quantity = int(clean_data['quantity'])
            if quantity < 0:
                flash('库存数量不能为负数', 'error')
                return render_template('admin/product_form.html',
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('库存数量格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证低库存阈值
        try:
            low_stock_threshold = int(clean_data['low_stock_threshold'])
            if low_stock_threshold < 0:
                flash('低库存阈值不能为负数', 'error')
                return render_template('admin/product_form.html',
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('低库存阈值格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        try:
            # 创建产品
            product = Product(
                name=clean_data['name'],
                description=clean_data['description'],
                price=price,
                category=clean_data['category'],
                condition=clean_data['condition'],
                stock_status=clean_data['stock_status'],
                face_to_face_only=clean_data['face_to_face_only'],
                quantity=quantity,
                low_stock_threshold=low_stock_threshold,
                track_inventory=clean_data['track_inventory']
            )
            
            # 处理图片 - 支持文件上传和URL输入，限制最大数量
            uploaded_images = []
            
            # 处理文件上传
            uploaded_files = request.files.getlist('image_files')
            for file in uploaded_files:
                if file and file.filename != '':
                    # 检查图片数量限制
                    if len(uploaded_images) >= Product.MAX_IMAGES:
                        flash(f'最多只能上传{Product.MAX_IMAGES}张图片', 'error')
                        break
                    
                    success, result, thumbnail = upload_image(file)
                    if success:
                        uploaded_images.append(get_image_url(result))
                        logger.info(f'图片上传成功: {result} - 管理员: {current_user.username}')
                    else:
                        flash(f'图片上传失败: {result}', 'error')
            
            # 处理URL输入
            url_images = request.form.getlist('images')
            valid_url_images = [img.strip() for img in url_images if img.strip()]
            
            # 合并所有图片并限制数量
            all_images = (uploaded_images + valid_url_images)[:Product.MAX_IMAGES]
            if all_images:
                product.set_images(all_images)
            
            # 处理封面图片
            cover_image = request.form.get('cover_image', '').strip()
            if cover_image and cover_image in all_images:
                product.cover_image = cover_image
            elif all_images:
                # 如果没有指定封面图片，使用第一张图片
                product.cover_image = all_images[0]
            
            # 处理规格
            spec_keys = request.form.getlist('spec_keys')
            spec_values = request.form.getlist('spec_values')
            specifications = {}
            for key, value in zip(spec_keys, spec_values):
                if key.strip() and value.strip():
                    specifications[key.strip()] = value.strip()
            if specifications:
                product.set_specifications(specifications)
            
            db.session.add(product)
            db.session.commit()
            
            logger.info(f'产品创建成功: {product.name} - 管理员: {current_user.username}')
            flash('产品添加成功', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'产品创建失败: {str(e)} - 管理员: {current_user.username}')
            flash('添加失败，请稍后重试', 'error')
    
    return render_template('admin/product_form.html',
                         categories=Product.CATEGORIES,
                         statuses=Product.STOCK_STATUSES)


@admin.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    """编辑产品页面"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        # 获取表单数据
        form_data = {
            'name': request.form.get('name', ''),
            'description': request.form.get('description', ''),
            'price': request.form.get('price', ''),
            'category': request.form.get('category', ''),
            'condition': request.form.get('condition', ''),
            'stock_status': request.form.get('stock_status', ''),
            'face_to_face_only': request.form.get('face_to_face_only') == '1',
            'quantity': request.form.get('quantity', '1'),
            'low_stock_threshold': request.form.get('low_stock_threshold', '1'),
            'track_inventory': request.form.get('track_inventory') == '1'
        }
        
        # 清理用户输入 - 单独处理描述字段
        description = form_data.pop('description', '')  # 先取出描述字段
        clean_data = sanitize_user_input(form_data)     # 清理其他字段
        clean_data['description'] = sanitize_rich_text(description)  # 单独处理描述字段
        
        # 验证必填字段
        required_fields = ['name', 'price', 'category', 'condition', 'stock_status']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/product_form.html',
                                 product=product,
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证价格
        try:
            price = float(clean_data['price'])
            if price <= 0:
                flash('价格必须大于0', 'error')
                return render_template('admin/product_form.html',
                                     product=product,
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('价格格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 product=product,
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证库存数量
        try:
            quantity = int(clean_data['quantity'])
            if quantity < 0:
                flash('库存数量不能为负数', 'error')
                return render_template('admin/product_form.html',
                                     product=product,
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('库存数量格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 product=product,
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        # 验证低库存阈值
        try:
            low_stock_threshold = int(clean_data['low_stock_threshold'])
            if low_stock_threshold < 0:
                flash('低库存阈值不能为负数', 'error')
                return render_template('admin/product_form.html',
                                     product=product,
                                     categories=Product.CATEGORIES,
                                     statuses=Product.STOCK_STATUSES)
        except ValueError:
            flash('低库存阈值格式不正确', 'error')
            return render_template('admin/product_form.html',
                                 product=product,
                                 categories=Product.CATEGORIES,
                                 statuses=Product.STOCK_STATUSES)
        
        try:
            # 调试：记录描述内容
            logger.info(f'原始描述内容: {description[:100]}...')
            logger.info(f'清理后描述内容: {clean_data["description"][:100]}...')
            
            # 更新产品信息
            product.name = clean_data['name']
            product.description = clean_data['description']
            product.price = price
            product.category = clean_data['category']
            product.condition = clean_data['condition']
            product.stock_status = clean_data['stock_status']
            product.face_to_face_only = clean_data['face_to_face_only']
            product.quantity = quantity
            product.low_stock_threshold = low_stock_threshold
            product.track_inventory = clean_data['track_inventory']
            
            # 处理图片 - 支持文件上传和URL输入，限制最大数量
            uploaded_images = []
            
            # 处理文件上传
            uploaded_files = request.files.getlist('image_files')
            existing_images = product.get_images()
            
            for file in uploaded_files:
                if file and file.filename != '':
                    # 检查图片数量限制
                    total_images = len(existing_images) + len(uploaded_images)
                    if total_images >= Product.MAX_IMAGES:
                        flash(f'最多只能上传{Product.MAX_IMAGES}张图片，当前已有{len(existing_images)}张', 'error')
                        break
                    
                    success, result, thumbnail = upload_image(file)
                    if success:
                        uploaded_images.append(get_image_url(result))
                        logger.info(f'图片上传成功: {result} - 管理员: {current_user.username}')
                    else:
                        flash(f'图片上传失败: {result}', 'error')
            
            # 处理URL输入
            url_images = request.form.getlist('images')
            valid_url_images = [img.strip() for img in url_images if img.strip()]
            
            # 合并所有图片 - 保留现有图片，添加新上传的图片
            all_images = existing_images + uploaded_images + valid_url_images
            
            # 去重并过滤空值，限制最大数量
            unique_images = []
            for img in all_images:
                if img and img not in unique_images and len(unique_images) < Product.MAX_IMAGES:
                    unique_images.append(img)
            
            product.set_images(unique_images)
            
            # 处理封面图片
            cover_image = request.form.get('cover_image', '').strip()
            if cover_image and cover_image in unique_images:
                product.cover_image = cover_image
            elif unique_images and not product.cover_image:
                # 如果没有设置封面图片且有图片，使用第一张图片
                product.cover_image = unique_images[0]
            
            # 处理规格
            spec_keys = request.form.getlist('spec_keys')
            spec_values = request.form.getlist('spec_values')
            specifications = {}
            for key, value in zip(spec_keys, spec_values):
                if key.strip() and value.strip():
                    specifications[key.strip()] = value.strip()
            product.set_specifications(specifications)
            
            db.session.commit()
            
            logger.info(f'产品更新成功: {product.name} - 管理员: {current_user.username}')
            flash('产品更新成功', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'产品更新失败: {str(e)} - 管理员: {current_user.username}')
            flash('更新失败，请稍后重试', 'error')
    
    return render_template('admin/product_form.html',
                         product=product,
                         categories=Product.CATEGORIES,
                         statuses=Product.STOCK_STATUSES)


@admin.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def product_delete(product_id):
    """删除产品"""
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        
        db.session.delete(product)
        db.session.commit()
        
        logger.info(f'产品删除成功: {product_name} - 管理员: {current_user.username}')
        return jsonify({'success': True, 'message': '产品删除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'产品删除失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': '删除失败，请稍后重试'})


@admin.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
def order_update_status(order_id):
    """更新订单状态"""
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('new_status')
        note = request.form.get('note', '')
        
        if new_status not in dict(Order.ORDER_STATUSES):
            return jsonify({'success': False, 'message': '无效的状态'})
        
        old_status = order.status
        order.status = new_status
        db.session.commit()
        
        logger.info(f'订单状态更新: {order.order_number} {old_status}->{new_status} - 管理员: {current_user.username}')
        
        # TODO: 发送状态更新邮件给客户
        
        return jsonify({'success': True, 'message': '状态更新成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'订单状态更新失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': '更新失败，请稍后重试'})


@admin.route('/message/<int:message_id>/reply', methods=['POST'])
@login_required
def message_reply(message_id):
    """回复留言"""
    try:
        message = Message.query.get_or_404(message_id)
        reply_content = request.form.get('reply_content', '').strip()
        
        if not reply_content:
            return jsonify({'success': False, 'message': '回复内容不能为空'})
        
        message.mark_as_replied(reply_content)
        db.session.commit()
        
        logger.info(f'留言回复成功: ID {message_id} - 管理员: {current_user.username}')
        
        # TODO: 发送回复邮件给客户
        
        return jsonify({'success': True, 'message': '回复发送成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'留言回复失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': '回复失败，请稍后重试'})


@admin.route('/message/<int:message_id>/archive', methods=['POST'])
@login_required
def message_archive(message_id):
    """归档留言"""
    try:
        message = Message.query.get_or_404(message_id)
        message.status = Message.STATUS_ARCHIVED
        db.session.commit()
        
        logger.info(f'留言归档成功: ID {message_id} - 管理员: {current_user.username}')
        return jsonify({'success': True, 'message': '留言已归档'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'留言归档失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': '归档失败，请稍后重试'})


@admin.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
def message_delete(message_id):
    """删除留言"""
    try:
        message = Message.query.get_or_404(message_id)
        customer_name = message.name
        
        db.session.delete(message)
        db.session.commit()
        
        logger.info(f'留言删除成功: {customer_name} - 管理员: {current_user.username}')
        return jsonify({'success': True, 'message': '留言删除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'留言删除失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': '删除失败，请稍后重试'})


@admin.route('/product/<int:product_id>/inventory', methods=['POST'])
@login_required
def product_inventory_update(product_id):
    """更新产品库存"""
    try:
        product = Product.query.get_or_404(product_id)
        action = request.form.get('action')
        quantity = request.form.get('quantity', type=int)
        
        if not action or quantity is None:
            return jsonify({'success': False, 'message': '参数不完整'})
        
        old_quantity = product.quantity
        old_status = product.stock_status
        
        if action == 'set':
            # 设置绝对库存数量
            product.set_stock_quantity(quantity)
        elif action == 'add':
            # 增加库存
            product.increase_stock(quantity)
        elif action == 'reduce':
            # 减少库存
            if not product.reduce_stock(quantity):
                return jsonify({'success': False, 'message': '库存不足，无法减少指定数量'})
        else:
            return jsonify({'success': False, 'message': '无效的操作类型'})
        
        db.session.commit()
        
        # 记录库存变化
        logger.info(f'库存更新: {product.name} ({old_quantity} -> {product.quantity}) - 管理员: {current_user.username}')
        
        # 检查库存状态
        inventory_status = product.get_inventory_status()
        warnings = []
        
        if product.is_low_stock():
            warnings.append(f'库存不足！当前库存: {product.quantity}，警告阈值: {product.low_stock_threshold}')
        
        if product.is_out_of_stock():
            warnings.append('商品已缺货！')
        
        return jsonify({
            'success': True, 
            'message': '库存更新成功',
            'new_quantity': product.quantity,
            'new_status': product.get_status_display(),
            'inventory_status': inventory_status,
            'warnings': warnings
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'库存更新失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@admin.route('/analytics')
@login_required
def analytics():
    """销售分析页面"""
    try:
        # 获取销售统计数据
        sales_stats = get_sales_stats()
        
        # 获取月度销售趋势
        monthly_trend = get_monthly_sales_trend(12)
        
        # 获取热门产品
        popular_products = get_popular_products(10)
        
        # 获取客户统计
        customer_stats = get_customer_stats()
        
        logger.info(f'销售分析页面访问 - 管理员: {current_user.username}')
        
        return render_template('admin/analytics.html', 
                             sales_stats=sales_stats,
                             monthly_trend=monthly_trend,
                             popular_products=popular_products,
                             customer_stats=customer_stats)
                             
    except Exception as e:
        logger.error(f'销售分析页面加载失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'数据加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/analytics/api/sales')
@login_required
def analytics_api_sales():
    """销售数据API"""
    try:
        # 获取日期范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 转换日期格式
        from datetime import datetime
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 获取销售统计
        stats = get_sales_stats(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f'销售数据API错误: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'数据获取失败: {str(e)}'
        })


@admin.route('/analytics/api/trend')
@login_required
def analytics_api_trend():
    """销售趋势数据API"""
    try:
        # 获取月份数参数
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 24)  # 限制在1-24个月之间
        
        # 获取趋势数据
        trend_data = get_monthly_sales_trend(months)
        
        return jsonify({
            'success': True,
            'data': trend_data
        })
        
    except Exception as e:
        logger.error(f'销售趋势API错误: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'数据获取失败: {str(e)}'
        })


# =================
# 分类管理路由
# =================

@admin.route('/categories')
@login_required
def categories():
    """分类管理页面"""
    try:
        # 获取所有分类（包括非活跃的）
        categories = get_all_categories(active_only=False)
        # 修正脏数据，确保sort_order为int类型
        for cat in categories:
            try:
                cat.sort_order = int(cat.sort_order)
            except Exception:
                cat.sort_order = 0
        
        logger.info(f'分类管理页面访问 - 管理员: {current_user.username}')
        return render_template('admin/categories.html', categories=categories)
        
    except Exception as e:
        logger.error(f'分类管理页面加载失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'页面加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """创建分类页面"""
    if request.method == 'POST':
        try:
            form_data = {
                'name': request.form.get('name', '').strip(),
                'display_name': request.form.get('display_name', '').strip(),
                'description': request.form.get('description', '').strip(),
                'slug': request.form.get('slug', '').strip(),
                'icon': request.form.get('icon', '').strip(),
                'sort_order': request.form.get('sort_order', '0')
            }
            
            # 验证必填字段
            if not form_data['name'] or not form_data['display_name']:
                flash('分类名称和显示名称为必填项', 'error')
                return render_template('admin/category_form.html', category=None, form_data=form_data)
            
            # 验证分类名称唯一性
            existing_name = Category.query.filter(Category.name == form_data['name']).first()
            if existing_name:
                flash('分类名称已存在', 'error')
                return render_template('admin/category_form.html', category=None, form_data=form_data)
            
            # 自动生成slug如果为空
            if not form_data['slug']:
                import re
                form_data['slug'] = re.sub(r'[^a-zA-Z0-9\-_]', '', form_data['name'].lower().replace(' ', '-'))
            
            # 验证slug唯一性
            existing_slug = Category.query.filter(Category.slug == form_data['slug']).first()
            if existing_slug:
                flash('URL标识(slug)已存在', 'error')
                return render_template('admin/category_form.html', category=None, form_data=form_data)
            
            # 验证排序值
            try:
                sort_order = int(form_data['sort_order'])
            except ValueError:
                sort_order = 0
            
            # 创建分类
            category = Category(
                name=form_data['name'],
                display_name=form_data['display_name'],
                description=form_data['description'] if form_data['description'] else None,
                slug=form_data['slug'],
                icon=form_data['icon'] if form_data['icon'] else None,
                sort_order=sort_order
            )
            
            db.session.add(category)
            db.session.commit()
            
            logger.info(f'分类创建成功: {category.name} - 管理员: {current_user.username}')
            flash('分类创建成功', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'分类创建失败: {str(e)} - 管理员: {current_user.username}')
            flash(f'创建失败: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', category=None, form_data=None)


@admin.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """编辑分类页面"""
    category = get_category_by_id(category_id)
    if not category:
        flash('分类不存在', 'error')
        return redirect(url_for('admin.categories'))
    
    if request.method == 'POST':
        try:
            form_data = {
                'name': request.form.get('name', '').strip(),
                'display_name': request.form.get('display_name', '').strip(),
                'description': request.form.get('description', '').strip(),
                'slug': request.form.get('slug', '').strip(),
                'icon': request.form.get('icon', '').strip(),
                'sort_order': request.form.get('sort_order', '0'),
                'is_active': request.form.get('is_active') == 'on'
            }
            
            # 验证必填字段
            if not form_data['name'] or not form_data['display_name']:
                flash('分类名称和显示名称为必填项', 'error')
                return render_template('admin/category_form.html', category=category, form_data=form_data)
            
            # 验证分类名称唯一性（排除当前分类）
            existing_name = Category.query.filter(
                Category.name == form_data['name'],
                Category.id != category_id
            ).first()
            if existing_name:
                flash('分类名称已存在', 'error')
                return render_template('admin/category_form.html', category=category, form_data=form_data)
            
            # 验证slug唯一性（排除当前分类）
            existing_slug = Category.query.filter(
                Category.slug == form_data['slug'],
                Category.id != category_id
            ).first()
            if existing_slug:
                flash('URL标识(slug)已存在', 'error')
                return render_template('admin/category_form.html', category=category, form_data=form_data)
            
            # 验证排序值
            try:
                sort_order = int(form_data['sort_order'])
            except ValueError:
                sort_order = 0
            
            # 更新分类信息
            category.name = form_data['name']
            category.display_name = form_data['display_name']
            category.description = form_data['description'] if form_data['description'] else None
            category.slug = form_data['slug']
            category.icon = form_data['icon'] if form_data['icon'] else None
            category.sort_order = sort_order
            category.is_active = form_data['is_active']
            
            db.session.commit()
            
            logger.info(f'分类更新成功: {category.name} - 管理员: {current_user.username}')
            flash('分类更新成功', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'分类更新失败: {str(e)} - 管理员: {current_user.username}')
            flash(f'更新失败: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', category=category, form_data=None)


@admin.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """删除分类"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return jsonify({'success': False, 'message': '分类不存在'})
        
        # 检查是否有产品使用此分类
        product_count = category.products.count()
        if product_count > 0:
            return jsonify({
                'success': False, 
                'message': f'无法删除：还有 {product_count} 个产品使用此分类'
            })
        
        # 删除分类
        db.session.delete(category)
        db.session.commit()
        
        logger.info(f'分类删除成功: {category.name} - 管理员: {current_user.username}')
        return jsonify({'success': True, 'message': '分类删除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'分类删除失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})


@admin.route('/categories/<int:category_id>/toggle-status', methods=['POST'])
@login_required
def toggle_category_status(category_id):
    """切换分类激活状态"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return jsonify({'success': False, 'message': '分类不存在'})
        
        # 切换状态
        category.is_active = not category.is_active
        db.session.commit()
        
        status_text = '激活' if category.is_active else '禁用'
        logger.info(f'分类状态切换: {category.name} -> {status_text} - 管理员: {current_user.username}')
        
        return jsonify({
            'success': True, 
            'message': f'分类已{status_text}',
            'is_active': category.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'分类状态切换失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@admin.route('/categories/api/list')
@login_required
def categories_api_list():
    """分类列表API（用于产品表单的分类选择）"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        categories = get_all_categories(active_only=active_only)
        
        category_list = []
        for cat in categories:
            category_list.append({
                'id': cat.id,
                'name': cat.name,
                'display_name': cat.display_name,
                'slug': cat.slug,
                'icon': cat.icon,
                'is_active': cat.is_active,
                'product_count': cat.get_product_count()
            })
        
        return jsonify({
            'success': True,
            'data': category_list
        })
        
    except Exception as e:
        logger.error(f'分类列表API错误: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'数据获取失败: {str(e)}'
        })


# =================
# API管理路由
# =================

@admin.route('/api-management')
@login_required
def api_management():
    """API管理页面"""
    try:
        # 检查API Key是否已配置
        api_configured = APIKeyManager.is_api_key_configured()
        
        # 获取API使用统计数据
        api_stats = get_api_usage_stats()
        
        # 获取最近的API使用日志（更多条数用于详细显示）
        recent_api_logs = get_recent_api_logs(50)
        
        logger.info(f'API管理页面访问 - 管理员: {current_user.username}')
        return render_template('admin/api_management.html', 
                             api_configured=api_configured,
                             api_stats=api_stats,
                             recent_api_logs=recent_api_logs)
        
    except Exception as e:
        logger.error(f'API管理页面加载失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'页面加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/api/generate-key', methods=['POST'])
@login_required
def api_generate_key():
    """生成新的API Key"""
    try:
        # 生成新的API Key
        api_key = APIKeyManager.generate_api_key()
        
        # 保存到数据库
        APIKeyManager.set_api_key(api_key)
        
        logger.info(f'API Key生成成功 - 管理员: {current_user.username}')
        
        return jsonify({
            'success': True,
            'api_key': api_key,
            'message': 'API Key生成成功'
        })
        
    except Exception as e:
        logger.error(f'API Key生成失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        })


@admin.route('/api/revoke-key', methods=['POST'])
@login_required
def api_revoke_key():
    """撤销API Key"""
    try:
        # 删除API Key配置
        set_site_setting('api_key_hash', '', 'API Key哈希值')
        db.session.commit()
        
        logger.info(f'API Key撤销成功 - 管理员: {current_user.username}')
        
        return jsonify({
            'success': True,
            'message': 'API Key已撤销'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API Key撤销失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'撤销失败: {str(e)}'
        })


# =================
# 站点信息管理路由
# =================

@admin.route('/site-info')
@login_required
def site_info():
    """站点信息管理页面"""
    try:
        # 获取所有站点信息部分和数据
        sections = get_site_info_sections(active_only=False)
        
        logger.info(f'站点信息管理页面访问 - 管理员: {current_user.username}')
        return render_template('admin/site_info.html', sections=sections)
        
    except Exception as e:
        logger.error(f'站点信息管理页面加载失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'页面加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/site-info/section/<int:section_id>')
@login_required
def edit_section(section_id):
    """编辑站点信息部分"""
    try:
        section = SiteInfoSection.query.get_or_404(section_id)
        items = section.get_active_items() if section else []
        
        return render_template('admin/site_info_section.html', 
                             section=section, 
                             items=items,
                             item_types=SiteInfoItem.ITEM_TYPES)
        
    except Exception as e:
        logger.error(f'编辑站点信息部分失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.site_info'))


@admin.route('/site-info/item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """编辑站点信息项"""
    try:
        item = SiteInfoItem.query.get_or_404(item_id)
        
        if request.method == 'POST':
            # 获取表单数据
            item_data = {
                'key': request.form.get('key', '').strip(),
                'item_type': request.form.get('item_type', ''),
                'sort_order': int(request.form.get('sort_order', 0)),
                'is_active': bool(request.form.get('is_active'))
            }
            
            # 更新基本信息
            item.key = item_data['key']
            item.item_type = item_data['item_type']
            item.sort_order = item_data['sort_order']
            item.is_active = item_data['is_active']
            
            # 根据类型处理内容
            content = {}
            if item_data['item_type'] == 'text':
                content['value'] = request.form.get('text_value', '')
            elif item_data['item_type'] == 'contact':
                content['label'] = request.form.get('contact_label', '')
                content['value'] = request.form.get('contact_value', '')
            elif item_data['item_type'] == 'feature':
                content['title'] = request.form.get('feature_title', '')
                content['description'] = request.form.get('feature_description', '')
                content['icon'] = request.form.get('feature_icon', '')
            elif item_data['item_type'] == 'faq':
                content['question'] = request.form.get('faq_question', '')
                content['answer'] = request.form.get('faq_answer', '')
            
            item.set_content(content)
            
            # 处理翻译（如果有英文内容）
            en_content = {}
            has_english = False
            
            if item_data['item_type'] == 'text':
                en_value = request.form.get('text_value_en', '').strip()
                if en_value:
                    en_content['value'] = en_value
                    has_english = True
            elif item_data['item_type'] == 'contact':
                en_label = request.form.get('contact_label_en', '').strip()
                en_value = request.form.get('contact_value_en', '').strip()
                if en_label or en_value:
                    en_content['label'] = en_label
                    en_content['value'] = en_value
                    has_english = True
            elif item_data['item_type'] == 'feature':
                en_title = request.form.get('feature_title_en', '').strip()
                en_description = request.form.get('feature_description_en', '').strip()
                if en_title or en_description:
                    en_content['title'] = en_title
                    en_content['description'] = en_description
                    en_content['icon'] = request.form.get('feature_icon', '')
                    has_english = True
            elif item_data['item_type'] == 'faq':
                en_question = request.form.get('faq_question_en', '').strip()
                en_answer = request.form.get('faq_answer_en', '').strip()
                if en_question or en_answer:
                    en_content['question'] = en_question
                    en_content['answer'] = en_answer
                    has_english = True
            
            # 保存或更新英文翻译
            if has_english:
                en_translation = item.get_translation('en')
                if en_translation:
                    en_translation.set_content(en_content)
                else:
                    en_translation = SiteInfoTranslation(
                        item_id=item.id,
                        language='en'
                    )
                    en_translation.set_content(en_content)
                    db.session.add(en_translation)
            else:
                # 删除英文翻译（如果存在且内容为空）
                en_translation = item.get_translation('en')
                if en_translation:
                    db.session.delete(en_translation)
            
            db.session.commit()
            logger.info(f'站点信息项更新成功: {item.key} - 管理员: {current_user.username}')
            flash('信息项更新成功', 'success')
            return redirect(url_for('admin.edit_section', section_id=item.section_id))
        
        # GET请求 - 显示编辑表单
        return render_template('admin/site_info_item.html', 
                             item=item,
                             item_types=SiteInfoItem.ITEM_TYPES)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'编辑站点信息项失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'操作失败: {str(e)}', 'error')
        return redirect(url_for('admin.site_info'))


@admin.route('/site-info/item/add/<int:section_id>', methods=['GET', 'POST'])
@login_required
def add_item(section_id):
    """添加新的站点信息项"""
    try:
        section = SiteInfoSection.query.get_or_404(section_id)
        
        if request.method == 'POST':
            # 获取表单数据
            item_data = {
                'key': request.form.get('key', '').strip(),
                'item_type': request.form.get('item_type', ''),
                'sort_order': int(request.form.get('sort_order', 0)),
                'is_active': bool(request.form.get('is_active'))
            }
            
            # 验证必填字段
            if not item_data['key'] or not item_data['item_type']:
                flash('标识符和类型为必填项', 'error')
                return render_template('admin/site_info_item.html', 
                                     section=section,
                                     item_types=SiteInfoItem.ITEM_TYPES)
            
            # 检查key是否重复
            existing_item = SiteInfoItem.query.filter(
                SiteInfoItem.section_id == section_id,
                SiteInfoItem.key == item_data['key']
            ).first()
            if existing_item:
                flash('该标识符已存在', 'error')
                return render_template('admin/site_info_item.html', 
                                     section=section,
                                     item_types=SiteInfoItem.ITEM_TYPES)
            
            # 创建新的信息项
            item = SiteInfoItem(
                section_id=section_id,
                key=item_data['key'],
                item_type=item_data['item_type'],
                sort_order=item_data['sort_order'],
                is_active=item_data['is_active']
            )
            
            # 根据类型设置内容
            content = {}
            if item_data['item_type'] == 'text':
                content['value'] = request.form.get('text_value', '')
            elif item_data['item_type'] == 'contact':
                content['label'] = request.form.get('contact_label', '')
                content['value'] = request.form.get('contact_value', '')
            elif item_data['item_type'] == 'feature':
                content['title'] = request.form.get('feature_title', '')
                content['description'] = request.form.get('feature_description', '')
                content['icon'] = request.form.get('feature_icon', '')
            elif item_data['item_type'] == 'faq':
                content['question'] = request.form.get('faq_question', '')
                content['answer'] = request.form.get('faq_answer', '')
            
            item.set_content(content)
            db.session.add(item)
            db.session.commit()
            
            logger.info(f'站点信息项添加成功: {item.key} - 管理员: {current_user.username}')
            flash('信息项添加成功', 'success')
            return redirect(url_for('admin.edit_section', section_id=section_id))
        
        # GET请求 - 显示添加表单
        return render_template('admin/site_info_item.html', 
                             section=section,
                             item_types=SiteInfoItem.ITEM_TYPES)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加站点信息项失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'添加失败: {str(e)}', 'error')
        return redirect(url_for('admin.site_info'))


@admin.route('/site-info/item/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    """删除站点信息项"""
    try:
        item = SiteInfoItem.query.get_or_404(item_id)
        section_id = item.section_id
        
        # 删除项目（包括相关翻译，由于cascade设置会自动删除）
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f'站点信息项删除成功: {item.key} - 管理员: {current_user.username}')
        flash('信息项删除成功', 'success')
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除站点信息项失败: {str(e)} - 管理员: {current_user.username}')
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        })


@admin.route('/site-info/preview')
@login_required
def preview_site_info():
    """预览站点信息页面效果"""
    try:
        # 获取所有站点信息数据（中文）
        site_info_data = get_all_site_info_data('zh')
        
        return render_template('admin/site_info_preview.html', 
                             site_info_data=site_info_data)
        
    except Exception as e:
        logger.error(f'预览站点信息失败: {str(e)} - 管理员: {current_user.username}')
        flash(f'预览失败: {str(e)}', 'error')
        return redirect(url_for('admin.site_info'))