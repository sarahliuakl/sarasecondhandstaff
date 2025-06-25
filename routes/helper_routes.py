"""
辅助路由模块
包含搜索、购物车API、SEO等辅助功能
"""

from flask import Blueprint, request, jsonify, Response
from flask_wtf.csrf import csrf
from models import db, Product, get_products_by_category, get_product_by_id
import logging

logger = logging.getLogger(__name__)

# 创建辅助路由蓝图
helper_bp = Blueprint('helper', __name__)

@helper_bp.route("/api/cart", methods=['POST'])
@csrf.exempt
def add_to_cart():
    """添加商品到购物车（API接口）"""
    # 对于JSON API，暂时跳过CSRF检查
    # 在生产环境中应该使用其他方式验证，如JWT token
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = get_product_by_id(product_id)
    if not product or not product.is_available():
        return jsonify({'success': False, 'message': '商品不存在或已售出'})
    
    # 这里返回商品信息，前端用localStorage管理购物车
    return jsonify({
        'success': True, 
        'product': {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.get_images()[0] if product.get_images() else '',
            'condition': product.condition,
            'face_to_face_only': product.face_to_face_only
        },
        'quantity': quantity
    })

@helper_bp.route("/api/search/suggestions")
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # 获取产品名称和分类的建议
    suggestions = []
    
    # 搜索产品名称
    products = Product.query.filter(
        db.func.lower(Product.name).contains(query.lower())
    ).filter(
        Product.stock_status == Product.STATUS_AVAILABLE
    ).limit(5).all()
    
    for product in products:
        suggestions.append({
            'text': product.name,
            'type': 'product',
            'category': product.category
        })
    
    # 添加分类建议
    categories = Product.CATEGORIES
    for category_code, category_name in categories:
        if query.lower() in category_name.lower() or query.lower() in category_code.lower():
            suggestions.append({
                'text': category_name,
                'type': 'category'
            })
    
    return jsonify(suggestions[:8])  # 限制最多8个建议

@helper_bp.route("/sitemap.xml")
def sitemap():
    """生成XML格式的网站地图"""
    try:
        # 获取所有可用产品
        products = get_products_by_category(available_only=True)
        
        # 构建sitemap XML
        sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
'''
        
        # 添加主要页面
        base_url = request.url_root.rstrip('/')
        main_pages = [
            ('', '1.0', 'daily'),  # 首页
            ('/products', '0.9', 'daily'),  # 产品列表
            ('/contact', '0.8', 'monthly'),  # 联系页面
            ('/about', '0.7', 'monthly'),  # 关于页面
            ('/help', '0.6', 'monthly'),  # 帮助页面
        ]
        
        for page, priority, changefreq in main_pages:
            sitemap_xml += f'''  <url>
    <loc>{base_url}{page}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
'''
        
        # 添加分类页面
        categories = Product.CATEGORIES
        for category_code, category_name in categories:
            sitemap_xml += f'''  <url>
    <loc>{base_url}/products?category={category_code}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
'''
        
        # 添加产品详情页
        for product in products:
            sitemap_xml += f'''  <url>
    <loc>{base_url}/product/{product.id}</loc>
    <lastmod>{product.updated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
'''
        
        sitemap_xml += '</urlset>'
        
        return Response(sitemap_xml, mimetype='application/xml')
        
    except Exception as e:
        logger.error(f'生成sitemap失败: {str(e)}')
        return Response('', status=500)

@helper_bp.route("/robots.txt")
def robots_txt():
    """生成robots.txt文件"""
    robots_content = f"""User-agent: *
Allow: /
Allow: /products
Allow: /product/*
Allow: /contact
Allow: /about
Allow: /help

Disallow: /admin/*
Disallow: /api/*
Disallow: /order/*
Disallow: /cart

Sitemap: {request.url_root}sitemap.xml
"""
    return Response(robots_content, mimetype='text/plain')