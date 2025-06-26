#!/usr/bin/env python3
"""
发送测试邮件到管理员邮箱
由于 Resend 测试限制，只能发送到注册邮箱
"""
import os
import resend
from datetime import datetime
from dotenv import load_dotenv

def test_admin_email():
    """发送测试邮件到管理员邮箱"""
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    api_key = os.getenv('RESEND_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'onboarding@resend.dev')
    admin_email = os.getenv('ADMIN_EMAIL', 'sarahliu.akl@gmail.com')
    
    print(f"API Key: {api_key[:8]}..." if api_key else "❌ 未找到 API Key")
    print(f"发件人: {from_email}")
    print(f"管理员邮箱: {admin_email}")
    
    # 设置 Resend API 密钥
    resend.api_key = api_key
    
    try:
        # 发送测试邮件到管理员邮箱
        params = {
            "from": from_email,
            "to": [admin_email],
            "subject": "Sara's Second-Hand 邮件功能测试成功",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>邮件功能测试</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2563eb;">✅ Sara's Second-Hand 邮件功能测试成功</h1>
                    
                    <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>测试结果</h3>
                        <p>✅ 邮件服务配置正确</p>
                        <p>✅ Resend API 连接正常</p>
                        <p>✅ 邮件发送功能工作正常</p>
                        <p>✅ HTML 格式邮件支持</p>
                        <p>✅ 中文内容显示正常</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>测试信息</h3>
                        <p><strong>测试时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>发送方式:</strong> Resend API</p>
                        <p><strong>发件人:</strong> {from_email}</p>
                        <p><strong>收件人:</strong> {admin_email}</p>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>重要提醒</h3>
                        <p>由于使用的是 Resend 测试模式，目前只能发送邮件到注册的邮箱地址。</p>
                        <p>如需发送邮件到其他地址，需要在 resend.com/domains 验证域名。</p>
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>下一步建议</h3>
                        <ul>
                            <li>验证自定义域名以发送邮件到任意地址</li>
                            <li>测试订单确认邮件功能</li>
                            <li>测试管理员通知邮件功能</li>
                            <li>配置邮件队列监控</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        测试完成！邮件发送功能已验证正常工作。<br>
                        Sara's Second-Hand 开发团队
                    </p>
                </div>
            </body>
            </html>
            """,
            "text": f"""
Sara's Second-Hand 邮件功能测试成功

测试结果:
✅ 邮件服务配置正确
✅ Resend API 连接正常  
✅ 邮件发送功能工作正常
✅ HTML 格式邮件支持
✅ 中文内容显示正常

测试信息:
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 发送方式: Resend API
- 发件人: {from_email}
- 收件人: {admin_email}

重要提醒:
由于使用的是 Resend 测试模式，目前只能发送邮件到注册的邮箱地址。
如需发送邮件到其他地址，需要在 resend.com/domains 验证域名。

下一步建议:
- 验证自定义域名以发送邮件到任意地址
- 测试订单确认邮件功能  
- 测试管理员通知邮件功能
- 配置邮件队列监控

测试完成！邮件发送功能已验证正常工作。
Sara's Second-Hand 开发团队
            """
        }
        
        print(f"正在发送测试邮件到: {admin_email}")
        response = resend.Emails.send(params)
        
        print("✅ 邮件发送成功!")
        print(f"📬 邮件ID: {response.get('id', 'N/A')}")
        print(f"🎯 收件人: {admin_email}")
        print(f"⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 额外信息
        print("\n📝 重要提醒:")
        print("- 由于 Resend 测试模式限制，目前只能发送到注册邮箱")
        print("- 要发送到 maxazure@gmail.com，需要验证自定义域名")
        print("- 可以在 resend.com/domains 配置域名验证")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Sara's Second-Hand 管理员邮件测试")
    print("=" * 60)
    
    success = test_admin_email()
    
    print("=" * 60)
    if success:
        print("🎉 测试成功！请检查管理员邮箱")
    else:
        print("❌ 测试失败")
    print("=" * 60)