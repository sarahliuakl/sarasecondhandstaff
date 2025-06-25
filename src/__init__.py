from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from .models import db, Admin
from .email_queue import email_queue
from .config import config
import os
import logging
from logging.handlers import RotatingFileHandler

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message = '请先登录以访问管理后台'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name]())

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    csrf.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    email_queue.app = app

    # Register blueprints
    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .api.routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Error handlers
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

    # Request logging
    @app.before_request
    def log_request_info():
        from flask import request
        if not app.debug:
            app.logger.debug(f'请求: {request.method} {request.url} - IP: {request.remote_addr} - UA: {request.headers.get("User-Agent")}')

    with app.app_context():
        db.create_all()
    
    email_queue.start_worker()

    return app
