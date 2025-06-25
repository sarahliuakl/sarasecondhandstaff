"""
产品API路由
提供产品的增删改查功能，包括图片上传
"""

from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
from models import db, Product, Category, get_product_by_id, get_products_by_category
from api_auth import require_api_key, require_rate_limit, get_api_success_response, get_api_error_response
from file_upload import upload_image, delete_image, get_image_url
from utils import sanitize_user_input, validate_form_data
import logging
import json

logger = logging.getLogger(__name__)

# 创建产品API蓝图
api_products = Blueprint('api_products', __name__, url_prefix='/api/v1/products')

@api_products.route('', methods=['GET'])
@require_api_key
@require_rate_limit(limit=200)
def get_products():
    """获取产品列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # 最大100个
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        # 构建查询
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category)
        
        if status:
            query = query.filter(Product.stock_status == status)
        
        if available_only:
            query = query.filter(Product.stock_status == 'available')
        
        if search:
            query = query.filter(
                Product.name.contains(search) | 
                Product.description.contains(search)
            )
        
        # 分页查询
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 格式化响应数据
        products_data = []
        for product in products.items:
            product_dict = product.to_dict()
            # 添加分类显示名称
            product_dict['category_display'] = product.get_category_display()
            # 添加库存状态
            product_dict['inventory_status'] = product.get_inventory_status()
            products_data.append(product_dict)
        
        response_data = {
            'products': products_data,
            'pagination': {
                'page': products.page,
                'per_page': products.per_page,
                'total': products.total,
                'pages': products.pages,
                'has_next': products.has_next,
                'has_prev': products.has_prev
            }
        }
        
        return get_api_success_response(response_data)
        
    except Exception as e:
        logger.error(f'获取产品列表失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_products.route('/<int:product_id>', methods=['GET'])
@require_api_key
@require_rate_limit(limit=500)
def get_product(product_id):
    """获取单个产品详情"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        product_dict = product.to_dict()
        # 添加额外信息
        product_dict['category_display'] = product.get_category_display()
        product_dict['inventory_status'] = product.get_inventory_status()
        product_dict['is_low_stock'] = product.is_low_stock() if hasattr(product, 'is_low_stock') else False
        product_dict['is_out_of_stock'] = product.is_out_of_stock() if hasattr(product, 'is_out_of_stock') else False
        
        return get_api_success_response(product_dict)
        
    except Exception as e:
        logger.error(f'获取产品详情失败: {str(e)}')
        return get_api_error_response('QUERY_FAILED', f'查询失败: {str(e)}', 500)

