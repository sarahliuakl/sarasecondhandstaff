from flask import render_template, request, redirect, url_for, flash, jsonify
from . import main
from ..models import Product, Order, Message

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/cart')
def cart():
    return render_template('cart.html')

@main.route('/order/confirm', methods=['GET', 'POST'])
def order_confirm():
    return render_template('order_confirm.html')

@main.route('/order/success')
def order_success():
    return render_template('order_success.html')

@main.route('/order/query', methods=['GET', 'POST'])
def order_query():
    return render_template('order_query.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@main.route('/help')
def help():
    return render_template('help.html')
