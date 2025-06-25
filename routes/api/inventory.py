"""
库存API路由
提供库存查询和管理功能
"""

from flask import Blueprint, request, jsonify
from models import db, Product, Category, get_inventory_stats, get_low_stock_products, get_out_of_stock_products
from api_auth import require_api_key, require_rate_limit, get_api_success_response, get_api_error_response
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建库存API蓝图
api_inventory = Blueprint('api_inventory', __name__, url_prefix='/api/v1/inventory')

@api_inventory.route('/stats', methods=['GET'])
@require_api_key
@require_rate_limit(limit=100)
def get_inventory_statistics():
    """获取库存统计信息"""
    try:
        # 获取基础库存统计
        stats = get_inventory_stats()
        
        # 获取分类库存统计
        category_stats = []
        categories = Category.query.filter(Category.is_active == True).all()
        
        for category in categories:
            products = category.products.all()
            total_products = len(products)
            available_products = len([p for p in products if p.stock_status == 'available'])
            total_quantity = sum(p.quantity for p in products if p.track_inventory)
            low_stock_count = len([p for p in products if hasattr(p, 'is_low_stock') and p.is_low_stock()])
            out_of_stock_count = len([p for p in products if hasattr(p, 'is_out_of_stock') and p.is_out_of_stock()])
            
            category_stats.append({
                'category_id': category.id,
                'category_name': category.name,
                'category_display_name': category.display_name,
                'total_products': total_products,
                'available_products': available_products,
                'total_quantity': total_quantity,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count
            })
        
        # 获取库存趋势（过去7天）
        trend_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            # 这里可以添加更复杂的趋势分析
            # 暂时返回基础数据
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'available_products': stats.get('available_products', 0),
                'total_quantity': stats.get('total_quantity', 0)
            })
        
        result_data = {
            'overview': stats,
            'by_category': category_stats,
            'trend': trend_data,
            'generated_at': datetime.now().isoformat()
        }
        
        return get_api_success_response(result_data)
        
    except Exception as e:
        logger.error(f'获取库存统计失败: {str(e)}')
        return get_api_error_response('STATS_FAILED', f'统计失败: {str(e)}', 500)

