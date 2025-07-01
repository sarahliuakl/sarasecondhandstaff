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

@api.route('/search/suggestions', methods=['GET'])
@log_api_usage
def search_suggestions():
    """获取搜索建议"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    seen_texts = set()  # 避免重复建议
    
    # 搜索商品名称（优先匹配）
    products = Product.query.filter(
        Product.name.ilike(f'%{query}%'),
        Product.stock_status == Product.STATUS_AVAILABLE
    ).order_by(Product.name.desc()).limit(5).all()
    
    for product in products:
        if product.name not in seen_texts:
            suggestions.append({
                'text': product.name,
                'type': 'product',
                'category': product.get_category_display(),
                'price': f"${product.price}",
                'condition': product.condition
            })
            seen_texts.add(product.name)
    
    # 搜索商品描述（如果名称匹配不够）
    if len(suggestions) < 5:
        desc_products = Product.query.filter(
            Product.description.ilike(f'%{query}%'),
            Product.stock_status == Product.STATUS_AVAILABLE,
            ~Product.name.ilike(f'%{query}%')  # 排除已经通过名称匹配的
        ).order_by(Product.created_at.desc()).limit(3).all()
        
        for product in desc_products:
            if product.name not in seen_texts:
                suggestions.append({
                    'text': product.name,
                    'type': 'product',
                    'category': product.get_category_display(),
                    'price': f"${product.price}",
                    'condition': product.condition
                })
                seen_texts.add(product.name)
    
    # 搜索分类
    from ..models import Product
    for category_code, category_name in Product.CATEGORIES:
        if query.lower() in category_name.lower() and category_name not in seen_texts:
            # 获取该分类的商品数量
            count = Product.query.filter(
                Product.category == category_code,
                Product.stock_status == Product.STATUS_AVAILABLE
            ).count()
            
            suggestions.append({
                'text': category_name,
                'type': 'category',
                'category': None,
                'count': count
            })
            seen_texts.add(category_name)
    
    # 智能建议：如果查询包含价格相关词汇
    price_keywords = ['便宜', '贵', '价格', '多少钱', '优惠']
    if any(keyword in query for keyword in price_keywords):
        # 添加价格范围建议
        suggestions.append({
            'text': '50元以下商品',
            'type': 'price_range',
            'category': None,
            'filter': 'max_price=50'
        })
        suggestions.append({
            'text': '100-200元商品',
            'type': 'price_range', 
            'category': None,
            'filter': 'min_price=100&max_price=200'
        })
    
    # 智能建议：如果查询包含成色相关词汇
    condition_keywords = ['新', '旧', '成色', '品相']
    if any(keyword in query for keyword in condition_keywords):
        conditions = ['全新', '9成新', '8成新']
        for condition in conditions:
            if condition not in seen_texts:
                suggestions.append({
                    'text': f'{condition}商品',
                    'type': 'condition',
                    'category': None,
                    'filter': f'condition={condition}'
                })
                seen_texts.add(condition)
    
    # 限制返回数量
    return jsonify(suggestions[:8])

@api.route('/cart', methods=['POST'])
@log_api_usage
def add_to_cart():
    """添加商品到购物车"""
    data = request.get_json()
    
    if not data or 'product_id' not in data:
        return jsonify({'success': False, 'message': '缺少商品ID'}), 400
    
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'}), 404
    
    if not product.is_available():
        return jsonify({'success': False, 'message': '商品已售出'}), 400
    
    # 返回商品信息供前端处理
    images = product.get_images()
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': images[0] if images else None,
            'condition': product.condition,
            'face_to_face_only': product.face_to_face_only
        },
        'quantity': quantity
    })
