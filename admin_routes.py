"""
Sara二手售卖网站 - 管理后台路由
包含管理员登录、产品管理、订单管理等功能
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from models import db, Admin, Product, Order, Message, SiteSettings
from models import get_admin_by_username, create_admin, get_site_setting, set_site_setting
from utils import sanitize_user_input, validate_form_data, validate_email_address
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
    # 获取统计数据
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
    
    # 获取最近的订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # 获取未读留言
    unread_messages = Message.query.filter(Message.status == 'unread').limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         unread_messages=unread_messages)


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