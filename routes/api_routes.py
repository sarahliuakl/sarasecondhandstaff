"""
API路由总蓝图
整合所有API功能模块
"""

from flask import Blueprint
from routes.api.main import api_main
from routes.api.products import api_products
from routes.api.categories import api_categories
from routes.api.inventory import api_inventory

# 创建API总蓝图
api_bp = Blueprint('api', __name__)

# 注册子蓝图
api_bp.register_blueprint(api_main)
api_bp.register_blueprint(api_products)
api_bp.register_blueprint(api_categories)
api_bp.register_blueprint(api_inventory)