@api_inventory.route('/low-stock', methods=['GET'])
@require_api_key
@require_rate_limit(limit=100)
def get_low_stock_items():
    """获取低库存商品列表"""
    try:
        # 获取参数
        limit = min(request.args.get('limit', 50, type=int), 200)  # 最大200个
        category = request.args.get('category')
        
        # 获取低库存产品
        low_stock_products = get_low_stock_products()
        
        # 按分类筛选
        if category:
            low_stock_products = [p for p in low_stock_products if p.category == category]
        
        # 限制数量
        if limit:
            low_stock_products = low_stock_products[:limit]
        
        # 格式化响应数据
        products_data = []
        for product in low_stock_products:
            product_dict = {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'category_display': product.get_category_display(),
                'current_quantity': product.quantity,
                'low_stock_threshold': product.low_stock_threshold,
                'stock_status': product.stock_status,
                'track_inventory': product.track_inventory,
                'price': float(product.price),
                'condition': product.condition,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            }
            
            # 计算缺口
            if hasattr(product, 'low_stock_threshold'):
                shortage = product.low_stock_threshold - product.quantity
                product_dict['shortage'] = max(shortage, 0)
            
            products_data.append(product_dict)
        
        # 按缺口排序（缺口最大的在前）
        products_data.sort(key=lambda x: x.get('shortage', 0), reverse=True)
        
        result_data = {
            'low_stock_products': products_data,
            'total_count': len(products_data),
            'filter': {
                'category': category,
                'limit': limit
            }
        }
        
        return get_api_success_response(result_data)
        
    except Exception as e:
        logger.error(f'获取低库存商品失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_inventory.route('/out-of-stock', methods=['GET'])
@require_api_key
@require_rate_limit(limit=100)
def get_out_of_stock_items():
    """获取缺货商品列表"""
    try:
        # 获取参数
        limit = min(request.args.get('limit', 50, type=int), 200)
        category = request.args.get('category')
        
        # 获取缺货产品
        out_of_stock_products = get_out_of_stock_products()
        
        # 按分类筛选
        if category:
            out_of_stock_products = [p for p in out_of_stock_products if p.category == category]
        
        # 限制数量
        if limit:
            out_of_stock_products = out_of_stock_products[:limit]
        
        # 格式化响应数据
        products_data = []
        for product in out_of_stock_products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'category_display': product.get_category_display(),
                'current_quantity': product.quantity,
                'stock_status': product.stock_status,
                'track_inventory': product.track_inventory,
                'price': float(product.price),
                'condition': product.condition,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
                'days_out_of_stock': (datetime.now() - product.updated_at).days
            })
        
        # 按缺货天数排序（缺货时间最长的在前）
        products_data.sort(key=lambda x: x.get('days_out_of_stock', 0), reverse=True)
        
        result_data = {
            'out_of_stock_products': products_data,
            'total_count': len(products_data),
            'filter': {
                'category': category,
                'limit': limit
            }
        }
        
        return get_api_success_response(result_data)
        
    except Exception as e:
        logger.error(f'获取缺货商品失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_inventory.route('/check/<int:product_id>', methods=['GET'])
@require_api_key
@require_rate_limit(limit=500)
def check_product_inventory(product_id):
    """检查单个产品库存状态"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        # 获取库存状态
        inventory_data = {
            'product_id': product.id,
            'product_name': product.name,
            'category': product.category,
            'category_display': product.get_category_display(),
            'current_quantity': product.quantity,
            'low_stock_threshold': getattr(product, 'low_stock_threshold', 1),
            'stock_status': product.stock_status,
            'track_inventory': getattr(product, 'track_inventory', True),
            'inventory_status': product.get_inventory_status() if hasattr(product, 'get_inventory_status') else 'unknown',
            'is_available': product.stock_status == 'available',
            'is_low_stock': product.is_low_stock() if hasattr(product, 'is_low_stock') else False,
            'is_out_of_stock': product.is_out_of_stock() if hasattr(product, 'is_out_of_stock') else False,
            'face_to_face_only': getattr(product, 'face_to_face_only', False),
            'price': float(product.price),
            'condition': product.condition,
            'updated_at': product.updated_at.isoformat()
        }
        
        # 添加警告信息
        warnings = []
        if inventory_data['is_out_of_stock']:
            warnings.append('商品已缺货')
        elif inventory_data['is_low_stock']:
            shortage = inventory_data['low_stock_threshold'] - inventory_data['current_quantity']
            warnings.append(f'库存不足，低于警告阈值 {shortage} 个')
        
        inventory_data['warnings'] = warnings
        
        return get_api_success_response(inventory_data)
        
    except Exception as e:
        logger.error(f'检查产品库存失败: {str(e)}')
        return get_api_error_response('CHECK_FAILED', f'检查失败: {str(e)}', 500)

@api_inventory.route('/bulk-check', methods=['POST'])
@require_api_key
@require_rate_limit(limit=50)
def bulk_check_inventory():
    """批量检查产品库存状态"""
    try:
        # 获取JSON数据
        if not request.is_json:
            return get_api_error_response('INVALID_CONTENT_TYPE', '请求必须是JSON格式', 400)
        
        data = request.get_json()
        if not data or 'product_ids' not in data:
            return get_api_error_response('MISSING_DATA', '请求数据为空或缺少product_ids字段', 400)
        
        product_ids = data['product_ids']
        if not isinstance(product_ids, list):
            return get_api_error_response('INVALID_DATA', 'product_ids必须是数组', 400)
        
        if len(product_ids) > 100:  # 限制批量操作数量
            return get_api_error_response('TOO_MANY_ITEMS', '一次最多检查100个产品', 400)
        
        # 查询产品
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        found_ids = {p.id for p in products}
        missing_ids = [pid for pid in product_ids if pid not in found_ids]
        
        # 检查库存状态
        inventory_data = []
        for product in products:
            product_data = {
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'current_quantity': product.quantity,
                'stock_status': product.stock_status,
                'is_available': product.stock_status == 'available',
                'is_low_stock': product.is_low_stock() if hasattr(product, 'is_low_stock') else False,
                'is_out_of_stock': product.is_out_of_stock() if hasattr(product, 'is_out_of_stock') else False,
                'inventory_status': product.get_inventory_status() if hasattr(product, 'get_inventory_status') else 'unknown'
            }
            inventory_data.append(product_data)
        
        result_data = {
            'inventory_status': inventory_data,
            'found_count': len(products),
            'missing_ids': missing_ids,
            'missing_count': len(missing_ids)
        }
        
        return get_api_success_response(result_data)
        
    except Exception as e:
        logger.error(f'批量检查库存失败: {str(e)}')
        return get_api_error_response('BULK_CHECK_FAILED', f'批量检查失败: {str(e)}', 500)

@api_inventory.route('/alerts', methods=['GET'])
@require_api_key
@require_rate_limit(limit=100)
def get_inventory_alerts():
    """获取库存警报信息"""
    try:
        # 获取所有需要关注的库存问题
        alerts = []
        
        # 低库存警报
        low_stock_products = get_low_stock_products()[:10]  # 只取前10个
        for product in low_stock_products:
            alerts.append({
                'type': 'low_stock',
                'severity': 'warning',
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'current_quantity': product.quantity,
                'threshold': getattr(product, 'low_stock_threshold', 1),
                'message': f'库存不足：{product.name} (当前库存: {product.quantity})',
                'created_at': product.updated_at.isoformat()
            })
        
        # 缺货警报
        out_of_stock_products = get_out_of_stock_products()[:10]
        for product in out_of_stock_products:
            alerts.append({
                'type': 'out_of_stock',
                'severity': 'critical',
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'current_quantity': product.quantity,
                'message': f'商品缺货：{product.name}',
                'created_at': product.updated_at.isoformat()
            })
        
        # 按严重程度排序（critical > warning）
        alerts.sort(key=lambda x: {'critical': 0, 'warning': 1}.get(x['severity'], 2))
        
        # 统计信息
        summary = {
            'total_alerts': len(alerts),
            'critical_count': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_count': len([a for a in alerts if a['severity'] == 'warning']),
            'categories_affected': len(set(a['category'] for a in alerts))
        }
        
        result_data = {
            'alerts': alerts,
            'summary': summary,
            'generated_at': datetime.now().isoformat()
        }
        
        return get_api_success_response(result_data)
        
    except Exception as e:
        logger.error(f'获取库存警报失败: {str(e)}')
        return get_api_error_response('ALERTS_FAILED', f'获取警报失败: {str(e)}', 500)

@api_inventory.route('/report', methods=['GET'])
@require_api_key
@require_rate_limit(limit=20)
def generate_inventory_report():
    """生成详细的库存报告"""
    try:
        # 获取参数
        format_type = request.args.get('format', 'summary')  # summary, detailed
        category = request.args.get('category')
        include_images = request.args.get('include_images', 'false').lower() == 'true'
        
        # 构建查询
        query = Product.query
        if category:
            query = query.filter(Product.category == category)
        
        products = query.order_by(Product.category, Product.name).all()
        
        # 生成报告数据
        report_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'format': format_type,
                'category_filter': category,
                'total_products': len(products)
            },
            'summary': {
                'total_products': len(products),
                'available_products': len([p for p in products if p.stock_status == 'available']),
                'sold_products': len([p for p in products if p.stock_status == 'sold']),
                'reserved_products': len([p for p in products if p.stock_status == 'reserved']),
                'total_value': sum(float(p.price) for p in products if p.stock_status == 'available'),
                'low_stock_count': len([p for p in products if hasattr(p, 'is_low_stock') and p.is_low_stock()]),
                'out_of_stock_count': len([p for p in products if hasattr(p, 'is_out_of_stock') and p.is_out_of_stock()])
            }
        }
        
        if format_type == 'detailed':
            # 详细报告包含每个产品的信息
            products_data = []
            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'category': product.category,
                    'category_display': product.get_category_display(),
                    'price': float(product.price),
                    'condition': product.condition,
                    'stock_status': product.stock_status,
                    'quantity': product.quantity,
                    'low_stock_threshold': getattr(product, 'low_stock_threshold', 1),
                    'track_inventory': getattr(product, 'track_inventory', True),
                    'face_to_face_only': getattr(product, 'face_to_face_only', False),
                    'is_low_stock': product.is_low_stock() if hasattr(product, 'is_low_stock') else False,
                    'is_out_of_stock': product.is_out_of_stock() if hasattr(product, 'is_out_of_stock') else False,
                    'created_at': product.created_at.isoformat(),
                    'updated_at': product.updated_at.isoformat()
                }
                
                if include_images:
                    product_data['images'] = product.get_images()
                
                products_data.append(product_data)
            
            report_data['products'] = products_data
        
        # 按分类统计
        category_stats = {}
        for product in products:
            category = product.category
            if category not in category_stats:
                category_stats[category] = {
                    'category': category,
                    'category_display': product.get_category_display(),
                    'total_products': 0,
                    'available_products': 0,
                    'total_value': 0,
                    'low_stock_count': 0,
                    'out_of_stock_count': 0
                }
            
            stats = category_stats[category]
            stats['total_products'] += 1
            
            if product.stock_status == 'available':
                stats['available_products'] += 1
                stats['total_value'] += float(product.price)
            
            if hasattr(product, 'is_low_stock') and product.is_low_stock():
                stats['low_stock_count'] += 1
            
            if hasattr(product, 'is_out_of_stock') and product.is_out_of_stock():
                stats['out_of_stock_count'] += 1
        
        report_data['by_category'] = list(category_stats.values())
        
        return get_api_success_response(report_data)
        
    except Exception as e:
        logger.error(f'生成库存报告失败: {str(e)}')
        return get_api_error_response('REPORT_FAILED', f'生成报告失败: {str(e)}', 500)