"""
邮件服务模块
使用Resend API发送订单确认邮件和其他通知邮件
"""
import os
import resend
from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging

# 配置Resend API密钥
resend.api_key = os.getenv('RESEND_API_KEY')

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@sarasecondhand.com')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'sara@sarasecondhand.com')
    
    def send_order_confirmation(self, order) -> bool:
        """发送订单确认邮件"""
        try:
            # 解析订单商品信息
            items = json.loads(order.items) if order.items else []
            
            # 生成邮件内容
            html_content = self._generate_order_confirmation_html(order, items)
            plain_content = self._generate_order_confirmation_text(order, items)
            
            # 发送邮件
            params = {
                "from": self.from_email,
                "to": [order.customer_email],
                "subject": f"订单确认 - {order.order_number}",
                "html": html_content,
                "text": plain_content
            }
            
            email = resend.Emails.send(params)
            logger.info(f"订单确认邮件已发送: {order.order_number} -> {order.customer_email}")
            return True
            
        except Exception as e:
            logger.error(f"发送订单确认邮件失败: {order.order_number} - {str(e)}")
            return False
    
    def send_admin_notification(self, order) -> bool:
        """发送新订单通知给管理员"""
        try:
            # 解析订单商品信息
            items = json.loads(order.items) if order.items else []
            
            html_content = self._generate_admin_notification_html(order, items)
            plain_content = self._generate_admin_notification_text(order, items)
            
            params = {
                "from": self.from_email,
                "to": [self.admin_email],
                "subject": f"新订单通知 - {order.order_number}",
                "html": html_content,
                "text": plain_content
            }
            
            email = resend.Emails.send(params)
            logger.info(f"管理员通知邮件已发送: {order.order_number}")
            return True
            
        except Exception as e:
            logger.error(f"发送管理员通知邮件失败: {order.order_number} - {str(e)}")
            return False
    
    def _generate_order_confirmation_html(self, order, items) -> str:
        """生成订单确认HTML邮件内容"""
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <strong>{item['name']}</strong><br>
                    数量: {item['quantity']}<br>
                    单价: NZD ${item['price']:.2f}<br>
                    小计: NZD ${item['price'] * item['quantity']:.2f}
                </td>
            </tr>
            """
        
        # 计算邮费
        has_face_to_face_only = any(item.get('face_to_face_only', False) for item in items)
        shipping_fee = 0.00 if has_face_to_face_only else (15.00 if order.delivery_method == 'shipping' else 0.00)
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>订单确认</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                    Sara's Second-Hand 订单确认
                </h1>
                
                <p>亲爱的 {order.customer_name}，</p>
                <p>感谢您的订购！您的订单已成功提交，详情如下：</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">订单信息</h3>
                    <p><strong>订单号:</strong> {order.order_number}</p>
                    <p><strong>下单时间:</strong> {order.created_at}</p>
                    <p><strong>交付方式:</strong> {'邮寄' if order.delivery_method == 'shipping' else '当面交易'}</p>
                    <p><strong>支付方式:</strong> {order.get_payment_display()}</p>
                    {f'<p><strong>收货地址:</strong> {order.customer_address}</p>' if order.customer_address else ''}
                </div>
                
                <h3>商品明细</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    {items_html}
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 15px; border-top: 2px solid #ddd;">
                            <strong>
                                商品小计: NZD ${order.total_amount - shipping_fee:.2f}<br>
                                {f'邮费: NZD ${shipping_fee:.2f}<br>' if shipping_fee > 0 else ''}
                                总计: NZD ${order.total_amount:.2f}
                            </strong>
                        </td>
                    </tr>
                </table>
                
                {f'<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;"><p><strong>备注:</strong> {order.notes}</p></div>' if order.notes else ''}
                
                <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="margin-top: 0;">下一步</h4>
                    <p>我会在2小时内通过邮件或电话联系您确认订单详情和交付安排。</p>
                    <p>如有任何问题，请随时联系我：</p>
                    <ul>
                        <li>邮箱: {self.admin_email}</li>
                        <li>网站: <a href="https://sarasecondhand.com">sarasecondhand.com</a></li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    谢谢您选择Sara's Second-Hand！<br>
                    Sara
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_order_confirmation_text(self, order, items) -> str:
        """生成订单确认纯文本邮件内容"""
        items_text = ""
        for item in items:
            items_text += f"- {item['name']} x{item['quantity']} - NZD ${item['price'] * item['quantity']:.2f}\n"
        
        has_face_to_face_only = any(item.get('face_to_face_only', False) for item in items)
        shipping_fee = 0.00 if has_face_to_face_only else (15.00 if order.delivery_method == 'shipping' else 0.00)
        
        text_template = f"""
