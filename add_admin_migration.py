#!/usr/bin/env python3
"""
Sara二手售卖网站 - 管理员和网站设置表迁移
添加admins和site_settings表
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def run_migration():
    """运行数据库迁移"""
    
    # 数据库文件路径
    db_path = 'sara_shop.db'
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，请先运行 init_db.py")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始添加管理员和网站设置表...")
        
        # 创建管理员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_super_admin BOOLEAN DEFAULT 0,
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建网站设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_site_settings_key ON site_settings(key)')
        
        # 检查是否已存在管理员
        cursor.execute('SELECT COUNT(*) FROM admins')
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # 创建默认管理员账户
            default_password = 'admin123'  # 生产环境需要修改
            password_hash = generate_password_hash(default_password)
            
            cursor.execute('''
                INSERT INTO admins (username, email, password_hash, is_super_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@sarasecondhand.com', password_hash, True))
            
            print(f"✅ 创建默认管理员账户:")
            print(f"   用户名: admin")
            print(f"   邮箱: admin@sarasecondhand.com")
            print(f"   密码: {default_password}")
            print(f"   ⚠️  请登录后立即修改密码！")
        
        # 检查并添加默认网站设置
        default_settings = [
            ('site_name', 'Sara二手商店', '网站名称'),
            ('site_description', '新西兰优质二手商品交易平台', '网站描述'),
            ('contact_email', 'sara@sarasecondhand.com', '联系邮箱'),
            ('contact_phone', '+64 21 123 4567', '联系电话')
        ]
        
        for key, value, description in default_settings:
            cursor.execute('SELECT COUNT(*) FROM site_settings WHERE key = ?', (key,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO site_settings (key, value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, description))
        
        conn.commit()
        print("✅ 管理员和网站设置表迁移完成！")
        
        # 显示表结构信息
        cursor.execute("PRAGMA table_info(admins)")
        admin_columns = cursor.fetchall()
        print(f"\n📋 admins表结构 ({len(admin_columns)}列):")
        for col in admin_columns:
            print(f"   {col[1]} ({col[2]})")
        
        cursor.execute("PRAGMA table_info(site_settings)")
        settings_columns = cursor.fetchall()
        print(f"\n📋 site_settings表结构 ({len(settings_columns)}列):")
        for col in settings_columns:
            print(f"   {col[1]} ({col[2]})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Sara二手售卖网站 - 管理员功能迁移")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n🎉 迁移成功完成！")
        print("\n接下来您可以:")
        print("1. 访问 /admin/login 登录管理后台")
        print("2. 使用默认账户登录后立即修改密码")
        print("3. 在网站设置中配置您的信息")
    else:
        print("\n💥 迁移失败，请检查错误信息")