@api_products.route('', methods=['POST'])
@require_api_key
@require_rate_limit(limit=50)
def create_product():
    """创建新产品"""
    try:
        # 获取JSON数据或表单数据
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # 清理用户输入
        clean_data = sanitize_user_input(data)
        
        # 验证必填字段
        required_fields = ['name', 'price', 'category', 'condition']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        if not is_valid:
            return get_api_error_response('VALIDATION_FAILED', ', '.join(errors), 400)
        
        # 验证价格
        try:
            price = float(clean_data['price'])
            if price <= 0:
                return get_api_error_response('INVALID_PRICE', '价格必须大于0', 400)
        except ValueError:
            return get_api_error_response('INVALID_PRICE', '价格格式不正确', 400)
        
        # 验证分类
        if clean_data['category'] not in dict(Product.CATEGORIES):
            return get_api_error_response('INVALID_CATEGORY', '无效的产品分类', 400)
        
        # 验证库存数量
        quantity = 1
        if 'quantity' in clean_data:
            try:
                quantity = int(clean_data['quantity'])
                if quantity < 0:
                    return get_api_error_response('INVALID_QUANTITY', '库存数量不能为负数', 400)
            except ValueError:
                return get_api_error_response('INVALID_QUANTITY', '库存数量格式不正确', 400)
        
        # 验证低库存阈值
        low_stock_threshold = 1
        if 'low_stock_threshold' in clean_data:
            try:
                low_stock_threshold = int(clean_data['low_stock_threshold'])
                if low_stock_threshold < 0:
                    return get_api_error_response('INVALID_THRESHOLD', '低库存阈值不能为负数', 400)
            except ValueError:
                return get_api_error_response('INVALID_THRESHOLD', '低库存阈值格式不正确', 400)
        
        # 创建产品
        product = Product(
            name=clean_data['name'],
            description=clean_data.get('description', ''),
            price=price,
            category=clean_data['category'],
            condition=clean_data['condition'],
            stock_status=clean_data.get('stock_status', 'available'),
            face_to_face_only=clean_data.get('face_to_face_only', '').lower() in ['true', '1', 'yes'],
            quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            track_inventory=clean_data.get('track_inventory', '').lower() in ['true', '1', 'yes']
        )
        
        # 处理图片上传
        uploaded_images = []
        
        # 处理文件上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename != '':
                    success, result, thumbnail = upload_image(file)
                    if success:
                        uploaded_images.append(get_image_url(result))
                        logger.info(f'API图片上传成功: {result}')
                    else:
                        logger.warning(f'API图片上传失败: {result}')
        
        # 处理URL图片
        if 'image_urls' in clean_data:
            if isinstance(clean_data['image_urls'], str):
                try:
                    url_images = json.loads(clean_data['image_urls'])
                except json.JSONDecodeError:
                    url_images = [clean_data['image_urls']]
            else:
                url_images = clean_data['image_urls']
            
            if isinstance(url_images, list):
                valid_url_images = [img.strip() for img in url_images if img.strip()]
                uploaded_images.extend(valid_url_images)
        
        if uploaded_images:
            product.set_images(uploaded_images)
        
        # 处理规格
        if 'specifications' in clean_data:
            if isinstance(clean_data['specifications'], str):
                try:
                    specifications = json.loads(clean_data['specifications'])
                    product.set_specifications(specifications)
                except json.JSONDecodeError:
                    pass
            elif isinstance(clean_data['specifications'], dict):
                product.set_specifications(clean_data['specifications'])
        
        db.session.add(product)
        db.session.commit()
        
        logger.info(f'API产品创建成功: {product.name} (ID: {product.id})')
        
        # 返回创建的产品信息
        product_dict = product.to_dict()
        product_dict['category_display'] = product.get_category_display()
        
        return get_api_success_response(product_dict, '产品创建成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API产品创建失败: {str(e)}')
        return get_api_error_response('CREATE_FAILED', f'创建失败: {str(e)}', 500)

