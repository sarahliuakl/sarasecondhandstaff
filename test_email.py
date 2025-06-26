#!/usr/bin/env python3
"""
测试邮件发送功能
发送测试邮件到指定邮箱地址
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入邮件服务
from src.email_service import EmailService
import resend

def test_send_email():
    """发送测试邮件"""
    
    # 检查环境变量配置
    api_key = os.getenv('RESEND_API_KEY')
    if not api_key:
        print("❌ 错误: 未找到 RESEND_API_KEY 环境变量")
        return False
    
    print(f"✅ Resend API Key: {api_key[:8]}...")
    
    # 创建邮件服务实例
    email_service = EmailService()
    print(f"✅ 发件人邮箱: {email_service.from_email}")
    
    # 设置测试邮件参数
    test_email = "maxazure@gmail.com"
    subject = "Sara's Second-Hand 邮件服务测试"
    
    # HTML邮件内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>邮件服务测试</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                Sara's Second-Hand 邮件服务测试
            </h1>
            
            <p>您好！</p>
            <p>这是一封来自 Sara's Second-Hand 网站的测试邮件。</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">测试信息</h3>
                <p><strong>发送时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>收件人:</strong> {test_email}</p>
                <p><strong>邮件服务:</strong> Resend API</p>
                <p><strong>状态:</strong> 邮件发送功能正常工作</p>
            </div>
            
            <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0;">功能确认</h4>
                <ul>
                    <li>✅ 邮件配置正确</li>
                    <li>✅ Resend API 连接正常</li>
                    <li>✅ HTML 邮件格式支持</li>
                    <li>✅ 中文内容显示正常</li>
                </ul>
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                如果您收到这封邮件，说明邮件发送功能已成功配置！<br>
                Sara's Second-Hand 团队
            </p>
        </div>
    </body>
    </html>
    """
    
    # 纯文本邮件内容
    text_content = f"""
Sara's Second-Hand 邮件服务测试

您好！

这是一封来自 Sara's Second-Hand 网站的测试邮件。

测试信息：
- 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 收件人: {test_email}
- 邮件服务: Resend API
- 状态: 邮件发送功能正常工作

功能确认：
✅ 邮件配置正确
✅ Resend API 连接正常
✅ HTML 邮件格式支持
✅ 中文内容显示正常

如果您收到这封邮件，说明邮件发送功能已成功配置！
Sara's Second-Hand 团队
    """
    
    try:
        print(f"📧 正在发送测试邮件到: {test_email}")
        
        # 使用 Resend API 直接发送邮件
        params = {
            "from": email_service.from_email,
            "to": [test_email],
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
        
        response = resend.Emails.send(params)
        
        print(f"✅ 邮件发送成功!")
        print(f"📬 邮件ID: {response.get('id', 'N/A')}")
        print(f"🎯 收件人: {test_email}")
        print(f"📝 主题: {subject}")
        print(f"⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Sara's Second-Hand 邮件服务测试")
    print("=" * 50)
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量已加载")
    except ImportError:
        print("⚠️  python-dotenv 未安装，尝试从系统环境变量读取")
    
    # 执行测试
    success = test_send_email()
    
    print("=" * 50)
    if success:
        print("🎉 测试完成！请检查您的邮箱 maxazure@gmail.com")
    else:
        print("❌ 测试失败，请检查配置")
    print("=" * 50)