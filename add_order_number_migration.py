"""
数据库迁移脚本 - 添加订单号字段
为现有的orders表添加order_number字段，并为现有订单生成订单号
"""
import os
import sys
import sqlite3
import uuid
import time
from datetime import datetime

def generate_order_number():
    """生成唯一订单号"""
    timestamp = str(int(time.time()))[-8:]  # 取时间戳后8位
    random_part = str(uuid.uuid4())[:4].upper()  # 取UUID前4位并转大写
    return f"SR{timestamp}{random_part}"

def migrate_database():
    """执行数据库迁移"""
    db_path = 'sara_shop.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，无需迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查order_number字段是否已存在
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'order_number' in columns:
            print("order_number字段已存在，无需迁移")
            conn.close()
            return
        
        print("开始添加order_number字段...")
        
        # 1. 添加order_number字段（允许为空）
        cursor.execute("ALTER TABLE orders ADD COLUMN order_number TEXT")
        
        # 2. 为现有订单生成订单号
        cursor.execute("SELECT id FROM orders WHERE order_number IS NULL")
        orders_without_number = cursor.fetchall()
        
        for (order_id,) in orders_without_number:
            order_number = generate_order_number()
            # 确保订单号唯一
            while True:
                cursor.execute("SELECT id FROM orders WHERE order_number = ?", (order_number,))
                if cursor.fetchone() is None:
                    break
                order_number = generate_order_number()
            
            cursor.execute("UPDATE orders SET order_number = ? WHERE id = ?", (order_number, order_id))
            print(f"为订单 {order_id} 生成订单号: {order_number}")
        
        # 3. 创建唯一索引
        cursor.execute("CREATE UNIQUE INDEX idx_orders_order_number ON orders(order_number)")
        
        conn.commit()
        print(f"迁移完成！为 {len(orders_without_number)} 个订单生成了订单号")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()