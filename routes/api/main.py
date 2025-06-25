"""
主API路由蓝图
提供API入口点和通用功能
"""

from flask import Blueprint, jsonify, request
from api_auth import require_api_key, get_api_success_response, get_api_error_response
import logging

logger = logging.getLogger(__name__)

# 创建API主蓝图
api_main = Blueprint('api_main', __name__, url_prefix='/api/v1')

@api_main.route('/health')
def health_check():
    """API健康检查端点（无需认证）"""
    return get_api_success_response({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'Sara Secondhand Shop API'
    })

@api_main.route('/info')
@require_api_key
def api_info():
    """API信息端点"""
    return get_api_success_response({
        'version': '1.0.0',
        'endpoints': {
            'products': '/api/v1/products',
            'categories': '/api/v1/categories', 
            'inventory': '/api/v1/inventory',
            'health': '/api/v1/health'
        },
        'authentication': 'API Key required',
        'rate_limit': '100 requests per hour'
    })

@api_main.errorhandler(404)
def api_not_found(error):
    """API 404错误处理"""
    return get_api_error_response(
        'NOT_FOUND',
        'API端点不存在',
        404
    )

@api_main.errorhandler(500)
def api_internal_error(error):
    """API 500错误处理"""
    logger.error(f'API内部错误: {str(error)}')
    return get_api_error_response(
        'INTERNAL_ERROR',
        '服务器内部错误',
        500
    )