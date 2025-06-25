#!/usr/bin/env python3
"""
分类系统数据库迁移脚本
为现有产品添加分类关联，创建categories表并迁移现有数据
"""

import sys
from flask import Flask
from models import db, Category, Product, init_default_categories

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

def migrate_categories():
    """迁移分类系统"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 分类系统迁移 ===\n")
            
            # 1. 创建categories表
            print("1. 创建categories表...")
            db.create_all()
            print("✓ 数据库表已创建")
            
            # 2. 初始化默认分类
            print("\n2. 初始化默认分类...")
            existing_categories = Category.query.count()
            
            if existing_categories == 0:
                success = init_default_categories()
                if success:
                    categories = Category.query.all()
                    print(f"✓ 成功创建 {len(categories)} 个默认分类")
                    for cat in categories:
                        print(f"   - {cat.display_name} ({cat.name})")
                else:
                    print("✗ 默认分类创建失败")
                    return False
            else:
                print(f"⚠ 已存在 {existing_categories} 个分类，跳过创建")
            
            # 3. 获取分类映射
            print("\n3. 建立分类映射关系...")
            categories = Category.query.all()
            category_map = {cat.name: cat for cat in categories}
            
            # 旧分类常量到新分类的映射
            legacy_category_map = {
                'electronics': 'electronics',
                'clothing': 'clothing', 
                'anime': 'anime',
                'appliances': 'appliances',
                'other': 'other'
            }
            
            print("分类映射关系:")
            for legacy, new in legacy_category_map.items():
                if new in category_map:
                    print(f"   {legacy} -> {category_map[new].display_name}")
                else:
                    print(f"   {legacy} -> 未找到对应分类")
            
            # 4. 迁移现有产品的分类关联
            print("\n4. 迁移产品分类关联...")
            products = Product.query.all()
            
            if not products:
                print("⚠ 没有找到任何产品，跳过迁移")
                return True
            
            migrated_count = 0
            unmapped_count = 0
            
            for product in products:
                # 如果产品已经有category_id，跳过
                if product.category_id:
                    continue
                    
                # 根据旧的category字段查找对应的新分类
                legacy_category = product.category
                if legacy_category in legacy_category_map:
                    new_category_name = legacy_category_map[legacy_category]
                    if new_category_name in category_map:
                        product.category_id = category_map[new_category_name].id
                        migrated_count += 1
                        print(f"   ✓ {product.name} ({legacy_category} -> {category_map[new_category_name].display_name})")
                    else:
                        unmapped_count += 1
                        print(f"   ⚠ {product.name} - 未找到对应分类: {new_category_name}")
                else:
                    # 尝试直接匹配分类名
                    if legacy_category in category_map:
                        product.category_id = category_map[legacy_category].id
                        migrated_count += 1
                        print(f"   ✓ {product.name} ({legacy_category} -> {category_map[legacy_category].display_name})")
                    else:
                        # 默认分配到"其他"分类
                        if 'other' in category_map:
                            product.category_id = category_map['other'].id
                            migrated_count += 1
                            print(f"   ? {product.name} - 未知分类 '{legacy_category}'，分配到'其他'")
                        else:
                            unmapped_count += 1
                            print(f"   ✗ {product.name} - 无法分配分类: {legacy_category}")
            
            # 5. 提交更改
            if migrated_count > 0:
                db.session.commit()
                print(f"\n✓ 成功迁移 {migrated_count} 个产品的分类关联")
            
            if unmapped_count > 0:
                print(f"⚠ {unmapped_count} 个产品未能分配分类")
            
            # 6. 验证迁移结果
            print("\n5. 验证迁移结果...")
            for category in categories:
                product_count = category.get_product_count()
                print(f"   {category.display_name}: {product_count} 个产品")
            
            unassigned_products = Product.query.filter(Product.category_id == None).count()
            if unassigned_products > 0:
                print(f"   ⚠ 未分配分类的产品: {unassigned_products} 个")
            else:
                print("   ✓ 所有产品都已分配分类")
            
            print("\n=== 迁移完成 ===")
            print("现在可以在管理后台使用新的分类管理功能了！")
            
            return True
            
        except Exception as e:
            print(f"✗ 迁移过程中出现错误: {str(e)}")
            db.session.rollback()
            return False

def rollback_migration():
    """回滚分类迁移（将category_id设为None）"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 回滚分类迁移 ===\n")
            
            # 统计当前状态
            products_with_category_id = Product.query.filter(Product.category_id != None).count()
            
            if products_with_category_id == 0:
                print("没有产品关联了新分类，无需回滚")
                return True
            
            print(f"发现 {products_with_category_id} 个产品关联了新分类")
            
            # 确认回滚
            confirm = input("确定要回滚分类迁移吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("回滚操作已取消")
                return False
            
            # 清除category_id
            Product.query.update({Product.category_id: None})
            db.session.commit()
            
            print(f"✓ 已清除 {products_with_category_id} 个产品的分类关联")
            print("注意：categories表和分类数据仍然保留")
            
            return True
            
        except Exception as e:
            print(f"✗ 回滚过程中出现错误: {str(e)}")
            db.session.rollback()
            return False

def show_migration_status():
    """显示迁移状态"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 分类迁移状态 ===\n")
            
            # 检查categories表是否存在
            try:
                category_count = Category.query.count()
                print(f"Categories表: ✓ 存在 ({category_count} 个分类)")
                
                # 显示分类统计
                categories = Category.query.order_by(Category.sort_order).all()
                for cat in categories:
                    product_count = cat.get_product_count()
                    status = "激活" if cat.is_active else "禁用"
                    print(f"   {cat.display_name}: {product_count} 个产品 [{status}]")
                    
            except Exception:
                print("Categories表: ✗ 不存在或无法访问")
                return
            
            # 检查产品分类关联状态
            total_products = Product.query.count()
            products_with_category_id = Product.query.filter(Product.category_id != None).count()
            products_without_category_id = total_products - products_with_category_id
            
            print(f"\n产品分类关联状态:")
            print(f"   总产品数: {total_products}")
            print(f"   已关联新分类: {products_with_category_id}")
            print(f"   未关联新分类: {products_without_category_id}")
            
            if products_without_category_id > 0:
                print(f"\n⚠ 发现 {products_without_category_id} 个产品未关联新分类")
                print("   建议运行迁移脚本进行数据迁移")
            else:
                print("\n✓ 所有产品都已关联新分类系统")
                
        except Exception as e:
            print(f"✗ 检查状态时出现错误: {str(e)}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python migrate_categories.py migrate   # 执行分类系统迁移")
        print("  python migrate_categories.py rollback  # 回滚分类迁移")
        print("  python migrate_categories.py status    # 显示迁移状态")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'migrate':
        migrate_categories()
    elif command == 'rollback':
        rollback_migration()
    elif command == 'status':
        show_migration_status()
    else:
        print(f"未知命令: {command}")
        print("支持的命令: migrate, rollback, status")

if __name__ == '__main__':
    main()