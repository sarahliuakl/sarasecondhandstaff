from flask import jsonify, request, g
from functools import wraps
import time
import sys
from . import api
from ..models import Product, Category, APIUsageLog, get_all_categories, get_product_by_id, get_products_by_category


def log_api_usage(f):
    """API使用日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        endpoint = request.endpoint
        method = request.method
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # 获取API密钥信息（如果有的话）
        api_key_hash = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
            # 只记录前8位和后4位，中间用*代替
            if len(api_key) > 12:
                api_key_hash = api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:]
            else:
                api_key_hash = api_key[:4] + '*' * (len(api_key) - 4)
        
        # 获取请求数据
        request_data = None
        if request.is_json:
            request_data = request.get_json()
        elif request.form:
            request_data = dict(request.form)
        
        try:
            # 执行原始函数
            response = f(*args, **kwargs)
            
            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 获取响应信息
            if isinstance(response, tuple):
                response_data, status_code = response
                response_size = len(str(response_data))
            else:
                response_data = response
                status_code = 200
                response_size = len(str(response_data))
            
            # 记录成功的API使用
            APIUsageLog.log_api_request(
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                api_key_hash=api_key_hash,
                request_data=request_data,
                response_status=status_code,
                response_size=response_size,
                processing_time=processing_time,
                success=True
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000
            
            # 记录失败的API使用
            APIUsageLog.log_api_request(
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                api_key_hash=api_key_hash,
                request_data=request_data,
                response_status=500,
                response_size=0,
                processing_time=processing_time,
                error_message=str(e),
                success=False
            )
            
            # 重新抛出异常
            raise e
    
    return decorated_function

@api.route('/')
@log_api_usage
def index():
    return jsonify({
        'message': 'Welcome to the Sara Second Hand Shop API',
        'version': '1.0.0',
        'endpoints': {
            'products': '/api/products',
            'categories': '/api/categories',
            'single_product': '/api/products/{id}',
            'category_products': '/api/categories/{id}/products'
        }
    })

@api.route('/products', methods=['GET'])
@log_api_usage
def get_products():
    products = Product.query.filter(Product.stock_status == Product.STATUS_AVAILABLE).all()
    return jsonify([product.to_dict() for product in products])

@api.route('/products/<int:product_id>', methods=['GET'])
@log_api_usage
def get_product(product_id):
    product = get_product_by_id(product_id)
    if product:
        return jsonify(product.to_dict())
    return jsonify({'error': 'Product not found'}), 404

@api.route('/categories', methods=['GET'])
@log_api_usage
def get_categories():
    categories = get_all_categories()
    return jsonify([category.to_dict() for category in categories])

@api.route('/categories/<int:category_id>/products', methods=['GET'])
@log_api_usage
def get_products_in_category(category_id):
    products = get_products_by_category(category_id)
    return jsonify([product.to_dict() for product in products])
