"""
Sara二手售卖网站 - 数据库初始化脚本
用于创建数据库表结构并导入示例数据
"""

from flask import Flask
from src.models import db, Product, Order, Message
import os

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sara-secondhand-shop-2025'
    
    # 初始化数据库
    db.init_app(app)
    
    return app


def init_database():
    """初始化数据库，创建表结构并导入示例数据"""
    app = create_app()
    
    with app.app_context():
        print("开始初始化数据库...")
        
        # 删除现有表（如果存在）
        db.drop_all()
        print("已删除现有数据表")
        
        # 创建所有表
        db.create_all()
        print("已创建数据表结构")
        
        # 导入示例产品数据
        import_sample_products()
        print("已导入示例产品数据")
        
        # 导入示例留言数据
        import_sample_messages()
        print("已导入示例留言数据")
        
        print("数据库初始化完成！")
        print(f"数据库文件位置: {os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sara_shop.db')}")


def import_sample_products():
    """导入示例产品数据"""
    
    # 根据项目需求中提到的商品创建示例数据
    sample_products = [
        {
            'name': '9成新笔记本电脑 (第1台)',
            'description': '多角度实拍，性能优良，适合办公学习。Dell Inspiron 15，Intel i5处理器，8GB内存，256GB SSD，使用时间短，保养良好，无任何损坏。',
            'price': 650.00,
            'category': Product.CATEGORY_ELECTRONICS,
            'condition': '9成新',
            'images': [
                'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80',
                'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'brand': 'Dell',
                'model': 'Inspiron 15',
                'cpu': 'Intel Core i5',
                'ram': '8GB DDR4',
                'storage': '256GB SSD',
                'screen': '15.6英寸',
                'condition_detail': '9成新，外观无划痕，性能良好'
            }
        },
        {
            'name': '9成新笔记本电脑 (第2台)',
            'description': '第二台笔记本电脑，配置略有不同。联想ThinkPad，商务办公首选，键盘手感极佳，屏幕色彩准确。',
            'price': 720.00,
            'category': Product.CATEGORY_ELECTRONICS,
            'condition': '9成新',
            'images': [
                'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'brand': 'Lenovo',
                'model': 'ThinkPad E15',
                'cpu': 'Intel Core i5',
                'ram': '16GB DDR4',
                'storage': '512GB SSD',
                'screen': '15.6英寸',
                'condition_detail': '9成新，商务办公理想选择'
            }
        },
        {
            'name': '8.5成新保暖大衣 (第1件)',
            'description': '冬季必备，时尚保暖，尺码适中。高质量羽绒填充，防风防水面料，保养良好，几乎没有使用痕迹。',
            'price': 80.00,
            'category': Product.CATEGORY_CLOTHING,
            'condition': '8.5成新',
            'images': [
                'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'size': 'M (适合身高160-170cm)',
                'color': '深蓝色',
                'material': '90%白鸭绒填充',
                'brand': 'Uniqlo',
                'condition_detail': '8.5成新，保暖效果极佳'
            }
        },
        {
            'name': '8.5成新保暖大衣 (第2件)',
            'description': '另一件保暖大衣，颜色和款式不同。适合不同身材的朋友，时尚百搭。',
            'price': 85.00,
            'category': Product.CATEGORY_CLOTHING,
            'condition': '8.5成新',
            'images': [
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'size': 'L (适合身高165-175cm)',
                'color': '黑色',
                'material': '羽绒混纺',
                'brand': 'H&M',
                'condition_detail': '8.5成新，经典黑色百搭款'
            }
        },
        {
            'name': '8.5成新保暖大衣 (第3件)',
            'description': '第三件保暖大衣，小码适合娇小身材。颜色清新，款式优雅。',
            'price': 75.00,
            'category': Product.CATEGORY_CLOTHING,
            'condition': '8.5成新',
            'images': [
                'https://images.unsplash.com/photo-1539533018447-63fcce2678e3?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'size': 'S (适合身高155-165cm)',
                'color': '米白色',
                'material': '合成羽绒',
                'brand': 'ZARA',
                'condition_detail': '8.5成新，适合娇小身材'
            }
        },
        {
            'name': '9.5成新夏日长裙 (第1件)',
            'description': '清新夏日长裙，面料舒适透气，版型优雅，几乎全新状态，只穿过几次。',
            'price': 45.00,
            'category': Product.CATEGORY_CLOTHING,
            'condition': '9.5成新',
            'images': [
                'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'size': 'M',
                'color': '浅蓝色',
                'material': '100%棉质',
                'brand': 'Forever 21',
                'condition_detail': '9.5成新，几乎全新'
            }
        },
        {
            'name': '9.5成新夏日长裙 (第2件)',
            'description': '另一件夏日长裙，花色图案，适合度假穿着，保存完好。',
            'price': 50.00,
            'category': Product.CATEGORY_CLOTHING,
            'condition': '9.5成新',
            'images': [
                'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'size': 'S',
                'color': '花色印花',
                'material': '棉麻混纺',
                'brand': 'Zara',
                'condition_detail': '9.5成新，度假风格'
            }
        },
        {
            'name': '9.9成新角色扮演服装 (第1套)',
            'description': '高质量角色扮演服装，制作精良，面料舒适，尺码标准，几乎全新状态。',
            'price': 120.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'character': '动漫角色服装',
                'size': 'M',
                'material': '高档聚酯纤维',
                'include': '全套服装配件',
                'condition_detail': '9.9成新，几乎未使用'
            }
        },
        {
            'name': '9.9成新角色扮演服装 (第2套)',
            'description': '另一套角色扮演服装，不同角色，同样高品质制作。',
            'price': 135.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'character': '经典动漫角色',
                'size': 'L',
                'material': '高档面料',
                'include': '服装+配饰',
                'condition_detail': '9.9成新，收藏级品质'
            }
        },
        {
            'name': '9.9成新动漫人物假发 (第1套)',
            'description': '高品质动漫人物假发，色彩还原度高，材质柔软自然，带假发网。',
            'price': 35.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'color': '蓝色长发',
                'length': '80cm',
                'material': '高温丝',
                'include': '假发+发网+护理液',
                'condition_detail': '9.9成新，几乎未使用'
            }
        },
        {
            'name': '9.9成新动漫人物假发 (第2套)',
            'description': '另一顶动漫假发，短发款式，适合不同角色需求。',
            'price': 30.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'color': '粉色短发',
                'length': '35cm',
                'material': '高温丝',
                'include': '假发+发网',
                'condition_detail': '9.9成新，短发款式'
            }
        },
        {
            'name': '9.9成新动漫人物假发 (第3套)',
            'description': '第三顶假发，经典黑色，适合多种角色扮演。',
            'price': 32.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'color': '黑色长发',
                'length': '60cm',
                'material': '高温丝',
                'include': '假发+发网+梳子',
                'condition_detail': '9.9成新，经典黑色'
            }
        },
        {
            'name': '9.9成新二手机壳',
            'description': '高品质手机保护壳，透明材质，保护性能良好，几乎全新。',
            'price': 15.00,
            'category': Product.CATEGORY_ELECTRONICS,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1512499617640-c74ae3a79d37?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'brand': 'Spigen',
                'model': 'iPhone 13 Pro',
                'material': 'TPU+PC',
                'color': '透明',
                'condition_detail': '9.9成新，透明保护壳'
            }
        },
        {
            'name': '9.5成新3D打印机',
            'description': '专业级3D打印机，功能完善，打印精度高，适合爱好者和小型工作室使用。',
            'price': 280.00,
            'category': Product.CATEGORY_ELECTRONICS,
            'condition': '9.5成新',
            'images': [
                'https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'brand': 'Ender 3',
                'print_size': '220×220×250mm',
                'material': 'PLA/ABS',
                'include': '打印机+工具包+说明书',
                'condition_detail': '9.5成新，使用次数很少'
            }
        },
        {
            'name': '9.9成新显卡',
            'description': '高性能显卡，游戏和专业应用皆可，保存完好，性能稳定。',
            'price': 450.00,
            'category': Product.CATEGORY_ELECTRONICS,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'brand': 'NVIDIA',
                'model': 'RTX 3060',
                'memory': '12GB GDDR6',
                'interface': 'PCIe 4.0',
                'condition_detail': '9.9成新，几乎未使用'
            }
        },
        {
            'name': '动漫人物小勋章套装',
            'description': '各种动漫人物小勋章，做工精美，适合收藏和装饰，数量丰富。',
            'price': 25.00,
            'category': Product.CATEGORY_ANIME,
            'condition': '9.9成新',
            'images': [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            ],
            'specifications': {
                'quantity': '15个装',
                'material': '合金+珐琅',
                'size': '2-3cm',
                'include': '勋章+包装盒',
                'condition_detail': '9.9成新，收藏级品质'
            }
        }
    ]
    
    # 将示例数据添加到数据库
    for product_data in sample_products:
        product = Product(
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            category=product_data['category'],
            condition=product_data['condition'],
            stock_status=Product.STATUS_AVAILABLE
        )
        
        product.set_images(product_data['images'])
        product.set_specifications(product_data['specifications'])
        
        db.session.add(product)
    
    db.session.commit()


