"""
Sara二手售卖网站 - 测试数据生成脚本
创建完整的测试数据，包括所有表的数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src import create_app
from src.models import (
    db, Category, Product, Order, Message, Admin, SiteSettings,
    init_default_categories
)
from datetime import datetime, timedelta
import json
import random

def clear_all_data():
    """清空所有测试数据（保留表结构）"""
    print("清空现有数据...")
    
    # 按照外键依赖关系的顺序删除数据
    Order.query.delete()
    Message.query.delete()
    Product.query.delete()
    Category.query.delete()
    Admin.query.delete()
    SiteSettings.query.delete()
    
    db.session.commit()
    print("✓ 已清空所有数据")

def add_categories():
    """添加分类数据"""
    print("添加分类数据...")
    
    categories_data = [
        {
            'name': 'electronics',
            'display_name': '电子产品',
            'description': '包括电脑、手机、相机、游戏设备等各类电子产品',
            'slug': 'electronics',
            'icon': 'fas fa-laptop',
            'sort_order': 1
        },
        {
            'name': 'clothing',
            'display_name': '衣物',
            'description': '各种服装、鞋帽、配饰等时尚用品',
            'slug': 'clothing',
            'icon': 'fas fa-tshirt',
            'sort_order': 2
        },
        {
            'name': 'anime',
            'display_name': '动漫周边',
            'description': '动漫相关商品、手办、cosplay用品、周边产品',
            'slug': 'anime',
            'icon': 'fas fa-star',
            'sort_order': 3
        },
        {
            'name': 'appliances',
            'display_name': '家电用品',
            'description': '生活家电、厨房用品、小家电等',
            'slug': 'appliances',
            'icon': 'fas fa-blender',
            'sort_order': 4
        },
        {
            'name': 'books',
            'display_name': '图书文具',
            'description': '各类图书、文具用品、学习资料',
            'slug': 'books',
            'icon': 'fas fa-book',
            'sort_order': 5
        },
        {
            'name': 'other',
            'display_name': '其他',
            'description': '其他未分类商品',
            'slug': 'other',
            'icon': 'fas fa-cube',
            'sort_order': 6
        }
    ]
    
    for cat_data in categories_data:
        category = Category(**cat_data)
        db.session.add(category)
    
    db.session.commit()
    print(f"✓ 已添加 {len(categories_data)} 个分类")

def add_admins():
    """添加管理员数据"""
    print("添加管理员数据...")
    
    admins_data = [
        {
            'username': 'admin',
            'email': 'admin@sara.com',
            'password': 'admin123',
            'is_super_admin': True
        },
        {
            'username': 'sara',
            'email': 'sara@sara.com',
            'password': 'sara123',
            'is_super_admin': False
        },
        {
            'username': 'manager',
            'email': 'manager@sara.com',
            'password': 'manager123',
            'is_super_admin': False
        }
    ]
    
    for admin_data in admins_data:
        admin = Admin(
            username=admin_data['username'],
            email=admin_data['email'],
            is_super_admin=admin_data['is_super_admin']
        )
        admin.set_password(admin_data['password'])
        
        # 设置一些管理员有登录记录
        if admin_data['username'] != 'manager':
            admin.last_login = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        
        db.session.add(admin)
    
    db.session.commit()
    print(f"✓ 已添加 {len(admins_data)} 个管理员账户")

def add_site_settings():
    """添加网站设置数据"""
    print("添加网站设置数据...")
    
    settings_data = [
        {
            'key': 'site_name',
            'value': 'Sara二手商店',
            'description': '网站名称'
        },
        {
            'key': 'site_description',
            'value': '新西兰奥克兰专业二手商品交易平台，品质保证，价格实惠',
            'description': '网站描述'
        },
        {
            'key': 'contact_email',
            'value': 'sara@sara.com',
            'description': '联系邮箱'
        },
        {
            'key': 'contact_phone',
            'value': '0225255862',
            'description': '联系电话'
        },
        {
            'key': 'contact_wechat',
            'value': 'sara_nz_2025',
            'description': '微信号'
        },
        {
            'key': 'shipping_fee',
            'value': '15.00',
            'description': '默认邮费(纽币)'
        },
        {
            'key': 'free_shipping_threshold',
            'value': '200.00',
            'description': '免邮费门槛(纽币)'
        },
        {
            'key': 'store_address',
            'value': '奥克兰市中心',
            'description': '店铺地址'
        },
        {
            'key': 'business_hours',
            'value': '周一至周日 9:00-18:00',
            'description': '营业时间'
        },
        {
            'key': 'about_us',
            'value': 'Sara二手商店致力于为奥克兰华人社区提供优质的二手商品交易服务。我们严格把控商品质量，确保每一件商品都物有所值。',
            'description': '关于我们'
        }
    ]
    
    for setting_data in settings_data:
        setting = SiteSettings(**setting_data)
        db.session.add(setting)
    
    db.session.commit()
    print(f"✓ 已添加 {len(settings_data)} 个网站设置")

def add_products():
    """添加产品数据"""
    print("添加产品数据...")
    
    # 获取分类ID
    electronics_cat = Category.query.filter_by(name='electronics').first()
    clothing_cat = Category.query.filter_by(name='clothing').first()
    anime_cat = Category.query.filter_by(name='anime').first()
    appliances_cat = Category.query.filter_by(name='appliances').first()
    books_cat = Category.query.filter_by(name='books').first()
    other_cat = Category.query.filter_by(name='other').first()
    
    products_data = [
        # 电子产品
        {
            'name': 'MacBook Air M2 13寸',
            'description': '苹果MacBook Air，M2芯片，13寸视网膜显示屏，256GB存储，使用6个月，成色极佳，原装充电器和包装盒齐全。适合学生和办公使用，性能出色，续航时间长。',
            'price': 1450.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '9成新',
            'face_to_face_only': True,
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Apple',
                'model': 'MacBook Air M2',
                'cpu': 'Apple M2',
                'ram': '8GB',
                'storage': '256GB SSD',
                'screen': '13.6英寸',
                'color': '星光色'
            }
        },
        {
            'name': 'iPhone 14 128GB',
            'description': 'iPhone 14，128GB存储，紫色，购买8个月，一直使用保护壳和钢化膜，外观如新。电池健康度98%，功能完好，随机配送原装充电线。',
            'price': 950.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '9.5成新',
            'face_to_face_only': True,
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Apple',
                'model': 'iPhone 14',
                'storage': '128GB',
                'color': '紫色',
                'battery_health': '98%',
                'network': '5G'
            }
        },
        {
            'name': 'Dell XPS 15 笔记本电脑',
            'description': 'Dell XPS 15，Intel i7处理器，16GB内存，512GB SSD，GTX 1650显卡，15.6英寸4K触摸屏。购买1年，主要用于编程和设计工作，性能强劲。',
            'price': 1200.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '8.5成新',
            'face_to_face_only': True,
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Dell',
                'model': 'XPS 15',
                'cpu': 'Intel i7-11800H',
                'ram': '16GB DDR4',
                'storage': '512GB SSD',
                'gpu': 'GTX 1650',
                'screen': '15.6英寸 4K触摸屏'
            }
        },
        {
            'name': 'Nintendo Switch OLED',
            'description': 'Nintendo Switch OLED版本，白色，购买半年，包含原装底座、Pro手柄、多款游戏卡带。屏幕无划痕，功能完好，是游戏爱好者的理想选择。',
            'price': 380.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '9成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Nintendo',
                'model': 'Switch OLED',
                'color': '白色',
                'screen': '7英寸OLED',
                'include': '底座+Pro手柄+游戏卡带'
            }
        },
        {
            'name': 'Canon EOS M50 微单相机',
            'description': 'Canon EOS M50 微单相机，2400万像素，4K视频录制，翻转触摸屏，包含15-45mm套机镜头。购买2年，使用频率不高，功能完好。',
            'price': 520.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '8.5成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Canon',
                'model': 'EOS M50',
                'sensor': '2400万像素APS-C',
                'video': '4K 24fps',
                'lens': '15-45mm套机镜头',
                'features': '翻转触摸屏、Wi-Fi'
            }
        },
        
        # 服装类
        {
            'name': 'Uniqlo羽绒服 女款M码',
            'description': 'Uniqlo优质羽绒服，女款M码，深蓝色，90%白鸭绒填充，轻便保暖，适合新西兰冬季。购买一年，穿着次数不多，洗涤保养良好。',
            'price': 89.00,
            'category': 'clothing',
            'category_id': clothing_cat.id,
            'condition': '9成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Uniqlo',
                'size': 'M码',
                'color': '深蓝色',
                'material': '90%白鸭绒',
                'suitable_for': '身高160-170cm'
            }
        },
        {
            'name': 'Levi\'s 511牛仔裤 男款',
            'description': 'Levi\'s经典511修身牛仔裤，男款W32L32，深蓝色，面料柔软舒适，版型修身但不紧绷。购买半年，穿着3-4次，几乎全新。',
            'price': 75.00,
            'category': 'clothing',
            'category_id': clothing_cat.id,
            'condition': '9.5成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Levi\'s',
                'model': '511修身款',
                'size': 'W32L32',
                'color': '深蓝色',
                'material': '98%棉 2%氨纶'
            }
        },
        {
            'name': 'Zara连衣裙 春夏款',
            'description': 'Zara春夏连衣裙，S码，粉色印花，雪纺面料，透气舒适，适合约会和日常穿着。购买后只穿过2次，保存完好。',
            'price': 45.00,
            'category': 'clothing',
            'category_id': clothing_cat.id,
            'condition': '9.5成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Zara',
                'size': 'S码',
                'color': '粉色印花',
                'material': '雪纺',
                'style': '春夏款连衣裙'
            }
        },
        {
            'name': 'Nike Air Max 90 运动鞋',
            'description': 'Nike Air Max 90经典运动鞋，男款US9码，白色配色，购买8个月，轻度使用，鞋底磨损很少，鞋面干净。',
            'price': 120.00,
            'category': 'clothing',
            'category_id': clothing_cat.id,
            'condition': '8.5成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Nike',
                'model': 'Air Max 90',
                'size': 'US9 (27cm)',
                'color': '白色',
                'material': '皮革+网面'
            }
        },
        
        # 动漫周边
        {
            'name': '进击的巨人 利威尔兵长手办',
            'description': '进击的巨人利威尔兵长手办，1/8比例，高约20cm，细节精致，色彩还原度高。购买后一直在展示柜中，从未拆封把玩。',
            'price': 180.00,
            'category': 'anime',
            'category_id': anime_cat.id,
            'condition': '全新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'character': '利威尔·阿卡曼',
                'series': '进击的巨人',
                'scale': '1/8',
                'height': '约20cm',
                'manufacturer': '正版授权'
            }
        },
        {
            'name': '鬼灭之刃 Cosplay服装套装',
            'description': '鬼灭之刃炭治郎Cosplay服装，全套包含外套、裤子、腰带、配件等，尺码M，面料舒适，做工精良。购买后试穿一次。',
            'price': 95.00,
            'category': 'anime',
            'category_id': anime_cat.id,
            'condition': '9.9成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'character': '炭治郎',
                'series': '鬼灭之刃',
                'size': 'M码',
                'include': '外套+裤子+腰带+配件',
                'material': '聚酯纤维'
            }
        },
        {
            'name': '海贼王 路飞草帽',
            'description': '海贼王路飞同款草帽，高品质稻草编织，帽型标准，做工精细。适合Cosplay或日常佩戴，购买后几乎未使用。',
            'price': 25.00,
            'category': 'anime',
            'category_id': anime_cat.id,
            'condition': '9.8成新',
            'quantity': 2,
            'images': ['https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'character': '蒙奇·D·路飞',
                'series': '海贼王',
                'material': '稻草编织',
                'size': '均码',
                'circumference': '58cm'
            }
        },
        
        # 家电用品
        {
            'name': 'Dyson V8 无线吸尘器',
            'description': 'Dyson V8无线吸尘器，购买1.5年，功能完好，吸力强劲，电池续航约40分钟。包含多个吸头，适合不同清洁需求。',
            'price': 320.00,
            'category': 'appliances',
            'category_id': appliances_cat.id,
            'condition': '8.5成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Dyson',
                'model': 'V8 Absolute',
                'battery': '40分钟续航',
                'include': '多种吸头+充电底座',
                'power': '115W'
            }
        },
        {
            'name': 'Breville咖啡机',
            'description': 'Breville半自动咖啡机，不锈钢外壳，15Bar压力，购买2年，日常使用但保养良好，可制作专业级咖啡。',
            'price': 280.00,
            'category': 'appliances',
            'category_id': appliances_cat.id,
            'condition': '8成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Breville',
                'type': '半自动咖啡机',
                'pressure': '15Bar',
                'material': '不锈钢',
                'capacity': '2.8L水箱'
            }
        },
        
        # 图书文具
        {
            'name': 'Python编程：从入门到实践',
            'description': 'Python编程经典教材，第二版，中文版，几乎全新，仅翻阅过几页。适合编程初学者，内容详实，案例丰富。',
            'price': 35.00,
            'category': 'books',
            'category_id': books_cat.id,
            'condition': '9.8成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1481627834876-b7833e8f5570?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'title': 'Python编程：从入门到实践',
                'author': 'Eric Matthes',
                'edition': '第二版',
                'language': '中文',
                'pages': '约500页'
            }
        },
        {
            'name': 'iPad Pro 2021配套键盘',
            'description': 'iPad Pro 12.9寸配套妙控键盘，深空灰色，功能完好，键盘回弹正常，触控板灵敏。购买8个月，使用频率不高。',
            'price': 280.00,
            'category': 'electronics',
            'category_id': electronics_cat.id,
            'condition': '9成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1611532736597-de2d4265fba3?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'Apple',
                'model': 'Magic Keyboard',
                'compatible': 'iPad Pro 12.9寸',
                'color': '深空灰',
                'features': '背光键盘+触控板'
            }
        },
        
        # 其他类别
        {
            'name': '宜家POÄNG休闲椅',
            'description': '宜家POÄNG休闲椅，桦木框架，米色坐垫，购买1年，偶尔使用，结构稳固，坐感舒适。适合客厅或书房。',
            'price': 60.00,
            'category': 'other',
            'category_id': other_cat.id,
            'condition': '9成新',
            'quantity': 1,
            'images': ['https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=400&q=80'],
            'specifications': {
                'brand': 'IKEA',
                'model': 'POÄNG',
                'material': '桦木框架',
                'color': '米色坐垫',
                'dimensions': '68x82x100cm'
            }
        }
    ]
    
    for product_data in products_data:
        product = Product(
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            category=product_data['category'],
            category_id=product_data['category_id'],
            condition=product_data['condition'],
            stock_status=Product.STATUS_AVAILABLE,
            face_to_face_only=product_data.get('face_to_face_only', False),
            quantity=product_data.get('quantity', 1),
            low_stock_threshold=1,
            track_inventory=True
        )
        
        product.set_images(product_data['images'])
        product.set_specifications(product_data['specifications'])
        
        db.session.add(product)
    
    db.session.commit()
    print(f"✓ 已添加 {len(products_data)} 个产品")

def add_orders():
    """添加订单数据"""
    print("添加订单数据...")
    
    # 获取一些产品用于创建订单
    products = Product.query.limit(10).all()
    
    orders_data = [
        {
            'customer_name': '张小明',
            'customer_email': 'zhangxm@gmail.com',
            'customer_phone': '0221234567',
            'delivery_method': 'pickup',
            'payment_method': 'cash',
            'status': 'completed',
            'customer_address': None,
            'notes': '约定在Queen Street见面交易',
            'created_at': datetime.utcnow() - timedelta(days=5)
        },
        {
            'customer_name': '李美丽',
            'customer_email': 'limei@yahoo.com',
            'customer_phone': '0227654321',
            'delivery_method': 'shipping',
            'payment_method': 'anz_transfer',
            'status': 'paid',
            'customer_address': '123 Queen Street, Auckland Central, Auckland 1010',
            'notes': '请在工作日发货，周末家里没人',
            'created_at': datetime.utcnow() - timedelta(days=3)
        },
        {
            'customer_name': '王强',
            'customer_email': 'wangqiang@hotmail.com',
            'customer_phone': '0229876543',
            'delivery_method': 'pickup',
            'payment_method': 'anz_transfer',
            'status': 'paid',
            'customer_address': None,
            'notes': '已转账，请确认收到款项',
            'created_at': datetime.utcnow() - timedelta(days=2)
        },
        {
            'customer_name': '陈静',
            'customer_email': 'chenjing@gmail.com',
            'customer_phone': '0225555555',
            'delivery_method': 'shipping',
            'payment_method': 'bank_transfer',
            'status': 'pending',
            'customer_address': '456 Ponsonby Road, Ponsonby, Auckland 1011',
            'notes': '希望能快递到家',
            'created_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'customer_name': '刘涛',
            'customer_email': 'liutao@outlook.com',
            'customer_phone': '0223333333',
            'delivery_method': 'pickup',
            'payment_method': 'wechat_alipay',
            'status': 'shipped',
            'customer_address': None,
            'notes': '微信支付已完成',
            'created_at': datetime.utcnow() - timedelta(hours=12)
        }
    ]
    
    for i, order_data in enumerate(orders_data):
        # 随机选择1-3个产品
        selected_products = random.sample(products, random.randint(1, 3))
        
        items = []
        total_amount = 0
        
        for product in selected_products:
            quantity = random.randint(1, 2)
            item_total = float(product.price) * quantity
            total_amount += item_total
            
            items.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'condition': product.condition,
                'image': product.get_images()[0] if product.get_images() else ''
            })
        
        # 如果是邮寄，加上邮费
        if order_data['delivery_method'] == 'shipping':
            total_amount += 15.00
        
        order = Order(
            customer_name=order_data['customer_name'],
            customer_email=order_data['customer_email'],
            customer_phone=order_data['customer_phone'],
            delivery_method=order_data['delivery_method'],
            payment_method=order_data['payment_method'],
            status=order_data['status'],
            customer_address=order_data['customer_address'],
            notes=order_data['notes'],
            total_amount=total_amount,
            created_at=order_data['created_at']
        )
        
        order.set_items(items)
        db.session.add(order)
    
    db.session.commit()
    print(f"✓ 已添加 {len(orders_data)} 个订单")

def add_messages():
    """添加留言数据"""
    print("添加留言数据...")
    
    messages_data = [
        {
            'name': '张三',
            'contact': 'zhangsan@gmail.com',
            'message': '您好，我对那台MacBook Air很感兴趣，请问可以约时间看看实物吗？我在Auckland CBD上班。',
            'status': 'replied',
            'reply': '您好张三！MacBook Air确实很不错，我们可以约在Queen Street的安全地点见面。请加我微信sara_nz_2025或者电话0225255862联系具体时间。',
            'created_at': datetime.utcnow() - timedelta(days=2),
            'replied_at': datetime.utcnow() - timedelta(days=2, hours=2)
        },
        {
            'name': '李四',
            'contact': '0227777777',
            'message': '请问那个Dyson吸尘器还有吗？我想要买，可以邮寄到Hamilton吗？',
            'status': 'replied',
            'reply': '您好李四！Dyson V8还有，可以邮寄到Hamilton，邮费大概25纽币。如果确定要买的话，可以先转账，我们收到款项后立即发货。',
            'created_at': datetime.utcnow() - timedelta(days=1),
            'replied_at': datetime.utcnow() - timedelta(days=1, hours=1)
        },
        {
            'name': '王五',
            'contact': 'wangwu@yahoo.com',
            'message': '我对Nintendo Switch很感兴趣，请问包含哪些游戏？电池续航怎么样？',
            'status': 'unread',
            'created_at': datetime.utcnow() - timedelta(hours=6)
        },
        {
            'name': '赵六',
            'contact': '0228888888',
            'message': '那个鬼灭之刃的cos服装质量怎么样？面料会不会很粗糙？我身高175穿M码合适吗？',
            'status': 'unread',
            'created_at': datetime.utcnow() - timedelta(hours=3)
        },
        {
            'name': '孙七',
            'contact': 'sunqi@hotmail.com',
            'message': '请问你们店铺的地址在哪里？我想直接过来看看有什么合适的商品。',
            'status': 'unread',
            'created_at': datetime.utcnow() - timedelta(hours=1)
        }
    ]
    
    for msg_data in messages_data:
        message = Message(
            name=msg_data['name'],
            contact=msg_data['contact'],
            message=msg_data['message'],
            status=msg_data['status'],
            created_at=msg_data['created_at']
        )
        
        if msg_data['status'] == 'replied':
            message.reply = msg_data['reply']
            message.replied_at = msg_data['replied_at']
        
        db.session.add(message)
    
    db.session.commit()
    print(f"✓ 已添加 {len(messages_data)} 条留言")

def show_summary():
    """显示数据汇总"""
    print("\n" + "="*50)
    print("数据添加完成！汇总信息：")
    print("="*50)
    
    # 分类统计
    categories = Category.query.all()
    print(f"📂 分类总数: {len(categories)}")
    for cat in categories:
        product_count = Product.query.filter_by(category_id=cat.id).count()
        print(f"   • {cat.display_name}: {product_count} 个产品")
    
    # 产品统计
    total_products = Product.query.count()
    available_products = Product.query.filter_by(stock_status='available').count()
    print(f"\n📦 产品总数: {total_products}")
    print(f"   • 可售产品: {available_products}")
    
    # 订单统计
    total_orders = Order.query.count()
    print(f"\n📋 订单总数: {total_orders}")
    for status_code, status_name in Order.ORDER_STATUSES:
        count = Order.query.filter_by(status=status_code).count()
        if count > 0:
            print(f"   • {status_name}: {count}")
    
    # 留言统计
    total_messages = Message.query.count()
    unread_messages = Message.query.filter_by(status='unread').count()
    print(f"\n💬 留言总数: {total_messages}")
    print(f"   • 未读留言: {unread_messages}")
    
    # 管理员统计
    total_admins = Admin.query.count()
    print(f"\n👤 管理员总数: {total_admins}")
    
    # 网站设置统计
    total_settings = SiteSettings.query.count()
    print(f"\n⚙️ 网站设置: {total_settings} 项")
    
    print("\n" + "="*50)
    print("测试数据添加完成！现在可以启动应用进行测试。")
    print("管理员登录信息：")
    print("• 超级管理员: admin / admin123")
    print("• 普通管理员: sara / sara123")
    print("• 普通管理员: manager / manager123")
    print("="*50)

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("开始创建测试数据...")
        print("="*50)
        
        # 清空现有数据
        clear_all_data()
        
        # 添加各种数据
        add_categories()
        add_admins()
        add_site_settings()
        add_products()
        add_orders()
        add_messages()
        
        # 显示汇总信息
        show_summary()

if __name__ == '__main__':
    main()