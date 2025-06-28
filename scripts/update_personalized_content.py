#!/usr/bin/env python3
"""
个性化内容更新脚本
为Sara的二手商店更新个人化、真实的内容
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask
from models import db, SiteInfoSection, SiteInfoItem, SiteInfoTranslation
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

def update_owner_info():
    """更新店主信息 - 个人化故事"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取店主信息部分
            section = SiteInfoSection.query.filter_by(key='owner_info').first()
            if not section:
                print("未找到店主信息部分")
                return False
            
            # 更新介绍内容
            intro_item = SiteInfoItem.query.filter_by(section_id=section.id, key='introduction').first()
            if intro_item:
                # 中文个人故事
                intro_item.set_content({
                    'value': '👋 大家好，我是Sara！奥克兰大学CS专业学生，住在North Shore。和很多科技爱好者一样，这些年积累了太多设备了！📱💻\n\n2025年的新品实在太诱人（新MacBook、新手机...），我决定理性断舍离。所有商品都是个人使用，精心保养，诚实描述。\n\n这不是生意，是我为优质电子产品寻找新主人的方式，同时帮助同学们省钱。每台设备都曾是我的日常伙伴，所以我了解它们的优缺点。'
                })
                
                # 更新英文翻译
                en_translation = SiteInfoTranslation.query.filter_by(
                    item_id=intro_item.id, language='en'
                ).first()
                if en_translation:
                    en_translation.set_content({
                        'value': '👋 Hi, I\'m Sara! CS student at Auckland University, living on North Shore. Like many tech enthusiasts, I\'ve accumulated way too many gadgets over the years! 📱💻\n\nWith 2025\'s amazing new releases (looking at you, new MacBooks and phones!), I\'ve decided to declutter responsibly. All items are personally owned, carefully maintained, and honestly described.\n\nThis isn\'t a business - it\'s my way of finding good homes for quality tech while helping fellow students save money. Every device has been my daily companion, so I know their quirks and strengths inside out.'
                    })
            
            db.session.commit()
            print("✓ 店主信息更新完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 更新店主信息失败: {str(e)}")
            return False