Sara's Second-Hand 订单确认

亲爱的 {order.customer_name}，

感谢您的订购！您的订单已成功提交，详情如下：

订单信息：
- 订单号: {order.order_number}
- 下单时间: {order.created_at}
- 交付方式: {'邮寄' if order.delivery_method == 'shipping' else '当面交易'}
- 支付方式: {order.get_payment_display()}
{f'- 收货地址: {order.customer_address}' if order.customer_address else ''}

商品明细：
{items_text}
商品小计: NZD ${order.total_amount - shipping_fee:.2f}
{f'邮费: NZD ${shipping_fee:.2f}' if shipping_fee > 0 else ''}
总计: NZD ${order.total_amount:.2f}

{f'备注: {order.notes}' if order.notes else ''}

下一步：
我会在2小时内通过邮件或电话联系您确认订单详情和交付安排。

如有任何问题，请随时联系我：
- 邮箱: {self.admin_email}
- 网站: https://sarasecondhand.com

谢谢您选择Sara's Second-Hand！
Sara
        """
        
        return text_template
    
    def _generate_admin_notification_html(self, order, items) -> str:
        """生成管理员通知HTML邮件内容"""
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">
                    {item['name']} x{item['quantity']} - NZD ${item['price'] * item['quantity']:.2f}
                    {' (仅见面交易)' if item.get('face_to_face_only', False) else ''}
                </td>
            </tr>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>新订单通知</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #dc2626;">新订单通知</h1>
                
                <div style="background: #fef2f2; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>订单 {order.order_number}</h3>
                    <p><strong>客户:</strong> {order.customer_name}</p>
                    <p><strong>邮箱:</strong> {order.customer_email}</p>
                    <p><strong>电话:</strong> {order.customer_phone or '未提供'}</p>
                    <p><strong>下单时间:</strong> {order.created_at}</p>
                    <p><strong>交付方式:</strong> {'邮寄' if order.delivery_method == 'shipping' else '当面交易'}</p>
                    <p><strong>支付方式:</strong> {order.get_payment_display()}</p>
                    {f'<p><strong>收货地址:</strong> {order.customer_address}</p>' if order.customer_address else ''}
                    <p><strong>订单总额:</strong> NZD ${order.total_amount:.2f}</p>
                </div>
                
                <h3>商品明细</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {items_html}
                </table>
                
                {f'<div style="background: #fffbeb; padding: 15px; border-radius: 5px; margin: 20px 0;"><p><strong>客户备注:</strong> {order.notes}</p></div>' if order.notes else ''}
                
                <p style="color: #dc2626; font-weight: bold;">
                    请及时联系客户确认订单详情！
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_admin_notification_text(self, order, items) -> str:
        """生成管理员通知纯文本邮件内容"""
        items_text = ""
        for item in items:
            face_to_face_note = " (仅见面交易)" if item.get('face_to_face_only', False) else ""
            items_text += f"- {item['name']} x{item['quantity']} - NZD ${item['price'] * item['quantity']:.2f}{face_to_face_note}\n"
        
        text_template = f"""
新订单通知

订单号: {order.order_number}
客户: {order.customer_name}
邮箱: {order.customer_email}
电话: {order.customer_phone or '未提供'}
下单时间: {order.created_at}
交付方式: {'邮寄' if order.delivery_method == 'shipping' else '当面交易'}
支付方式: {order.get_payment_display()}
{f'收货地址: {order.customer_address}' if order.customer_address else ''}
订单总额: NZD ${order.total_amount:.2f}

商品明细:
{items_text}

{f'客户备注: {order.notes}' if order.notes else ''}

请及时联系客户确认订单详情！
        """
        
        return text_template


# 创建全局邮件服务实例
email_service = EmailService()