def import_sample_messages():
    """导入示例留言数据"""
    
    sample_messages = [
        {
            'name': '张小明',
            'contact': 'zhang@example.com',
            'message': '您好Sara，我对那台Dell笔记本电脑很感兴趣，请问可以先看看实物吗？我在奥克兰市中心工作。',
            'status': Message.STATUS_REPLIED,
            'reply': '您好张小明！当然可以看实物，我们可以约在奥克兰市中心的安全地点见面。请加我微信或者打电话0225255862具体约时间地点。'
        },
        {
            'name': '李美丽',
            'contact': '021-456-789',
            'message': '请问那件蓝色的夏日长裙还有吗？我穿M码，可以邮寄到基督城吗？',
            'status': Message.STATUS_REPLIED,
            'reply': '您好李美丽！蓝色长裙还有，M码很合适。邮寄到基督城没问题，邮费大约15纽币。如果确认购买，请提供详细地址。'
        },
        {
            'name': '王动漫',
            'contact': 'wangdm@gmail.com',
            'message': '我是cosplay爱好者，想了解一下角色扮演服装的具体尺寸和包含的配件有哪些？',
            'status': Message.STATUS_UNREAD
        },
        {
            'name': '陈技术',
            'contact': '022-789-456',
            'message': '3D打印机还能正常使用吗？有没有使用说明书？我是新手，担心不会操作。',
            'status': Message.STATUS_UNREAD
        }
    ]
    
    for msg_data in sample_messages:
        message = Message(
            name=msg_data['name'],
            contact=msg_data['contact'],
            message=msg_data['message'],
            status=msg_data['status']
        )
        
        if 'reply' in msg_data:
            message.reply = msg_data['reply']
            from datetime import datetime, timedelta
            message.replied_at = datetime.utcnow() - timedelta(hours=1)
        
        db.session.add(message)
    
    db.session.commit()


def show_database_info():
    """显示数据库信息"""
    app = create_app()
    
    with app.app_context():
        print("\n=== 数据库信息 ===")
        
        # 产品统计
        total_products = Product.query.count()
        available_products = Product.query.filter(Product.stock_status == Product.STATUS_AVAILABLE).count()
        
        print(f"产品总数: {total_products}")
        print(f"可售产品: {available_products}")
        
        # 按分类统计
        print("\n按分类统计:")
        for category, display_name in Product.CATEGORIES:
            count = Product.query.filter(Product.category == category).count()
            print(f"  {display_name}: {count}")
        
        # 订单统计
        total_orders = Order.query.count()
        print(f"\n订单总数: {total_orders}")
        
        # 留言统计
        total_messages = Message.query.count()
        unread_messages = Message.query.filter(Message.status == Message.STATUS_UNREAD).count()
        print(f"\n留言总数: {total_messages}")
        print(f"未读留言: {unread_messages}")


if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 显示数据库信息
    show_database_info()