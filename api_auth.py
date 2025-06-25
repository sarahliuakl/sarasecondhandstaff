"""
API认证和权限管理模块
提供API Key验证、权限检查等功能
"""

import secrets
import hashlib
from functools import wraps
from flask import request, jsonify, current_app
from models import db, SiteSettings, get_site_setting, set_site_setting
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """API Key管理器"""
    
    @staticmethod
    def generate_api_key():
        """生成新的API Key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key):
        """对API Key进行哈希处理"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def get_stored_api_key_hash():
        """获取存储的API Key哈希值"""
        return get_site_setting('api_key_hash', '')
    
    @staticmethod
    def set_api_key(api_key):
        """设置新的API Key"""
        hashed_key = APIKeyManager.hash_api_key(api_key)
        set_site_setting('api_key_hash', hashed_key, 'API Key哈希值')
        db.session.commit()
        logger.info('API Key已更新')
        return True
    
    @staticmethod
    def verify_api_key(api_key):
        """验证API Key"""
        if not api_key:
            return False
        
        stored_hash = APIKeyManager.get_stored_api_key_hash()
        if not stored_hash:
            logger.warning('API Key未设置')
            return False
        
        provided_hash = APIKeyManager.hash_api_key(api_key)
        is_valid = secrets.compare_digest(stored_hash, provided_hash)
        
        if not is_valid:
            logger.warning(f'无效的API Key尝试: {api_key[:8]}...')
        
        return is_valid
    
    @staticmethod
    def is_api_key_configured():
        """检查是否已配置API Key"""
        return bool(APIKeyManager.get_stored_api_key_hash())

def require_api_key(f):
    """装饰器：要求有效的API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否已配置API Key
        if not APIKeyManager.is_api_key_configured():
            return jsonify({
                'success': False,
                'error': 'API_NOT_CONFIGURED',
                'message': 'API Key未配置，请联系管理员'
            }), 503
        
        # 从请求头或查询参数获取API Key
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'MISSING_API_KEY',
                'message': '缺少API Key。请在请求头中包含X-API-Key或在查询参数中添加api_key'
            }), 401
        
        # 验证API Key
        if not APIKeyManager.verify_api_key(api_key):
            return jsonify({
                'success': False,
                'error': 'INVALID_API_KEY',
                'message': 'API Key无效'
            }), 403
        
        # 记录API请求
        logger.info(f'API请求: {request.method} {request.path} - Key: {api_key[:8]}...')
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_api_error_response(error_code, message, status_code=400):
    """生成标准的API错误响应"""
    return jsonify({
        'success': False,
        'error': error_code,
        'message': message
    }), status_code

def get_api_success_response(data=None, message=None):
    """生成标准的API成功响应"""
    response = {'success': True}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response)

class APIRateLimit:
    """API速率限制（简单实现）"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, api_key, limit=100, window=3600):
        """检查是否允许请求（每小时限制）"""
        import time
        current_time = time.time()
        
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # 清除过期的请求记录
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key] 
            if current_time - req_time < window
        ]
        
        # 检查是否超过限制
        if len(self.requests[api_key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[api_key].append(current_time)
        return True

# 全局速率限制实例
rate_limiter = APIRateLimit()

def require_rate_limit(limit=100, window=3600):
    """装饰器：API速率限制"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if api_key and not rate_limiter.is_allowed(api_key, limit, window):
                return get_api_error_response(
                    'RATE_LIMIT_EXCEEDED',
                    f'API调用频率过高，每小时限制{limit}次请求',
                    429
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator