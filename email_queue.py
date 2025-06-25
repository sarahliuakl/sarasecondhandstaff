"""
邮件队列系统
提供邮件队列和异步发送功能
"""
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from email_service import email_service
import logging

logger = logging.getLogger(__name__)

class EmailQueue:
    """邮件队列管理器"""
    
    def __init__(self, db_path='email_queue.db', app=None):
        self.db_path = db_path
        self.app = app
        self.init_database()
        self._running = False
        self._worker_thread = None
    
    def init_database(self):
        """初始化邮件队列数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_type TEXT NOT NULL,
                recipient TEXT NOT NULL, 
                subject TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP NULL,
                error_message TEXT NULL
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_queue_scheduled ON email_queue(scheduled_at)')
        
        conn.commit()
        conn.close()
    
    def add_order_confirmation_email(self, order, delay_seconds=0):
        """添加订单确认邮件到队列"""
        scheduled_at = datetime.now() + timedelta(seconds=delay_seconds)
        
        email_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'customer_email': order.customer_email,
            'customer_name': order.customer_name
        }
        
        self._add_to_queue(
            email_type='order_confirmation',
            recipient=order.customer_email,
            subject=f'订单确认 - {order.order_number}',
            data=json.dumps(email_data),
            scheduled_at=scheduled_at
        )
        
        logger.info(f"订单确认邮件已添加到队列: {order.order_number}")
    
    def add_admin_notification_email(self, order, delay_seconds=0):
        """添加管理员通知邮件到队列"""
        scheduled_at = datetime.now() + timedelta(seconds=delay_seconds)
        
        email_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'admin_email': os.getenv('ADMIN_EMAIL', 'sara@sarasecondhand.com')
        }
        
        self._add_to_queue(
            email_type='admin_notification',
            recipient=os.getenv('ADMIN_EMAIL', 'sara@sarasecondhand.com'),
            subject=f'新订单通知 - {order.order_number}',
            data=json.dumps(email_data),
            scheduled_at=scheduled_at
        )
        
        logger.info(f"管理员通知邮件已添加到队列: {order.order_number}")
    
    def _add_to_queue(self, email_type, recipient, subject, data, scheduled_at=None):
        """添加邮件到队列"""
        if scheduled_at is None:
            scheduled_at = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_queue 
            (email_type, recipient, subject, data, scheduled_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (email_type, recipient, subject, data, scheduled_at))
        
        conn.commit()
        conn.close()
    
    def start_worker(self):
        """启动邮件队列工作线程"""
        if self._running:
            logger.warning("邮件队列工作线程已经在运行")
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("邮件队列工作线程已启动")
    
    def stop_worker(self):
        """停止邮件队列工作线程"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=10)
        logger.info("邮件队列工作线程已停止")
    
    def _worker_loop(self):
        """邮件队列工作循环"""
        while self._running:
            try:
                self._process_pending_emails()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"邮件队列工作线程错误: {str(e)}")
                time.sleep(60)  # 发生错误时等待更长时间
    
    def _process_pending_emails(self):
        """处理待发送的邮件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取到期的待发送邮件
        cursor.execute('''
            SELECT id, email_type, recipient, subject, data, attempts, max_attempts
            FROM email_queue 
            WHERE status = 'pending' 
            AND scheduled_at <= CURRENT_TIMESTAMP
            AND attempts < max_attempts
            ORDER BY scheduled_at ASC
            LIMIT 10
        ''')
        
        emails = cursor.fetchall()
        conn.close()
        
        for email in emails:
            email_id, email_type, recipient, subject, data, attempts, max_attempts = email
            
            try:
                # 发送邮件
                success = self._send_email(email_type, json.loads(data))
                
                if success:
                    self._mark_email_sent(email_id)
                    logger.info(f"邮件发送成功: ID {email_id}, 类型 {email_type}, 收件人 {recipient}")
                else:
                    self._mark_email_failed(email_id, attempts + 1, "发送失败")
                    logger.warning(f"邮件发送失败: ID {email_id}, 尝试次数 {attempts + 1}")
                
            except Exception as e:
                error_msg = str(e)
                self._mark_email_failed(email_id, attempts + 1, error_msg)
                logger.error(f"邮件发送异常: ID {email_id}, 错误: {error_msg}")
    
    def _send_email(self, email_type, data):
        """发送特定类型的邮件"""
        try:
            if not self.app:
                logger.error("Flask应用未设置，无法发送邮件")
                return False
            
            # 在应用上下文中执行数据库查询
            from models import Order
            
            with self.app.app_context():
                if email_type == 'order_confirmation':
                    order = Order.query.get(data['order_id'])
                    if order:
                        return email_service.send_order_confirmation(order)
                elif email_type == 'admin_notification':
                    order = Order.query.get(data['order_id'])
                    if order:
                        return email_service.send_admin_notification(order)
            
            return False
        except Exception as e:
            logger.error(f"发送邮件时出错: {str(e)}")
            return False
    
    def _mark_email_sent(self, email_id):
        """标记邮件为已发送"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE email_queue 
            SET status = 'sent', sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (email_id,))
        
        conn.commit()
        conn.close()
    
    def _mark_email_failed(self, email_id, attempts, error_message):
        """标记邮件发送失败"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 如果达到最大尝试次数，标记为失败
        status = 'failed' if attempts >= 3 else 'pending'
        
        cursor.execute('''
            UPDATE email_queue 
            SET attempts = ?, error_message = ?, status = ?
            WHERE id = ?
        ''', (attempts, error_message, status, email_id))
        
        conn.commit()
        conn.close()
    
    def get_queue_status(self):
        """获取队列状态统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM email_queue 
            GROUP BY status
        ''')
        
        status_counts = dict(cursor.fetchall())
        conn.close()
        
        return {
            'pending': status_counts.get('pending', 0),
            'sent': status_counts.get('sent', 0),
            'failed': status_counts.get('failed', 0),
            'total': sum(status_counts.values())
        }
    
    def cleanup_old_emails(self, days=30):
        """清理旧的邮件记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM email_queue 
            WHERE status = 'sent' 
            AND sent_at < ?
        ''', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"清理了 {deleted_count} 条旧邮件记录")
        return deleted_count

# 创建全局邮件队列实例（稍后在app.py中设置应用实例）
email_queue = EmailQueue()