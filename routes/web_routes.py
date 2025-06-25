"""
Web路由总蓝图
整合所有前端路由功能模块
"""

from flask import Blueprint
from routes.main_routes import main_bp
from routes.helper_routes import helper_bp

# 创建Web总蓝图
web_bp = Blueprint('web', __name__)

# 注册子蓝图
web_bp.register_blueprint(main_bp)
web_bp.register_blueprint(helper_bp)