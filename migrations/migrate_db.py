#!/usr/bin/env python3
"""
数据库迁移脚本
从SQLite迁移到PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import json
from datetime import datetime

# 加载环境变量
load_dotenv()

def get_sqlite_connection():
    """获取SQLite连接"""
    db_path = os.path.join(os.path.dirname(__file__), 'sara_shop.db')
    if not os.path.exists(db_path):
        print(f"SQLite数据库文件不存在: {db_path}")
        return None
    return sqlite3.connect(db_path)

def get_postgres_connection():
    """获取PostgreSQL连接"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'sara_secondhand'),
            user=os.getenv('DB_USERNAME', 'sara_user'),
            password=os.getenv('DB_PASSWORD', 'sara123')
        )
        return conn
    except Exception as e:
        print(f"PostgreSQL连接失败: {e}")
        return None

def create_postgres_tables(pg_conn):
    """在PostgreSQL中创建表结构"""
    cursor = pg_conn.cursor()
    
    # 创建产品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            condition VARCHAR(20) NOT NULL,
            category VARCHAR(50) NOT NULL,
            stock_status VARCHAR(20) DEFAULT 'in_stock',
            face_to_face_only BOOLEAN DEFAULT FALSE,
            quantity INTEGER DEFAULT 1,
            low_stock_threshold INTEGER DEFAULT 1,
            track_inventory BOOLEAN DEFAULT FALSE,
            images TEXT,
            specifications TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            customer_name VARCHAR(100) NOT NULL,
            customer_email VARCHAR(100) NOT NULL,
            customer_phone VARCHAR(20),
            total_amount DECIMAL(10,2) NOT NULL,
            delivery_method VARCHAR(20) NOT NULL,
            payment_method VARCHAR(20) NOT NULL,
            customer_address TEXT,
            notes TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建留言表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'unread',
            reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied_at TIMESTAMP
        )
    """)
    
    # 创建管理员表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_super_admin BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(stock_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_face_to_face_only ON products(face_to_face_only)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)")
    
    pg_conn.commit()
    print("PostgreSQL表结构创建完成")

def migrate_data(sqlite_conn, pg_conn):
    """迁移数据"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # 迁移产品表
    print("迁移产品数据...")
    sqlite_cursor.execute("SELECT * FROM products")
    products = sqlite_cursor.fetchall()
    
    # 获取列名
    sqlite_cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    for product in products:
        product_dict = dict(zip(columns, product))
        
        # 处理特殊字段
        if 'face_to_face_only' not in product_dict:
            product_dict['face_to_face_only'] = False
            
        # 处理库存状态字段
        stock_status = 'sold' if bool(product_dict.get('is_sold', 0)) else 'in_stock'
        
        pg_cursor.execute("""
            INSERT INTO products (name, description, price, condition, category, stock_status, 
                               face_to_face_only, quantity, low_stock_threshold, track_inventory,
                               images, specifications, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product_dict.get('name'),
            product_dict.get('description'),
            product_dict.get('price'),
            product_dict.get('condition'),
            product_dict.get('category'),
            stock_status,
            bool(product_dict.get('face_to_face_only', 0)),
            1,  # quantity 默认值
            1,  # low_stock_threshold 默认值
            False,  # track_inventory 默认值
            product_dict.get('images'),
            product_dict.get('specifications'),
            product_dict.get('created_at'),
            product_dict.get('updated_at')
        ))
    
    print(f"已迁移 {len(products)} 个产品")
    
    # 迁移订单表
    print("迁移订单数据...")
    sqlite_cursor.execute("SELECT * FROM orders")
    orders = sqlite_cursor.fetchall()
    
    sqlite_cursor.execute("PRAGMA table_info(orders)")
    order_columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    for order in orders:
        order_dict = dict(zip(order_columns, order))
        
        pg_cursor.execute("""
            INSERT INTO orders (order_number, customer_name, customer_email, customer_phone,
                               total_amount, delivery_method, payment_method, customer_address,
                               notes, status, items, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_dict.get('order_number'),
            order_dict.get('customer_name'),
            order_dict.get('customer_email'),
            order_dict.get('customer_phone'),
            order_dict.get('total_amount'),
            order_dict.get('delivery_method'),
            order_dict.get('payment_method'),
            order_dict.get('customer_address'),
            order_dict.get('notes'),
            order_dict.get('status', 'pending'),
            order_dict.get('items'),
            order_dict.get('created_at'),
            order_dict.get('updated_at')
        ))
    
    print(f"已迁移 {len(orders)} 个订单")
    
    # 迁移留言表
    print("迁移留言数据...")
    sqlite_cursor.execute("SELECT * FROM messages")
    messages = sqlite_cursor.fetchall()
    
    sqlite_cursor.execute("PRAGMA table_info(messages)")
    message_columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    for message in messages:
        message_dict = dict(zip(message_columns, message))
        
        pg_cursor.execute("""
            INSERT INTO messages (name, contact, message, status, reply, created_at, replied_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            message_dict.get('name'),
            message_dict.get('contact'),
            message_dict.get('message'),
            message_dict.get('status', 'unread'),
            message_dict.get('reply'),
            message_dict.get('created_at'),
            message_dict.get('replied_at')
        ))
    
    print(f"已迁移 {len(messages)} 条留言")
    
    # 迁移管理员表
    print("迁移管理员数据...")
    try:
        sqlite_cursor.execute("SELECT * FROM admins")
        admins = sqlite_cursor.fetchall()
        
        sqlite_cursor.execute("PRAGMA table_info(admins)")
        admin_columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        for admin in admins:
            admin_dict = dict(zip(admin_columns, admin))
            
            # 为管理员生成默认邮箱
            email = admin_dict.get('email', f"{admin_dict.get('username')}@sarasecondhand.com")
            
            pg_cursor.execute("""
                INSERT INTO admins (username, email, password_hash, is_active, is_super_admin, 
                                  last_login, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                admin_dict.get('username'),
                email,
                admin_dict.get('password_hash'),
                bool(admin_dict.get('is_active', 1)),
                False,  # is_super_admin 默认值
                None,   # last_login
                admin_dict.get('created_at'),
                admin_dict.get('created_at')  # updated_at 使用 created_at
            ))
        
        print(f"已迁移 {len(admins)} 个管理员账户")
    except sqlite3.OperationalError:
        print("管理员表不存在，跳过迁移")
    
    pg_conn.commit()
    print("数据迁移完成")

def main():
    """主函数"""
    print("开始数据库迁移：SQLite -> PostgreSQL")
    
    # 检查环境变量
    if os.getenv('DATABASE_TYPE', 'sqlite').lower() != 'postgresql':
        print("请在.env文件中设置 DATABASE_TYPE=postgresql")
        return False
    
    # 连接数据库
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        print("无法连接到SQLite数据库")
        return False
    
    pg_conn = get_postgres_connection()
    if not pg_conn:
        print("无法连接到PostgreSQL数据库")
        return False
    
    try:
        # 创建PostgreSQL表结构
        create_postgres_tables(pg_conn)
        
        # 迁移数据
        migrate_data(sqlite_conn, pg_conn)
        
        print("数据库迁移成功完成！")
        print("请更新.env文件中的DATABASE_TYPE=postgresql")
        return True
        
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        pg_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)