def update_policies():
    """更新法律政策 - 个人销售者角度"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取政策部分
            section = SiteInfoSection.query.filter_by(key='policies').first()
            if not section:
                print("未找到政策部分")
                return False
            
            # 清空现有政策项目和翻译
            items = SiteInfoItem.query.filter_by(section_id=section.id).all()
            for item in items:
                SiteInfoTranslation.query.filter_by(item_id=item.id).delete()
            SiteInfoItem.query.filter_by(section_id=section.id).delete()
            
            # 添加新的个人销售政策
            policies = [
                {
                    'key': 'private_seller_status',
                    'item_type': 'text',
                    'content_zh': {
                        'value': '🏠 个人卖家身份\n作为个人出售闲置物品（非商业经营），我遵循新西兰个人销售法规。虽然消费者保障法对个人销售保护有限，但我承诺：\n• 所有物品诚实准确描述\n• 明确披露任何已知问题或磨损\n• 照片和规格真实呈现'
                    },
                    'content_en': {
                        'value': '🏠 Private Seller Status\nAs an individual selling personal items (not a business), I operate under New Zealand\'s private sale regulations. While Consumer Guarantees Act protections are limited for private sales, I commit to:\n• Honest and accurate descriptions of all items\n• Clear disclosure of any known issues or wear\n• Fair representation in photos and specifications'
                    }
                },
                {
                    'key': 'buyer_rights',
                    'item_type': 'text',
                    'content_zh': {
                        'value': '📋 您的权利\n• 物品必须与描述相符\n• 有权在购买前检查物品（奥克兰地区）\n• 仅针对描述不符的物品享有明确退货政策'
                    },
                    'content_en': {
                        'value': '📋 Your Rights\n• Items must match the description provided\n• Right to inspect items before purchase (Auckland area)\n• Clear return policy for misrepresented items only'
                    }
                },
                {
                    'key': 'my_commitments',
                    'item_type': 'text',
                    'content_zh': {
                        'value': '🛡️ 我的承诺\n• 48小时内退货窗口（如物品与描述不符）\n• 透明沟通设备使用历史\n• 无隐藏缺陷 - 所见即所得\n• 2小时内回复，学生友好的交易时间'
                    },
                    'content_en': {
                        'value': '🛡️ My Commitments\n• 48-hour return window if item doesn\'t match description\n• Transparent communication about device history\n• No hidden defects - what you see is what you get\n• 2-hour response during student-friendly hours'
                    }
                }
            ]
            
            for policy_data in policies:
                # 创建项目
                item = SiteInfoItem(
                    section_id=section.id,
                    key=policy_data['key'],
                    item_type=policy_data['item_type']
                )
                item.set_content(policy_data['content_zh'])
                db.session.add(item)
                db.session.flush()  # 获取ID
                
                # 添加英文翻译
                translation = SiteInfoTranslation(
                    item_id=item.id,
                    language='en'
                )
                translation.set_content(policy_data['content_en'])
                db.session.add(translation)
            
            db.session.commit()
            print("✓ 政策内容更新完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 更新政策内容失败: {str(e)}")
            return False

def update_faq():
    """更新FAQ - 学生视角的真实问题"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取FAQ部分
            section = SiteInfoSection.query.filter_by(key='faq').first()
            if not section:
                print("未找到FAQ部分")
                return False
            
            # 清空现有FAQ和翻译
            items = SiteInfoItem.query.filter_by(section_id=section.id).all()
            for item in items:
                SiteInfoTranslation.query.filter_by(item_id=item.id).delete()
            SiteInfoItem.query.filter_by(section_id=section.id).delete()
            
            # 添加新的学生友好FAQ
            faqs = [
                {
                    'key': 'why_selling',
                    'question_zh': '为什么要出售这些设备？',
                    'answer_zh': '新年新装备！为2025年的新品发布腾出空间，同时理性回血。作为CS学生，我对新技术充满热情，但也要现实考虑经济因素。',
                    'question_en': 'Why are you selling these items?',
                    'answer_en': 'New year, new tech! Making room for 2025 releases and funding upgrades responsibly. As a CS student, I\'m passionate about new tech but need to be realistic about finances.'
                },
                {
                    'key': 'condition_rating',
                    'question_zh': '如何判断设备成色？',
                    'answer_zh': '我会诚实评估使用情况：优秀（几乎全新）、良好（轻微使用痕迹）、一般（有使用痕迹但功能完好）。每台设备都有详细照片和使用历史。',
                    'question_en': 'How do you determine condition ratings?',
                    'answer_en': 'I rate honestly based on actual use: Excellent (like new), Good (minor wear), Fair (visible use but fully functional). Every device comes with detailed photos and usage history.'
                },
                {
                    'key': 'testing_items',
                    'question_zh': '可以当面测试设备吗？',
                    'answer_zh': '当然可以！奥克兰的买家欢迎来检查和测试所有功能。我还可以展示我的使用习惯和设备表现。咖啡我请！☕',
                    'question_en': 'Can I test items before buying?',
                    'answer_en': 'Absolutely! Auckland buyers welcome to inspect and test everything. I\'ll even show you my usage patterns and device performance. Coffee\'s on me! ☕'
                },
                {
                    'key': 'student_trust',
                    'question_zh': '为什么相信学生卖家？',
                    'answer_zh': '看看我的详细照片、诚实描述和使用心得。我在建立声誉，为将来的销售打基础。同学之间，更注重信任而非利润。',
                    'question_en': 'Why should I trust a student seller?',
                    'answer_en': 'Check my detailed photos, honest descriptions, and genuine usage insights. I\'m building reputation for future sales. Student-to-student means trust over profit.'
                },
                {
                    'key': 'tech_enthusiasm',
                    'question_zh': '你真的了解这些设备吗？',
                    'answer_zh': '作为CS学生和科技爱好者，我对每台设备的性能、优缺点都很了解。买前我会详细介绍，买后有问题也可以随时咨询技术细节。',
                    'question_en': 'Do you really know these devices?',
                    'answer_en': 'As a CS student and tech enthusiast, I know each device\'s performance, strengths, and limitations. I\'ll explain everything before purchase and help with tech questions afterward.'
                }
            ]
            
            for faq_data in faqs:
                # 创建FAQ项目
                item = SiteInfoItem(
                    section_id=section.id,
                    key=faq_data['key'],
                    item_type='faq'
                )
                item.set_content({
                    'question': faq_data['question_zh'],
                    'answer': faq_data['answer_zh']
                })
                db.session.add(item)
                db.session.flush()
                
                # 添加英文翻译
                translation = SiteInfoTranslation(
                    item_id=item.id,
                    language='en'
                )
                translation.set_content({
                    'question': faq_data['question_en'],
                    'answer': faq_data['answer_en']
                })
                db.session.add(translation)
            
            db.session.commit()
            print("✓ FAQ内容更新完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 更新FAQ内容失败: {str(e)}")
            return False

