"""
分类API路由
提供分类的增删改查功能
"""

from flask import Blueprint, request, jsonify
from models import db, Category, get_all_categories, get_category_by_id, create_category
from api_auth import require_api_key, require_rate_limit, get_api_success_response, get_api_error_response
from utils import sanitize_user_input, validate_form_data
import logging
import re

logger = logging.getLogger(__name__)

# 创建分类API蓝图
api_categories = Blueprint('api_categories', __name__, url_prefix='/api/v1/categories')

@api_categories.route('', methods=['GET'])
@require_api_key
@require_rate_limit(limit=200)
def get_categories():
    """获取分类列表"""
    try:
        # 获取查询参数
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        include_products = request.args.get('include_products', 'false').lower() == 'true'
        
        # 获取分类列表
        categories = get_all_categories(active_only=active_only)
        
        # 格式化响应数据
        categories_data = []
        for category in categories:
            category_dict = {
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'description': category.description,
                'slug': category.slug,
                'icon': category.icon,
                'sort_order': category.sort_order,
                'is_active': category.is_active,
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat()
            }
            
            # 添加产品数量
            category_dict['product_count'] = category.get_product_count()
            
            # 如果需要包含产品列表
            if include_products:
                products = category.products.filter_by(stock_status='available').all()
                category_dict['products'] = [
                    {
                        'id': p.id,
                        'name': p.name,
                        'price': float(p.price),
                        'condition': p.condition,
                        'stock_status': p.stock_status
                    } for p in products
                ]
            
            categories_data.append(category_dict)
        
        # 按排序权重排序
        categories_data.sort(key=lambda x: x['sort_order'])
        
        return get_api_success_response({
            'categories': categories_data,
            'total': len(categories_data)
        })
        
    except Exception as e:
        logger.error(f'获取分类列表失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_categories.route('/<int:category_id>', methods=['GET'])
@require_api_key
@require_rate_limit(limit=300)
def get_category(category_id):
    """获取单个分类详情"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return get_api_error_response('NOT_FOUND', '分类不存在', 404)
        
        include_products = request.args.get('include_products', 'false').lower() == 'true'
        
        category_dict = {
            'id': category.id,
            'name': category.name,
            'display_name': category.display_name,
            'description': category.description,
            'slug': category.slug,
            'icon': category.icon,
            'sort_order': category.sort_order,
            'is_active': category.is_active,
            'product_count': category.get_product_count(),
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat()
        }
        
        # 如果需要包含产品列表
        if include_products:
            products = category.products.all()
            category_dict['products'] = [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price),
                    'condition': p.condition,
                    'stock_status': p.stock_status,
                    'created_at': p.created_at.isoformat()
                } for p in products
            ]
        
        return get_api_success_response(category_dict)
        
    except Exception as e:
        logger.error(f'获取分类详情失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_categories.route('', methods=['POST'])
@require_api_key
@require_rate_limit(limit=30)
def create_new_category():
    """创建新分类"""
    try:
        # 获取JSON数据
        if not request.is_json:
            return get_api_error_response('INVALID_CONTENT_TYPE', '请求必须是JSON格式', 400)
        
        data = request.get_json()
        if not data:
            return get_api_error_response('MISSING_DATA', '请求数据为空', 400)
        
        # 清理用户输入
        clean_data = sanitize_user_input(data)
        
        # 验证必填字段
        required_fields = ['name', 'display_name']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        if not is_valid:
            return get_api_error_response('VALIDATION_FAILED', ', '.join(errors), 400)
        
        # 验证分类名称唯一性
        existing_name = Category.query.filter(Category.name == clean_data['name']).first()
        if existing_name:
            return get_api_error_response('NAME_EXISTS', '分类名称已存在', 400)
        
        # 自动生成slug如果为空
        slug = clean_data.get('slug', '').strip()
        if not slug:
            slug = re.sub(r'[^a-zA-Z0-9\\-_]', '', clean_data['name'].lower().replace(' ', '-'))
        
        # 验证slug唯一性
        existing_slug = Category.query.filter(Category.slug == slug).first()
        if existing_slug:
            return get_api_error_response('SLUG_EXISTS', 'URL标识(slug)已存在', 400)
        
        # 验证排序值
        sort_order = 0
        if 'sort_order' in clean_data:
            try:
                sort_order = int(clean_data['sort_order'])
            except ValueError:
                return get_api_error_response('INVALID_SORT_ORDER', '排序权重必须是整数', 400)
        
        # 创建分类
        category = Category(
            name=clean_data['name'],
            display_name=clean_data['display_name'],
            description=clean_data.get('description', '').strip() or None,
            slug=slug,
            icon=clean_data.get('icon', '').strip() or None,
            sort_order=sort_order,
            is_active=clean_data.get('is_active', True)
        )
        
        db.session.add(category)
        db.session.commit()
        
        logger.info(f'API分类创建成功: {category.name} (ID: {category.id})')
        
        # 返回创建的分类信息
        category_dict = {
            'id': category.id,
            'name': category.name,
            'display_name': category.display_name,
            'description': category.description,
            'slug': category.slug,
            'icon': category.icon,
            'sort_order': category.sort_order,
            'is_active': category.is_active,
            'product_count': 0,
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat()
        }
        
        return get_api_success_response(category_dict, '分类创建成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API分类创建失败: {str(e)}')
        return get_api_error_response('CREATE_FAILED', f'创建失败: {str(e)}', 500)

@api_categories.route('/<int:category_id>', methods=['PUT'])
@require_api_key
@require_rate_limit(limit=50)
def update_category(category_id):
    """更新分类信息"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return get_api_error_response('NOT_FOUND', '分类不存在', 404)
        
        # 获取JSON数据
        if not request.is_json:
            return get_api_error_response('INVALID_CONTENT_TYPE', '请求必须是JSON格式', 400)
        
        data = request.get_json()
        if not data:
            return get_api_error_response('MISSING_DATA', '请求数据为空', 400)
        
        clean_data = sanitize_user_input(data)
        
        # 验证和更新字段
        if 'name' in clean_data and clean_data['name']:
            # 验证名称唯一性（排除当前分类）
            existing_name = Category.query.filter(
                Category.name == clean_data['name'],
                Category.id != category_id
            ).first()
            if existing_name:
                return get_api_error_response('NAME_EXISTS', '分类名称已存在', 400)
            category.name = clean_data['name']
        
        if 'display_name' in clean_data and clean_data['display_name']:
            category.display_name = clean_data['display_name']
        
        if 'description' in clean_data:
            category.description = clean_data['description'].strip() or None
        
        if 'slug' in clean_data:
            slug = clean_data['slug'].strip()
            if slug:
                # 验证slug唯一性（排除当前分类）
                existing_slug = Category.query.filter(
                    Category.slug == slug,
                    Category.id != category_id
                ).first()
                if existing_slug:
                    return get_api_error_response('SLUG_EXISTS', 'URL标识(slug)已存在', 400)
                category.slug = slug
        
        if 'icon' in clean_data:
            category.icon = clean_data['icon'].strip() or None
        
        if 'sort_order' in clean_data:
            try:
                sort_order = int(clean_data['sort_order'])
                category.sort_order = sort_order
            except ValueError:
                return get_api_error_response('INVALID_SORT_ORDER', '排序权重必须是整数', 400)
        
        if 'is_active' in clean_data:
            category.is_active = bool(clean_data['is_active'])
        
        db.session.commit()
        
        logger.info(f'API分类更新成功: {category.name} (ID: {category.id})')
        
        # 返回更新后的分类信息
        category_dict = {
            'id': category.id,
            'name': category.name,
            'display_name': category.display_name,
            'description': category.description,
            'slug': category.slug,
            'icon': category.icon,
            'sort_order': category.sort_order,
            'is_active': category.is_active,
            'product_count': category.get_product_count(),
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat()
        }
        
        return get_api_success_response(category_dict, '分类更新成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API分类更新失败: {str(e)}')
        return get_api_error_response('UPDATE_FAILED', f'更新失败: {str(e)}', 500)

@api_categories.route('/<int:category_id>', methods=['DELETE'])
@require_api_key
@require_rate_limit(limit=20)
def delete_category(category_id):
    """删除分类"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return get_api_error_response('NOT_FOUND', '分类不存在', 404)
        
        # 检查是否有产品使用此分类
        product_count = category.products.count()
        if product_count > 0:
            return get_api_error_response(
                'CATEGORY_IN_USE',
                f'无法删除：还有 {product_count} 个产品使用此分类',
                400
            )
        
        category_name = category.name
        
        db.session.delete(category)
        db.session.commit()
        
        logger.info(f'API分类删除成功: {category_name} (ID: {category_id})')
        
        return get_api_success_response(None, '分类删除成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API分类删除失败: {str(e)}')
        return get_api_error_response('DELETE_FAILED', f'删除失败: {str(e)}', 500)

@api_categories.route('/<int:category_id>/toggle', methods=['PATCH'])
@require_api_key
@require_rate_limit(limit=100)
def toggle_category_status(category_id):
    """切换分类激活状态"""
    try:
        category = get_category_by_id(category_id)
        if not category:
            return get_api_error_response('NOT_FOUND', '分类不存在', 404)
        
        # 切换状态
        old_status = category.is_active
        category.is_active = not category.is_active
        db.session.commit()
        
        status_text = '激活' if category.is_active else '禁用'
        logger.info(f'API分类状态切换: {category.name} ({old_status} -> {category.is_active})')
        
        result_data = {
            'id': category.id,
            'name': category.name,
            'is_active': category.is_active,
            'status_text': status_text
        }
        
        return get_api_success_response(result_data, f'分类已{status_text}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API分类状态切换失败: {str(e)}')
        return get_api_error_response('UPDATE_FAILED', f'操作失败: {str(e)}', 500)

@api_categories.route('/batch', methods=['POST'])
@require_api_key
@require_rate_limit(limit=10)
def batch_create_categories():
    """批量创建分类"""
    try:
        # 获取JSON数据
        if not request.is_json:
            return get_api_error_response('INVALID_CONTENT_TYPE', '请求必须是JSON格式', 400)
        
        data = request.get_json()
        if not data or 'categories' not in data:
            return get_api_error_response('MISSING_DATA', '请求数据为空或缺少categories字段', 400)
        
        categories_data = data['categories']
        if not isinstance(categories_data, list):
            return get_api_error_response('INVALID_DATA', 'categories必须是数组', 400)
        
        if len(categories_data) > 50:  # 限制批量操作数量
            return get_api_error_response('TOO_MANY_ITEMS', '一次最多创建50个分类', 400)
        
        created_categories = []
        failed_categories = []
        
        for i, cat_data in enumerate(categories_data):
            try:
                clean_data = sanitize_user_input(cat_data)
                
                # 验证必填字段
                if not clean_data.get('name') or not clean_data.get('display_name'):
                    failed_categories.append({
                        'index': i,
                        'data': cat_data,
                        'error': '缺少必填字段name或display_name'
                    })
                    continue
                
                # 检查名称重复
                existing_name = Category.query.filter(Category.name == clean_data['name']).first()
                if existing_name:
                    failed_categories.append({
                        'index': i,
                        'data': cat_data,
                        'error': f'分类名称已存在: {clean_data["name"]}'
                    })
                    continue
                
                # 生成slug
                slug = clean_data.get('slug', '').strip()
                if not slug:
                    slug = re.sub(r'[^a-zA-Z0-9\\-_]', '', clean_data['name'].lower().replace(' ', '-'))
                
                # 检查slug重复
                existing_slug = Category.query.filter(Category.slug == slug).first()
                if existing_slug:
                    failed_categories.append({
                        'index': i,
                        'data': cat_data,
                        'error': f'URL标识已存在: {slug}'
                    })
                    continue
                
                # 创建分类
                category = Category(
                    name=clean_data['name'],
                    display_name=clean_data['display_name'],
                    description=clean_data.get('description', '').strip() or None,
                    slug=slug,
                    icon=clean_data.get('icon', '').strip() or None,
                    sort_order=int(clean_data.get('sort_order', 0)),
                    is_active=clean_data.get('is_active', True)
                )
                
                db.session.add(category)
                db.session.flush()  # 获取ID但不提交
                
                created_categories.append({
                    'id': category.id,
                    'name': category.name,
                    'display_name': category.display_name,
                    'slug': category.slug
                })
                
            except Exception as e:
                failed_categories.append({
                    'index': i,
                    'data': cat_data,
                    'error': str(e)
                })
        
        if created_categories:
            db.session.commit()
            logger.info(f'API批量创建分类成功: {len(created_categories)} 个')
        else:
            db.session.rollback()
        
        result_data = {
            'created': created_categories,
            'failed': failed_categories,
            'created_count': len(created_categories),
            'failed_count': len(failed_categories)
        }
        
        if failed_categories:
            return get_api_success_response(result_data, f'部分成功：创建 {len(created_categories)} 个，失败 {len(failed_categories)} 个')
        else:
            return get_api_success_response(result_data, f'批量创建成功：{len(created_categories)} 个分类')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API批量创建分类失败: {str(e)}')
        return get_api_error_response('BATCH_CREATE_FAILED', f'批量创建失败: {str(e)}', 500)

@api_categories.route('/search', methods=['GET'])
@require_api_key
@require_rate_limit(limit=200)
def search_categories():
    """搜索分类"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return get_api_error_response('MISSING_QUERY', '缺少搜索关键词', 400)
        
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # 构建查询
        search_query = Category.query.filter(
            Category.name.contains(query) |
            Category.display_name.contains(query) |
            Category.description.contains(query)
        )
        
        if active_only:
            search_query = search_query.filter(Category.is_active == True)
        
        categories = search_query.order_by(Category.sort_order).all()
        
        # 格式化响应数据
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'description': category.description,
                'slug': category.slug,
                'icon': category.icon,
                'is_active': category.is_active,
                'product_count': category.get_product_count()
            })
        
        return get_api_success_response({
            'categories': categories_data,
            'total': len(categories_data),
            'query': query
        })
        
    except Exception as e:
        logger.error(f'搜索分类失败: {str(e)}')
        return get_api_error_response('SEARCH_FAILED', f'搜索失败: {str(e)}', 500)