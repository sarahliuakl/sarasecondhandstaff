#!/usr/bin/env python
"""
数据库连接池监控工具
用于监控和调试数据库连接池状态
"""
from app import app
from src.models import db
import time
import threading
import json
from datetime import datetime


class DatabasePoolMonitor:
    """数据库连接池监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            'pool_size': 0,
            'checked_out': 0,
            'overflow': 0,
            'checked_in': 0,
            'total_checkouts': 0,
            'total_connections': 0,
            'pool_status': 'unknown'
        }
    
    def get_pool_status(self):
        """获取连接池状态"""
        try:
            with app.app_context():
                engine = db.engine
                pool = engine.pool
                
                # 获取连接池统计信息
                self.stats.update({
                    'pool_size': pool.size(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'checked_in': pool.checkedin(),
                    'pool_status': 'healthy' if pool.checkedout() < pool.size() else 'busy',
                    'timestamp': datetime.now().isoformat()
                })
                
                return self.stats
                
        except Exception as e:
            self.stats.update({
                'error': str(e),
                'pool_status': 'error',
                'timestamp': datetime.now().isoformat()
            })
            return self.stats
    
    def start_monitoring(self, interval=5):
        """开始监控（每隔指定秒数检查一次）"""
        if self.monitoring:
            print("监控已在运行中")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                status = self.get_pool_status()
                self.log_status(status)
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print(f"数据库连接池监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        print("数据库连接池监控已停止")
    
    def log_status(self, status):
        """记录状态信息"""
        timestamp = status.get('timestamp', datetime.now().isoformat())
        pool_size = status.get('pool_size', 0)
        checked_out = status.get('checked_out', 0)
        overflow = status.get('overflow', 0)
        pool_status = status.get('pool_status', 'unknown')
        
        print(f"[{timestamp}] 连接池状态: {pool_status} | "
              f"池大小: {pool_size} | 已使用: {checked_out} | 溢出: {overflow}")
        
        if pool_status == 'busy':
            print("⚠️  警告: 连接池接近满负荷!")
        elif pool_status == 'error':
            print(f"❌ 错误: {status.get('error', '未知错误')}")
    
    def print_detailed_status(self):
        """打印详细状态"""
        status = self.get_pool_status()
        print("\n" + "="*50)
        print("数据库连接池详细状态")
        print("="*50)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        print("="*50)
    
    def test_connection_performance(self, num_tests=10):
        """测试连接性能"""
        print(f"\n开始连接性能测试 ({num_tests} 次)...")
        
        times = []
        for i in range(num_tests):
            start_time = time.time()
            try:
                with app.app_context():
                    # 执行简单查询
                    result = db.engine.execute('SELECT 1')
                    result.close()
                    
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # 转换为毫秒
                times.append(duration)
                print(f"测试 {i+1}/{num_tests}: {duration:.2f}ms")
                
            except Exception as e:
                print(f"测试 {i+1}/{num_tests}: 错误 - {str(e)}")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\n性能测试结果:")
            print(f"平均响应时间: {avg_time:.2f}ms")
            print(f"最快响应时间: {min_time:.2f}ms")
            print(f"最慢响应时间: {max_time:.2f}ms")
            
            if avg_time > 100:
                print("⚠️  平均响应时间较慢，建议检查数据库配置")
            else:
                print("✅ 响应时间良好")


def main():
    """主函数 - 命令行工具"""
    import sys
    
    monitor = DatabasePoolMonitor()
    
    if len(sys.argv) < 2:
        print("数据库连接池监控工具")
        print("用法:")
        print("  python db_monitor.py status    - 查看当前状态")
        print("  python db_monitor.py monitor   - 开始持续监控")
        print("  python db_monitor.py test      - 执行性能测试")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        monitor.print_detailed_status()
    
    elif command == 'monitor':
        try:
            monitor.start_monitoring()
            print("按 Ctrl+C 停止监控...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    elif command == 'test':
        monitor.test_connection_performance()
    
    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()