def update_contact_info():
    """更新联系信息 - 学生友好的时间和方式"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取联系信息部分
            section = SiteInfoSection.query.filter_by(key='contact_info').first()
            if not section:
                print("未找到联系信息部分")
                return False
            
            # 更新现有联系信息
            items_to_update = [
                {
                    'key': 'working_hours',
                    'content_zh': {'label': '最佳联系时间', 'value': '平日：下午4-9点（课后）| 周末：上午10点-晚8点'},
                    'content_en': {'label': 'Best Contact Hours', 'value': 'Weekdays: 4pm-9pm (after classes) | Weekends: 10am-8pm'}
                },
                {
                    'key': 'response_time',
                    'content_zh': {'label': '回复保证', 'value': '上述时间内2小时内必回复'},
                    'content_en': {'label': 'Response Guarantee', 'value': 'Reply within 2 hours during above times'}
                },
                {
                    'key': 'meetup_preference',
                    'content_zh': {'label': '见面偏好', 'value': '大学、咖啡厅或公共场所，我带设备历史，你带好奇心！'},
                    'content_en': {'label': 'Meetup Preference', 'value': 'University, cafes, or public spaces. I bring device history, you bring curiosity!'}
                }
            ]
            
            for item_data in items_to_update:
                item = SiteInfoItem.query.filter_by(
                    section_id=section.id, 
                    key=item_data['key']
                ).first()
                
                if item:
                    item.set_content(item_data['content_zh'])
                    
                    # 更新英文翻译
                    en_translation = SiteInfoTranslation.query.filter_by(
                        item_id=item.id, language='en'
                    ).first()
                    if en_translation:
                        en_translation.set_content(item_data['content_en'])
                else:
                    # 创建新项目（如果不存在）
                    new_item = SiteInfoItem(
                        section_id=section.id,
                        key=item_data['key'],
                        item_type='contact'
                    )
                    new_item.set_content(item_data['content_zh'])
                    db.session.add(new_item)
                    db.session.flush()
                    
                    # 添加英文翻译
                    translation = SiteInfoTranslation(
                        item_id=new_item.id,
                        language='en'
                    )
                    translation.set_content(item_data['content_en'])
                    db.session.add(translation)
            
            db.session.commit()
            print("✓ 联系信息更新完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 更新联系信息失败: {str(e)}")
            return False

def add_trust_building_section():
    """添加信任建立部分"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查是否已存在
            existing_section = SiteInfoSection.query.filter_by(key='trust_building').first()
            if existing_section:
                print("信任建立部分已存在，跳过创建")
                return True
            
            # 创建新部分
            section = SiteInfoSection(
                key='trust_building',
                name='信任保障',
                icon='🌟',
                sort_order=15,
                is_active=True
            )
            db.session.add(section)
            db.session.flush()
            
            # 添加信任要素
            trust_items = [
                {
                    'key': 'authentic_voice',
                    'item_type': 'feature',
                    'content_zh': {
                        'title': '真实用户体验',
                        'description': '学生视角，非销售话术',
                        'icon': '🎯'
                    },
                    'content_en': {
                        'title': 'Real User Perspective',
                        'description': 'Student-to-student, not sales pitch',
                        'icon': '🎯'
                    }
                },
                {
                    'key': 'community_feel',
                    'item_type': 'feature',
                    'content_zh': {
                        'title': '科技爱好者社群',
                        'description': '与买家分享技术热情',
                        'icon': '💻'
                    },
                    'content_en': {
                        'title': 'Tech Enthusiast Community',
                        'description': 'Sharing tech passion with buyers',
                        'icon': '💻'
                    }
                },
                {
                    'key': 'student_friendly',
                    'item_type': 'feature',
                    'content_zh': {
                        'title': '学生友好',
                        'description': '合理价格 + 灵活时间',
                        'icon': '🎓'
                    },
                    'content_en': {
                        'title': 'Student-Friendly',
                        'description': 'Fair pricing + flexible timing',
                        'icon': '🎓'
                    }
                }
            ]
            
            for trust_data in trust_items:
                item = SiteInfoItem(
                    section_id=section.id,
                    key=trust_data['key'],
                    item_type=trust_data['item_type']
                )
                item.set_content(trust_data['content_zh'])
                db.session.add(item)
                db.session.flush()
                
                # 添加英文翻译
                translation = SiteInfoTranslation(
                    item_id=item.id,
                    language='en'
                )
                translation.set_content(trust_data['content_en'])
                db.session.add(translation)
            
            # 注意：SiteInfoTranslation只能关联item，不能直接关联section
            # 部分翻译需要通过其他方式处理或在模板中硬编码
            
            db.session.commit()
            print("✓ 信任建立部分添加完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 添加信任建立部分失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("=== Sara个性化内容更新脚本 ===\n")
    
    updates = [
        ("更新店主个人故事", update_owner_info),
        ("更新法律政策内容", update_policies), 
        ("更新FAQ问答", update_faq),
        ("更新联系信息", update_contact_info),
        ("添加信任建立要素", add_trust_building_section)
    ]
    
    success_count = 0
    for description, update_func in updates:
        print(f"正在{description}...")
        if update_func():
            success_count += 1
        print()
    
    print(f"🎉 更新完成！成功更新 {success_count}/{len(updates)} 个部分")
    print("现在访问 /zh/info 或 /en/info 查看个性化内容")

if __name__ == "__main__":
    main()