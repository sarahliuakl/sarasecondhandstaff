#!/usr/bin/env python3
"""
站点信息数据库迁移脚本
添加SiteInfoSection、SiteInfoItem、SiteInfoTranslation表
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask
from models import db, SiteInfoSection, SiteInfoItem, SiteInfoTranslation, init_default_site_info
import json

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    # 检查多个可能的数据库位置
    possible_db_paths = [
        os.path.join(basedir, "..", "sara_shop.db"),
        os.path.join(basedir, "..", "instance", "sara_shop.db"),
        os.path.join(basedir, "..", "src", "sara_shop.db")
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        # 如果没有找到现有数据库，使用默认位置
        db_path = possible_db_paths[0]
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sara-secondhand-shop-2025'
    
    # 初始化数据库
    db.init_app(app)
    
    return app


def check_tables_exist():
    """检查新表是否已经存在"""
    app = create_app()
    
    with app.app_context():
        try:
            # 尝试查询新表
            SiteInfoSection.query.first()
            SiteInfoItem.query.first()
            SiteInfoTranslation.query.first()
            return True
        except Exception:
            return False


def create_site_info_tables():
    """创建站点信息相关表"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始创建站点信息数据表...")
            
            # 创建新表
            db.create_all()
            print("✓ 站点信息数据表创建成功")
            
            # 初始化默认数据
            if init_default_site_info():
                print("✓ 默认站点信息数据初始化成功")
            else:
                print("✗ 默认站点信息数据初始化失败")
                return False
            
            print("✓ 站点信息迁移完成！")
            return True
            
        except Exception as e:
            print(f"✗ 创建站点信息表时发生错误: {e}")
            db.session.rollback()
            return False


def show_migration_info():
    """显示迁移后的信息"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 站点信息数据统计 ===")
            
            # 统计各表的记录数
            sections_count = SiteInfoSection.query.count()
            items_count = SiteInfoItem.query.count()
            translations_count = SiteInfoTranslation.query.count()
            
            print(f"信息部分总数: {sections_count}")
            print(f"信息项总数: {items_count}")
            print(f"翻译记录总数: {translations_count}")
            
            # 显示各部分的详细信息
            print("\n各部分详细信息:")
            sections = SiteInfoSection.query.order_by(SiteInfoSection.sort_order).all()
            for section in sections:
                items_count = section.items.count()
                print(f"  {section.name} ({section.key}): {items_count} 个信息项")
            
            return True
            
        except Exception as e:
            print(f"获取迁移信息时发生错误: {e}")
            return False


def rollback_migration():
    """回滚迁移（删除新创建的表）"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始回滚站点信息表...")
            
            # 删除表（注意删除顺序，先删除有外键关系的表）
            SiteInfoTranslation.__table__.drop(db.engine, checkfirst=True)
            print("✓ 删除站点信息翻译表")
            
            SiteInfoItem.__table__.drop(db.engine, checkfirst=True)
            print("✓ 删除站点信息项表")
            
            SiteInfoSection.__table__.drop(db.engine, checkfirst=True)
            print("✓ 删除站点信息部分表")
            
            print("✓ 站点信息表回滚完成")
            return True
            
        except Exception as e:
            print(f"回滚过程中发生错误: {e}")
            return False


def main():
    """主函数"""
    print("=== 站点信息数据库迁移工具 ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        # 回滚操作
        print("执行回滚操作...")
        if rollback_migration():
            print("回滚成功完成")
            return True
        else:
            print("回滚失败")
            return False
    
    # 检查表是否已存在
    if check_tables_exist():
        print("站点信息表已存在，无需重复迁移")
        show_migration_info()
        return True
    
    # 执行迁移
    print("开始创建站点信息表...")
    if create_site_info_tables():
        show_migration_info()
        print("\n迁移成功完成！")
        print("现在可以在后台管理界面中管理站点信息了。")
        return True
    else:
        print("迁移失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)