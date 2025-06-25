"""
Sara二手售卖网站 - 管理后台路由
包含管理员登录、产品管理、订单管理等功能
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from models import db, Admin, Product, Order, Message, SiteSettings
from models import get_admin_by_username, create_admin, get_site_setting, set_site_setting
from models import get_low_stock_products, get_out_of_stock_products, get_inventory_stats
from models import get_sales_stats, get_monthly_sales_trend, get_popular_products, get_customer_stats
from utils import sanitize_user_input, validate_form_data, validate_email_address
from file_upload import upload_image, delete_image, get_image_url
import logging

# 创建管理后台蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)


@admin_bp.route('/')
def index():
    """管理后台主页重定向"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))


@admin_bp.route('/login', methods=['GET', 'POST'])
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


@admin_bp.route('/logout')
@login_required
def logout():
    """管理员登出"""
    logger.info(f'管理员登出: {current_user.username}')
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
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
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         unread_messages=unread_messages,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products)


@admin_bp.route('/profile', methods=['GET', 'POST'])
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


@admin_bp.route('/change-password', methods=['GET', 'POST'])
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


@admin_bp.route('/site-settings', methods=['GET', 'POST'])
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


@admin_bp.route('/products')
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


@admin_bp.route('/orders')
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


@admin_bp.route('/messages')
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


@admin_bp.route('/product/create', methods=['GET', 'POST'])
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
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
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
            
            # 处理图片 - 支持文件上传和URL输入
            uploaded_images = []
            
            # 处理文件上传
            uploaded_files = request.files.getlist('image_files')
            for file in uploaded_files:
                if file and file.filename != '':
                    success, result, thumbnail = upload_image(file)
                    if success:
                        uploaded_images.append(get_image_url(result))
                        logger.info(f'图片上传成功: {result} - 管理员: {current_user.username}')
                    else:
                        flash(f'图片上传失败: {result}', 'error')
            
            # 处理URL输入
            url_images = request.form.getlist('images')
            valid_url_images = [img.strip() for img in url_images if img.strip()]
            
            # 合并所有图片
            all_images = uploaded_images + valid_url_images
            if all_images:
                product.set_images(all_images)
            
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


@admin_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
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
        
        # 清理用户输入
        clean_data = sanitize_user_input(form_data)
        
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
            
            # 处理图片 - 支持文件上传和URL输入
            uploaded_images = []
            
            # 处理文件上传
            uploaded_files = request.files.getlist('image_files')
            for file in uploaded_files:
                if file and file.filename != '':
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
            existing_images = product.get_images()
            all_images = existing_images + uploaded_images + valid_url_images
            
            # 去重并过滤空值
            unique_images = []
            for img in all_images:
                if img and img not in unique_images:
                    unique_images.append(img)
            
            product.set_images(unique_images)
            
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


@admin_bp.route('/product/<int:product_id>/delete', methods=['POST'])
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


@admin_bp.route('/order/<int:order_id>/update-status', methods=['POST'])
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


@admin_bp.route('/message/<int:message_id>/reply', methods=['POST'])
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


@admin_bp.route('/message/<int:message_id>/archive', methods=['POST'])
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


@admin_bp.route('/message/<int:message_id>/delete', methods=['POST'])
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


@admin_bp.route('/product/<int:product_id>/inventory', methods=['POST'])
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


@admin_bp.route('/analytics')
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


@admin_bp.route('/analytics/api/sales')
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


@admin_bp.route('/analytics/api/trend')
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