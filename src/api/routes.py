from flask import jsonify, request
from . import api
from ..models import Product, Category, get_all_categories, get_product_by_id, get_products_by_category

@api.route('/')
def index():
    return jsonify({'message': 'Welcome to the Sara Second Hand Shop API'})

@api.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = get_product_by_id(product_id)
    if product:
        return jsonify(product.to_dict())
    return jsonify({'error': 'Product not found'}), 404

@api.route('/categories', methods=['GET'])
def get_categories():
    categories = get_all_categories()
    return jsonify([category.to_dict() for category in categories])

@api.route('/categories/<int:category_id>/products', methods=['GET'])
def get_products_in_category(category_id):
    products = get_products_by_category(category_id)
    return jsonify([product.to_dict() for product in products])
