"""
Sara二手售卖网站 - 数据库初始化脚本
用于创建数据库表结构并导入示例数据
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from flask import Flask
from src.models import db, Order, Admin, init_default_site_info

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
        
        # 导入admin用户
        import_admin_user()
        print("已导入admin用户")
        
        # 导入站点信息数据
        import_site_info()
        print("已导入站点信息数据")
        
        print("数据库初始化完成！")
        print(f"数据库文件位置: {os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sara_shop.db')}")





def import_admin_user():
    """导入admin用户"""
    
    # 检查是否已存在admin用户
    existing_admin = Admin.query.filter(Admin.username == 'admin').first()
    if existing_admin:
        print("admin用户已存在，跳过创建")
        return
    
    # 创建admin用户
    admin_user = Admin(
        username='admin',
        email='admin@sarastore.com',
        is_super_admin=True
    )
    admin_user.set_password('admin123')  # 建议在生产环境中使用更强的密码
    
    db.session.add(admin_user)
    db.session.commit()


def import_site_info():
    """导入站点信息数据"""
    
    # 使用模型中的初始化函数
    success = init_default_site_info()
    if not success:
        print("警告：站点信息数据初始化可能不完整")


def show_database_info():
    """显示数据库信息"""
    app = create_app()
    
    with app.app_context():
        print("\n=== 数据库信息 ===")
        
        # 管理员统计
        total_admins = Admin.query.count()
        print(f"管理员用户数: {total_admins}")
        
        # 订单统计
        total_orders = Order.query.count()
        print(f"订单总数: {total_orders}")
        
        # 站点信息统计
        from src.models import SiteInfoSection
        total_info_sections = SiteInfoSection.query.count()
        print(f"站点信息栏目数: {total_info_sections}")


if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 显示数据库信息
    show_database_info()