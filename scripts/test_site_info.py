#!/usr/bin/env python3
"""
站点信息功能测试脚本
验证所有功能是否正常工作
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask
from models import db, SiteInfoSection, SiteInfoItem, SiteInfoTranslation, get_all_site_info_data

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sara-secondhand-shop-2025'
    
    db.init_app(app)
    return app

def test_database_structure():
    """测试数据库结构"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 测试数据库结构 ===")
            
            # 测试部分查询
            sections = SiteInfoSection.query.all()
            print(f"✓ 查询到 {len(sections)} 个信息部分")
            
            # 测试信息项查询
            items = SiteInfoItem.query.all()
            print(f"✓ 查询到 {len(items)} 个信息项")
            
            # 测试翻译查询
            translations = SiteInfoTranslation.query.all()
            print(f"✓ 查询到 {len(translations)} 条翻译记录")
            
            return True
            
        except Exception as e:
            print(f"✗ 数据库结构测试失败: {str(e)}")
            return False

def test_data_integrity():
    """测试数据完整性"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 测试数据完整性 ===")
            
            expected_sections = ['owner_info', 'policies', 'transaction_info', 'faq', 'contact_info']
            
            for section_key in expected_sections:
                section = SiteInfoSection.query.filter(SiteInfoSection.key == section_key).first()
                if not section:
                    print(f"✗ 缺少部分: {section_key}")
                    return False
                
                items_count = section.items.count()
                if items_count == 0:
                    print(f"✗ 部分 {section_key} 没有信息项")
                    return False
                
                print(f"✓ 部分 {section.name} 有 {items_count} 个信息项")
            
            return True
            
        except Exception as e:
            print(f"✗ 数据完整性测试失败: {str(e)}")
            return False

def test_multilingual_support():
    """测试多语言支持"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 测试多语言支持 ===")
            
            # 测试中文数据
            zh_data = get_all_site_info_data('zh')
            if not zh_data:
                print("✗ 无法获取中文数据")
                return False
            print(f"✓ 中文数据包含 {len(zh_data)} 个部分")
            
            # 测试英文数据
            en_data = get_all_site_info_data('en')
            if not en_data:
                print("✗ 无法获取英文数据")
                return False
            print(f"✓ 英文数据包含 {len(en_data)} 个部分")
            
            # 验证数据结构
            for section_key, section_data in zh_data.items():
                if 'section' not in section_data or 'items' not in section_data:
                    print(f"✗ 部分 {section_key} 数据结构不正确")
                    return False
                
                for item in section_data['items']:
                    if 'content' not in item:
                        print(f"✗ 信息项缺少内容数据")
                        return False
            
            print("✓ 数据结构验证通过")
            return True
            
        except Exception as e:
            print(f"✗ 多语言支持测试失败: {str(e)}")
            return False

def test_content_types():
    """测试内容类型"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 测试内容类型 ===")
            
            # 统计各种类型的数量
            type_counts = {}
            items = SiteInfoItem.query.all()
            
            for item in items:
                item_type = item.item_type
                if item_type not in type_counts:
                    type_counts[item_type] = 0
                type_counts[item_type] += 1
            
            expected_types = ['text', 'contact', 'feature', 'faq']
            for expected_type in expected_types:
                if expected_type in type_counts:
                    print(f"✓ {expected_type} 类型: {type_counts[expected_type]} 个")
                else:
                    print(f"⚠️  {expected_type} 类型: 0 个")
            
            return True
            
        except Exception as e:
            print(f"✗ 内容类型测试失败: {str(e)}")
            return False

def test_content_extraction():
    """测试内容提取"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== 测试内容提取 ===")
            
            # 测试店主信息提取
            owner_section = SiteInfoSection.query.filter(SiteInfoSection.key == 'owner_info').first()
            if owner_section:
                name_item = SiteInfoItem.query.filter(
                    SiteInfoItem.section_id == owner_section.id,
                    SiteInfoItem.key == 'name'
                ).first()
                
                if name_item:
                    content = name_item.get_content()
                    if 'value' in content and content['value']:
                        print(f"✓ 店主姓名: {content['value']}")
                    else:
                        print("✗ 店主姓名内容为空")
                        return False
                else:
                    print("✗ 找不到店主姓名项")
                    return False
            else:
                print("✗ 找不到店主信息部分")
                return False
            
            # 测试FAQ内容
            faq_section = SiteInfoSection.query.filter(SiteInfoSection.key == 'faq').first()
            if faq_section:
                faq_items = faq_section.items.filter(SiteInfoItem.item_type == 'faq').all()
                if faq_items:
                    for faq_item in faq_items:
                        content = faq_item.get_content()
                        if 'question' in content and 'answer' in content:
                            print(f"✓ FAQ: {content['question'][:30]}...")
                        else:
                            print(f"✗ FAQ项 {faq_item.key} 内容结构不正确")
                            return False
                else:
                    print("✗ FAQ部分没有问答项")
                    return False
            
            return True
            
        except Exception as e:
            print(f"✗ 内容提取测试失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("=== Sara 站点信息功能测试 ===\n")
    
    tests = [
        ("数据库结构", test_database_structure),
        ("数据完整性", test_data_integrity),
        ("多语言支持", test_multilingual_support),
        ("内容类型", test_content_types),
        ("内容提取", test_content_extraction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"正在运行: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过\n")
        else:
            print(f"❌ {test_name} 测试失败\n")
    
    print("=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！站点信息功能工作正常。")
        print("\n可以使用的功能:")
        print("  1. 后台管理: http://localhost:5000/admin/site-info")
        print("  2. 中文页面: http://localhost:5000/zh/info")
        print("  3. 英文页面: http://localhost:5000/en/info")
    else:
        print("⚠️  有测试失败，请检查问题。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)