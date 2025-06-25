from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from models import db, Admin
from email_queue import email_queue
from admin_routes import admin_bp
from config import config
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

# 注册蓝图
# 管理后台蓝图
app.register_blueprint(admin_bp)

# Web前端蓝图
from routes.web_routes import web_bp
app.register_blueprint(web_bp)

# API蓝图
from routes.api_routes import api_bp
app.register_blueprint(api_bp)

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    from flask import render_template, request
    app.logger.warning(f'404错误: {request.url} - IP: {request.remote_addr}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    from flask import render_template, request
    db.session.rollback()
    app.logger.error(f'500错误: {str(error)} - URL: {request.url} - IP: {request.remote_addr}')
    return render_template('500.html'), 500

# 请求日志记录
@app.before_request
def log_request_info():
    """记录请求信息"""
    from flask import request
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