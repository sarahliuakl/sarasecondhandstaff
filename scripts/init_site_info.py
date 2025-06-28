#!/usr/bin/env python3
"""
站点信息初始化脚本
确保站点信息数据被正确加载到应用使用的数据库中
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
    
    # 使用与应用相同的数据库配置
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sara-secondhand-shop-2025'
    
    # 初始化数据库
    db.init_app(app)
    
    return app


def check_and_create_tables():
    """检查并创建表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否存在
            SiteInfoSection.query.first()
            print("✓ 站点信息表已存在")
            return True
        except Exception as e:
            print(f"站点信息表不存在，开始创建... ({str(e)})")
            try:
                # 创建所有表
                db.create_all()
                print("✓ 站点信息表创建成功")
                return True
            except Exception as create_error:
                print(f"✗ 创建表失败: {str(create_error)}")
                return False


def clear_existing_data():
    """清空现有的站点信息数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 删除所有翻译记录
            SiteInfoTranslation.query.delete()
            print("✓ 清除翻译记录")
            
            # 删除所有信息项
            SiteInfoItem.query.delete()
            print("✓ 清除信息项")
            
            # 删除所有部分
            SiteInfoSection.query.delete()
            print("✓ 清除信息部分")
            
            db.session.commit()
            print("✓ 数据清理完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 清理数据失败: {str(e)}")
            return False


def init_site_info_data():
    """初始化站点信息数据"""
    app = create_app()
    
    with app.app_context():
        if init_default_site_info():
            print("✓ 站点信息数据初始化成功")
            return True
        else:
            print("✗ 站点信息数据初始化失败")
            return False


def add_english_translations():
    """添加英文翻译数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 英文翻译数据
            translations_data = {
                'owner_info': {
                    'name': {'value': 'Sara'},
                    'phone': {'label': 'Phone', 'value': '0225255862'},
                    'email': {'label': 'Email', 'value': 'sarahliu.akl@gmail.com'},
                    'location': {'label': 'Location', 'value': 'Auckland North Shore'},
                    'introduction': {'value': 'Hello, welcome to Sara\'s Store! I\'m Sara, currently living in North Shore Auckland, love life and enjoy sharing. I hope through this warm little store to help quality second-hand items from my home find new owners, and also benefit more friends.'}
                },
                'security_features': {
                    'authentic_photos': {'title': 'Authentic Photos', 'description': 'All items are for personal use, photographed from actual items, with authentic descriptions.'},
                    'delivery_options': {'title': 'Delivery Options', 'description': 'Support face-to-face and postal delivery, Auckland area prioritizes face-to-face transactions.'},
                    'payment_flexibility': {'title': 'Payment Flexibility', 'description': 'Flexible payment methods, safe and reliable.'},
                    'quick_response': {'title': 'Quick Response', 'description': 'Promise to reply to all inquiries within 2 hours, patiently answer after-sales questions.'}
                },
                'policies': {
                    'return_policy': {'value': 'Second-hand items do not support returns after face-to-face confirmation.'},
                    'after_sales': {'value': 'If you have any questions or after-sales issues, you can contact us, Sara will patiently answer.'},
                    'product_guarantee': {'value': 'All products are photographed from actual items, ensuring authentic descriptions.'}
                },
                'payment_methods': {
                    'anz_transfer': {'title': 'ANZ Bank Transfer', 'icon': '🏦'},
                    'bank_transfer': {'title': 'Inter-bank Transfer', 'icon': '🔄'},
                    'wechat_alipay': {'title': 'WeChat/Alipay', 'icon': '📱'},
                    'cash': {'title': 'Cash Payment', 'icon': '💵'}
                },
                'faq': {
                    'shipping_areas': {'question': 'Which cities in New Zealand can you ship to?', 'answer': 'Supports nationwide shipping in New Zealand, Auckland area prioritizes face-to-face transactions.'},
                    'order_status': {'question': 'How to check order status?', 'answer': 'You can contact Sara via email or phone to check order status.'},
                    'after_sales_service': {'question': 'How is after-sales service guaranteed?', 'answer': 'If there are after-sales issues, Sara will reply within 2 hours and assist in resolving them.'},
                    'shipping_cost': {'question': 'How is shipping cost calculated?', 'answer': 'Shipping cost is calculated based on item size and weight, Auckland area is recommended for face-to-face transaction.'}
                },
                'contact_info': {
                    'working_hours': {'label': 'Working Hours', 'value': '9:00-21:00'},
                    'service_area': {'label': 'Service Area', 'value': 'Auckland North Shore'},
                    'response_time': {'label': 'Response Time', 'value': 'Reply within 24 hours'}
                }
            }
            
            # 为每个部分添加英文翻译
            for section_key, section_translations in translations_data.items():
                section = SiteInfoSection.query.filter(SiteInfoSection.key == section_key).first()
                if not section:
                    continue
                
                for item_key, translation_content in section_translations.items():
                    item = SiteInfoItem.query.filter(
                        SiteInfoItem.section_id == section.id,
                        SiteInfoItem.key == item_key
                    ).first()
                    
                    if not item:
                        continue
                    
                    # 检查是否已存在英文翻译
                    existing_translation = SiteInfoTranslation.query.filter(
                        SiteInfoTranslation.item_id == item.id,
                        SiteInfoTranslation.language == 'en'
                    ).first()
                    
                    if existing_translation:
                        existing_translation.set_content(translation_content)
                    else:
                        translation = SiteInfoTranslation(
                            item_id=item.id,
                            language='en'
                        )
                        translation.set_content(translation_content)
                        db.session.add(translation)
            
            db.session.commit()
            print("✓ 英文翻译数据添加成功")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 添加英文翻译失败: {str(e)}")
            return False


