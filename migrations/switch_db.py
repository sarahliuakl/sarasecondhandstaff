#!/usr/bin/env python3
"""
数据库切换脚本
在SQLite和PostgreSQL之间切换
"""

import os
import sys
from dotenv import load_dotenv, set_key

def switch_to_sqlite():
    """切换到SQLite数据库"""
    env_file = '.env'
    if os.path.exists(env_file):
        set_key(env_file, 'DATABASE_TYPE', 'sqlite')
        print("已切换到SQLite数据库")
        print("重启应用后生效")
    else:
        print("未找到.env文件")

def switch_to_postgresql():
    """切换到PostgreSQL数据库"""
    env_file = '.env'
    if os.path.exists(env_file):
        set_key(env_file, 'DATABASE_TYPE', 'postgresql')
        print("已切换到PostgreSQL数据库")
        print("请确保PostgreSQL服务正在运行且配置正确")
        print("重启应用后生效")
    else:
        print("未找到.env文件")

def show_current_config():
    """显示当前数据库配置"""
    load_dotenv()
    db_type = os.getenv('DATABASE_TYPE', 'sqlite')
    print(f"当前数据库类型: {db_type}")
    
    if db_type == 'postgresql':
        print(f"  主机: {os.getenv('DB_HOST', 'localhost')}")
        print(f"  端口: {os.getenv('DB_PORT', '5432')}")
        print(f"  数据库: {os.getenv('DB_NAME', 'sara_secondhand')}")
        print(f"  用户: {os.getenv('DB_USERNAME', 'sara_user')}")
    else:
        print("  文件: sara_shop.db")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python switch_db.py sqlite     # 切换到SQLite")
        print("  python switch_db.py postgres   # 切换到PostgreSQL")
        print("  python switch_db.py status     # 显示当前配置")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'sqlite':
        switch_to_sqlite()
    elif command in ['postgres', 'postgresql']:
        switch_to_postgresql()
    elif command == 'status':
        show_current_config()
    else:
        print(f"未知命令: {command}")
        print("支持的命令: sqlite, postgres, status")

if __name__ == "__main__":
    main()