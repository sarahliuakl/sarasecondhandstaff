"""
Sara二手售卖网站 - 库存管理数据库迁移
添加产品库存数量字段，实现精确库存管理
"""

import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_inventory_fields():
    """添加库存相关字段到产品表"""
    
    # 获取数据库路径
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'sara_shop.db')
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fields_to_add = []
        
        if 'quantity' not in columns:
            fields_to_add.append(('quantity', 'INTEGER DEFAULT 1'))
        
        if 'low_stock_threshold' not in columns:
            fields_to_add.append(('low_stock_threshold', 'INTEGER DEFAULT 1'))
        
        if 'track_inventory' not in columns:
            fields_to_add.append(('track_inventory', 'BOOLEAN DEFAULT 1'))
        
        # 添加新字段
        for field_name, field_definition in fields_to_add:
            try:
                alter_sql = f"ALTER TABLE products ADD COLUMN {field_name} {field_definition}"
                cursor.execute(alter_sql)
                logger.info(f"成功添加字段: {field_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"字段已存在，跳过: {field_name}")
                else:
                    raise e
        
        # 更新现有产品的库存数量
        # 根据stock_status设置初始库存
        update_sql = """
        UPDATE products 
        SET quantity = CASE 
            WHEN stock_status = 'available' THEN 1
            WHEN stock_status = 'sold' THEN 0
            WHEN stock_status = 'reserved' THEN 1
            ELSE 1
        END
        WHERE quantity IS NULL
        """
        cursor.execute(update_sql)
        
        # 提交更改
        conn.commit()
        logger.info("库存字段迁移完成")
        
        # 显示更新后的表结构
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        logger.info("更新后的products表结构:")
        for column in columns:
            logger.info(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'} {'DEFAULT ' + str(column[4]) if column[4] else ''}")
        
        # 显示库存统计
        cursor.execute("""
        SELECT 
            stock_status,
            COUNT(*) as count,
            AVG(quantity) as avg_quantity
        FROM products 
        GROUP BY stock_status
        """)
        stats = cursor.fetchall()
        logger.info("\n库存统计:")
        for stat in stats:
            logger.info(f"  {stat[0]}: {stat[1]}个产品，平均库存: {stat[2]:.1f}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("开始库存管理数据库迁移...")
    success = add_inventory_fields()
    
    if success:
        print("✅ 库存管理迁移成功完成！")
        print("\n新增功能:")
        print("- quantity: 产品库存数量")
        print("- low_stock_threshold: 低库存警告阈值")
        print("- track_inventory: 是否启用库存跟踪")
        print("\n管理员现在可以:")
        print("- 精确管理产品库存数量")
        print("- 设置低库存警告阈值")
        print("- 订单完成后自动扣减库存")
        print("- 查看库存不足的产品提醒")
    else:
        print("❌ 迁移失败，请检查日志并重试")