def show_data_summary():
    """显示数据概要"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 站点信息数据概要 ===")
            
            sections = SiteInfoSection.query.order_by(SiteInfoSection.sort_order).all()
            total_items = 0
            total_translations = 0
            
            for section in sections:
                items_count = section.items.count()
                total_items += items_count
                
                # 统计该部分的翻译数量
                section_translations = 0
                for item in section.items:
                    translations = item.translations.count()
                    section_translations += translations
                    total_translations += translations
                
                print(f"  {section.icon or '📄'} {section.name} ({section.key})")
                print(f"    - 信息项: {items_count} 个")
                print(f"    - 翻译: {section_translations} 条")
                print(f"    - 状态: {'启用' if section.is_active else '禁用'}")
                print()
            
            print(f"总计:")
            print(f"  - 信息部分: {len(sections)} 个")
            print(f"  - 信息项: {total_items} 个")
            print(f"  - 翻译记录: {total_translations} 条")
            
            # 检查数据完整性
            print(f"\n=== 数据完整性检查 ===")
            has_chinese = total_items > 0
            has_english = total_translations > 0
            print(f"  - 中文内容: {'✓' if has_chinese else '✗'}")
            print(f"  - 英文翻译: {'✓' if has_english else '✗'}")
            
            return True
            
        except Exception as e:
            print(f"✗ 获取数据概要失败: {str(e)}")
            return False


def main():
    """主函数"""
    print("=== Sara 站点信息初始化脚本 ===\n")
    
    # 检查参数
    force_reset = '--reset' in sys.argv
    skip_translations = '--no-en' in sys.argv
    
    if force_reset:
        print("⚠️  强制重置模式，将清空所有现有数据")
        confirm = input("确定要继续吗？(y/N): ")
        if confirm.lower() != 'y':
            print("操作已取消")
            return
    
    # 步骤1: 检查并创建表
    print("步骤1: 检查数据库表...")
    if not check_and_create_tables():
        print("初始化失败")
        return
    
    # 步骤2: 清理数据（如果需要）
    if force_reset:
        print("\n步骤2: 清理现有数据...")
        if not clear_existing_data():
            print("清理失败")
            return
    
    # 步骤3: 初始化基础数据
    print(f"\n步骤3: 初始化站点信息数据...")
    if not init_site_info_data():
        print("初始化失败")
        return
    
    # 步骤4: 添加英文翻译（如果需要）
    if not skip_translations:
        print(f"\n步骤4: 添加英文翻译...")
        if not add_english_translations():
            print("翻译添加失败")
            return
    
    # 步骤5: 显示结果
    print(f"\n步骤5: 检查结果...")
    show_data_summary()
    
    print(f"\n🎉 站点信息初始化完成！")
    print(f"现在可以访问管理后台查看和编辑站点信息:")
    print(f"  - 管理界面: /admin/site-info")
    print(f"  - 前台页面: /zh/info 或 /en/info")


if __name__ == "__main__":
    main()