#!/usr/bin/env python3
"""
简单的邮件发送测试
直接使用 Resend API 发送测试邮件
"""
import os
import resend
from datetime import datetime
from dotenv import load_dotenv

def test_resend_api():
    """测试 Resend API 配置"""
    
    # 加载环境变量
    load_dotenv()
    
    # 获取 API 密钥
    api_key = os.getenv('RESEND_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'onboarding@resend.dev')
    
    print(f"API Key: {api_key[:8]}..." if api_key else "❌ 未找到 API Key")
    print(f"发件人: {from_email}")
    
    # 设置 Resend API 密钥
    resend.api_key = api_key
    
    # 测试邮件参数
    test_email = "maxazure@gmail.com"
    
    try:
        # 发送简单测试邮件
        params = {
            "from": from_email,
            "to": [test_email],
            "subject": "Sara's Second-Hand 邮件功能测试",
            "html": f"""
            <h1>邮件测试成功！</h1>
            <p>您好！这是来自 Sara's Second-Hand 的测试邮件。</p>
            <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>如果您收到这封邮件，说明邮件发送功能工作正常。</p>
            """,
            "text": f"""
邮件测试成功！

您好！这是来自 Sara's Second-Hand 的测试邮件。
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
如果您收到这封邮件，说明邮件发送功能工作正常。
            """
        }
        
        print(f"正在发送测试邮件到: {test_email}")
        response = resend.Emails.send(params)
        
        print("✅ 邮件发送成功!")
        print(f"邮件ID: {response.get('id', 'N/A')}")
        print(f"请检查您的邮箱: {test_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        
        # 提供调试信息
        if "API key is invalid" in str(e):
            print("\n调试建议:")
            print("1. 检查 .env 文件中的 RESEND_API_KEY 是否正确")
            print("2. 确认 Resend 账户状态是否正常")
            print("3. 检查 API 密钥是否有正确的权限")
        
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Sara's Second-Hand 简单邮件测试")
    print("=" * 50)
    
    success = test_resend_api()
    
    print("=" * 50)
    if success:
        print("🎉 测试成功！")
    else:
        print("❌ 测试失败")
    print("=" * 50)