@api_products.route('/<int:product_id>', methods=['PUT'])
@require_api_key
@require_rate_limit(limit=50)
def update_product(product_id):
    """更新产品信息"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        # 获取数据
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        clean_data = sanitize_user_input(data)
        
        # 验证和更新基本字段
        if 'name' in clean_data and clean_data['name']:
            product.name = clean_data['name']
        
        if 'description' in clean_data:
            product.description = clean_data['description']
        
        if 'price' in clean_data:
            try:
                price = float(clean_data['price'])
                if price <= 0:
                    return get_api_error_response('INVALID_PRICE', '价格必须大于0', 400)
                product.price = price
            except ValueError:
                return get_api_error_response('INVALID_PRICE', '价格格式不正确', 400)
        
        if 'category' in clean_data:
            if clean_data['category'] not in dict(Product.CATEGORIES):
                return get_api_error_response('INVALID_CATEGORY', '无效的产品分类', 400)
            product.category = clean_data['category']
        
        if 'condition' in clean_data and clean_data['condition']:
            product.condition = clean_data['condition']
        
        if 'stock_status' in clean_data:
            product.stock_status = clean_data['stock_status']
        
        if 'face_to_face_only' in clean_data:
            product.face_to_face_only = clean_data['face_to_face_only'].lower() in ['true', '1', 'yes']
        
        if 'quantity' in clean_data:
            try:
                quantity = int(clean_data['quantity'])
                if quantity < 0:
                    return get_api_error_response('INVALID_QUANTITY', '库存数量不能为负数', 400)
                product.quantity = quantity
            except ValueError:
                return get_api_error_response('INVALID_QUANTITY', '库存数量格式不正确', 400)
        
        if 'low_stock_threshold' in clean_data:
            try:
                threshold = int(clean_data['low_stock_threshold'])
                if threshold < 0:
                    return get_api_error_response('INVALID_THRESHOLD', '低库存阈值不能为负数', 400)
                product.low_stock_threshold = threshold
            except ValueError:
                return get_api_error_response('INVALID_THRESHOLD', '低库存阈值格式不正确', 400)
        
        if 'track_inventory' in clean_data:
            product.track_inventory = clean_data['track_inventory'].lower() in ['true', '1', 'yes']
        
        # 处理图片更新
        update_images = request.args.get('update_images', 'false').lower() == 'true'
        if update_images:
            uploaded_images = []
            
            # 处理新上传的文件
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and file.filename != '':
                        success, result, thumbnail = upload_image(file)
                        if success:
                            uploaded_images.append(get_image_url(result))
                            logger.info(f'API图片上传成功: {result}')
            
            # 处理URL图片
            if 'image_urls' in clean_data:
                if isinstance(clean_data['image_urls'], str):
                    try:
                        url_images = json.loads(clean_data['image_urls'])
                    except json.JSONDecodeError:
                        url_images = [clean_data['image_urls']]
                else:
                    url_images = clean_data['image_urls']
                
                if isinstance(url_images, list):
                    valid_url_images = [img.strip() for img in url_images if img.strip()]
                    uploaded_images.extend(valid_url_images)
            
            # 是否保留现有图片
            keep_existing = request.args.get('keep_existing_images', 'true').lower() == 'true'
            if keep_existing:
                existing_images = product.get_images()
                all_images = existing_images + uploaded_images
                # 去重
                unique_images = []
                for img in all_images:
                    if img and img not in unique_images:
                        unique_images.append(img)
                product.set_images(unique_images)
            else:
                product.set_images(uploaded_images)
        
        # 处理规格更新
        if 'specifications' in clean_data:
            if isinstance(clean_data['specifications'], str):
                try:
                    specifications = json.loads(clean_data['specifications'])
                    product.set_specifications(specifications)
                except json.JSONDecodeError:
                    pass
            elif isinstance(clean_data['specifications'], dict):
                product.set_specifications(clean_data['specifications'])
        
        db.session.commit()
        
        logger.info(f'API产品更新成功: {product.name} (ID: {product.id})')
        
        # 返回更新后的产品信息
        product_dict = product.to_dict()
        product_dict['category_display'] = product.get_category_display()
        
        return get_api_success_response(product_dict, '产品更新成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API产品更新失败: {str(e)}')
        return get_api_error_response('UPDATE_FAILED', f'更新失败: {str(e)}', 500)

@api_products.route('/<int:product_id>', methods=['DELETE'])
@require_api_key
@require_rate_limit(limit=30)
def delete_product(product_id):
    """删除产品"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        product_name = product.name
        
        # 删除关联的图片文件（如果是本地上传的）
        images = product.get_images()
        for image_url in images:
            if 'uploads/' in image_url:
                # 这是本地上传的图片，尝试删除
                try:
                    # 提取文件名
                    filename = image_url.split('/')[-1]
                    delete_image(filename)
                except Exception as e:
                    logger.warning(f'删除图片文件失败: {image_url} - {str(e)}')
        
        db.session.delete(product)
        db.session.commit()
        
        logger.info(f'API产品删除成功: {product_name} (ID: {product_id})')
        
        return get_api_success_response(None, '产品删除成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API产品删除失败: {str(e)}')
        return get_api_error_response('DELETE_FAILED', f'删除失败: {str(e)}', 500)

