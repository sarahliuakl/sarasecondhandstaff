#!/usr/bin/env python3
"""
分类数据初始化脚本
创建默认的产品分类数据，用于管理后台的分类管理功能
"""

import sys
import os
from flask import Flask
from models import db, Category, init_default_categories

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 从环境变量或配置文件加载配置
    from config import Config
    config = Config()
    
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    
    # 如果支持连接池选项，添加它们
    if hasattr(config, 'SQLALCHEMY_ENGINE_OPTIONS'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    return app

def init_categories():
    """初始化分类数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建categories表（如果不存在）
            db.create_all()
            print("✓ 数据库表已创建")
            
            # 检查是否已有分类数据
            existing_count = Category.query.count()
            if existing_count > 0:
                print(f"⚠ 已存在 {existing_count} 个分类，跳过初始化")
                
                # 显示现有分类
                categories = Category.query.order_by(Category.sort_order, Category.created_at).all()
                print("\n现有分类列表:")
                for cat in categories:
                    status = "激活" if cat.is_active else "禁用"
                    print(f"  - {cat.display_name} ({cat.name}) [{status}]")
                return
            
            # 初始化默认分类
            print("正在初始化默认分类数据...")
            success = init_default_categories()
            
            if success:
                # 显示创建的分类
                categories = Category.query.order_by(Category.sort_order).all()
                print(f"✓ 成功创建 {len(categories)} 个默认分类:")
                
                for cat in categories:
                    icon_display = f" ({cat.icon})" if cat.icon else ""
                    print(f"  - {cat.display_name} ({cat.name}){icon_display}")
                
                print("\n分类初始化完成！现在可以在管理后台进行分类管理。")
            else:
                print("✗ 分类初始化失败")
                return False
                
        except Exception as e:
            print(f"✗ 初始化过程中出现错误: {str(e)}")
            return False
    
    return True

def reset_categories():
    """重置分类数据（删除所有分类并重新创建）"""
    app = create_app()
    
    with app.app_context():
        try:
            # 删除所有现有分类
            deleted_count = Category.query.count()
            Category.query.delete()
            db.session.commit()
            
            if deleted_count > 0:
                print(f"✓ 已删除 {deleted_count} 个现有分类")
            
            # 重新初始化默认分类
            success = init_default_categories()
            
            if success:
                categories = Category.query.order_by(Category.sort_order).all()
                print(f"✓ 重新创建 {len(categories)} 个默认分类")
                
                for cat in categories:
                    icon_display = f" ({cat.icon})" if cat.icon else ""
                    print(f"  - {cat.display_name} ({cat.name}){icon_display}")
                    
                print("\n分类重置完成！")
            else:
                print("✗ 分类重置失败")
                return False
                
        except Exception as e:
            print(f"✗ 重置过程中出现错误: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def show_categories():
    """显示当前所有分类"""
    app = create_app()
    
    with app.app_context():
        try:
            categories = Category.query.order_by(Category.sort_order, Category.created_at).all()
            
            if not categories:
                print("当前没有任何分类数据")
                return
            
            print(f"当前共有 {len(categories)} 个分类:\n")
            print("ID  | 排序 | 名称          | 显示名称    | Slug       | 图标           | 状态 | 产品数")
            print("-" * 85)
            
            for cat in categories:
                status = "激活" if cat.is_active else "禁用"
                icon = cat.icon or "-"
                product_count = cat.get_product_count()
                
                print(f"{cat.id:2d}  | {cat.sort_order:2d}   | {cat.name:12s} | {cat.display_name:8s} | {cat.slug:10s} | {icon:12s} | {status:2s} | {product_count:3d}")
                
        except Exception as e:
            print(f"✗ 查询分类时出现错误: {str(e)}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python init_categories.py init    # 初始化默认分类（如果没有现有分类）")
        print("  python init_categories.py reset   # 重置所有分类（删除现有并重新创建）")
        print("  python init_categories.py show    # 显示当前所有分类")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        print("=== 分类初始化工具 ===")
        init_categories()
    elif command == 'reset':
        print("=== 分类重置工具 ===")
        print("⚠ 警告：此操作将删除所有现有分类数据！")
        
        # 确认操作
        confirm = input("确定要继续吗？(y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            reset_categories()
        else:
            print("操作已取消")
    elif command == 'show':
        print("=== 当前分类列表 ===")
        show_categories()
    else:
        print(f"未知命令: {command}")
        print("支持的命令: init, reset, show")

if __name__ == '__main__':
    main()