@api_products.route('/<int:product_id>/images', methods=['POST'])
@require_api_key
@require_rate_limit(limit=50)
def upload_product_images(product_id):
    """为产品上传图片"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        if 'images' not in request.files:
            return get_api_error_response('NO_FILES', '没有找到图片文件', 400)
        
        files = request.files.getlist('images')
        if not files or all(file.filename == '' for file in files):
            return get_api_error_response('NO_FILES', '没有选择图片文件', 400)
        
        uploaded_images = []
        failed_uploads = []
        
        for file in files:
            if file and file.filename != '':
                success, result, thumbnail = upload_image(file)
                if success:
                    uploaded_images.append(get_image_url(result))
                    logger.info(f'API图片上传成功: {result}')
                else:
                    failed_uploads.append(f'{file.filename}: {result}')
                    logger.warning(f'API图片上传失败: {file.filename} - {result}')
        
        if uploaded_images:
            # 添加到现有图片列表
            existing_images = product.get_images()
            all_images = existing_images + uploaded_images
            
            # 去重
            unique_images = []
            for img in all_images:
                if img and img not in unique_images:
                    unique_images.append(img)
            
            product.set_images(unique_images)
            db.session.commit()
            
            result_data = {
                'uploaded_images': uploaded_images,
                'total_images': len(unique_images)
            }
            
            if failed_uploads:
                result_data['failed_uploads'] = failed_uploads
            
            return get_api_success_response(result_data, f'成功上传 {len(uploaded_images)} 张图片')
        else:
            return get_api_error_response('UPLOAD_FAILED', f'所有图片上传失败: {"; ".join(failed_uploads)}', 500)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API图片上传失败: {str(e)}')
        return get_api_error_response('UPLOAD_FAILED', f'上传失败: {str(e)}', 500)

@api_products.route('/<int:product_id>/inventory', methods=['PATCH'])
@require_api_key
@require_rate_limit(limit=100)
def update_product_inventory(product_id):
    """更新产品库存"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return get_api_error_response('NOT_FOUND', '产品不存在', 404)
        
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        action = data.get('action')
        quantity = data.get('quantity')
        
        if not action or quantity is None:
            return get_api_error_response('MISSING_PARAMS', '缺少action或quantity参数', 400)
        
        try:
            quantity = int(quantity)
        except ValueError:
            return get_api_error_response('INVALID_QUANTITY', '库存数量必须是整数', 400)
        
        old_quantity = product.quantity
        
        if action == 'set':
            # 设置绝对库存数量
            if quantity < 0:
                return get_api_error_response('INVALID_QUANTITY', '库存数量不能为负数', 400)
            product.set_stock_quantity(quantity)
        elif action == 'add':
            # 增加库存
            if quantity <= 0:
                return get_api_error_response('INVALID_QUANTITY', '增加的库存数量必须大于0', 400)
            product.increase_stock(quantity)
        elif action == 'reduce':
            # 减少库存
            if quantity <= 0:
                return get_api_error_response('INVALID_QUANTITY', '减少的库存数量必须大于0', 400)
            if not product.reduce_stock(quantity):
                return get_api_error_response('INSUFFICIENT_STOCK', '库存不足，无法减少指定数量', 400)
        else:
            return get_api_error_response('INVALID_ACTION', '无效的操作类型，支持: set, add, reduce', 400)
        
        db.session.commit()
        
        logger.info(f'API库存更新: {product.name} ({old_quantity} -> {product.quantity})')
        
        # 检查库存状态
        warnings = []
        if hasattr(product, 'is_low_stock') and product.is_low_stock():
            warnings.append(f'库存不足！当前库存: {product.quantity}，警告阈值: {product.low_stock_threshold}')
        
        if hasattr(product, 'is_out_of_stock') and product.is_out_of_stock():
            warnings.append('商品已缺货！')
        
        result_data = {
            'product_id': product.id,
            'old_quantity': old_quantity,
            'new_quantity': product.quantity,
            'stock_status': product.stock_status,
            'inventory_status': product.get_inventory_status(),
            'warnings': warnings
        }
        
        return get_api_success_response(result_data, '库存更新成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'API库存更新失败: {str(e)}')
        return get_api_error_response('UPDATE_FAILED', f'库存更新失败: {str(e)}', 500)