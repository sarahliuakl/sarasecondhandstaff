import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-change-in-production')
    
    # 数据库配置 - 根据环境变量选择数据库类型
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    
    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    def __init__(self):
        """初始化配置时设置数据库URI和连接池"""
        if self.DATABASE_TYPE == 'postgresql':
            # PostgreSQL配置
            username = os.getenv('DB_USERNAME', 'sara_user')
            password = os.getenv('DB_PASSWORD', 'sara123')
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'sara_secondhand')
            
            self.SQLALCHEMY_DATABASE_URI = f'postgresql://{username}:{password}@{host}:{port}/{database}'
            
            # PostgreSQL连接池配置
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),  # 连接池大小
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),  # 获取连接超时时间（秒）
                'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),  # 连接回收时间（秒）
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),  # 最大溢出连接数
                'pool_pre_ping': True,  # 连接前检测连接有效性
                'echo': False,  # 在开发环境可设为True查看SQL
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'Sara_SecondHand_Shop'
                }
            }
        else:
            # SQLite配置（默认）
            basedir = os.path.abspath(os.path.dirname(__file__))
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
            
            # SQLite连接池配置（相对简单）
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_timeout': 20,
                'pool_recycle': 300,
                'pool_pre_ping': True,
                'connect_args': {
                    'timeout': 20,
                    'check_same_thread': False  # SQLite特定配置
                }
            }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    def __init__(self):
        """开发环境特定初始化"""
        super().__init__()
        
        # 开发环境启用SQL调试（如果需要）
        if os.getenv('SQL_DEBUG', 'false').lower() == 'true':
            if hasattr(self, 'SQLALCHEMY_ENGINE_OPTIONS'):
                self.SQLALCHEMY_ENGINE_OPTIONS['echo'] = True
            else:
                self.SQLALCHEMY_ENGINE_OPTIONS = {'echo': True}
        
        # 开发环境可以使用更小的连接池
        if hasattr(self, 'SQLALCHEMY_ENGINE_OPTIONS') and 'pool_size' in self.SQLALCHEMY_ENGINE_OPTIONS:
            self.SQLALCHEMY_ENGINE_OPTIONS['pool_size'] = int(os.getenv('DEV_DB_POOL_SIZE', '5'))

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    def __init__(self):
        """生产环境默认使用PostgreSQL，优化连接池配置"""
        database_type = os.getenv('DATABASE_TYPE', 'postgresql').lower()
        
        if database_type == 'postgresql':
            username = os.getenv('DB_USERNAME', 'sara_user')
            password = os.getenv('DB_PASSWORD')
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'sara_secondhand')
            
            if not password:
                raise ValueError("生产环境必须设置DB_PASSWORD环境变量")
            
            self.SQLALCHEMY_DATABASE_URI = f'postgresql://{username}:{password}@{host}:{port}/{database}'
            
            # 生产环境优化的PostgreSQL连接池配置
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_size': int(os.getenv('PROD_DB_POOL_SIZE', '20')),  # 生产环境更大的连接池
                'pool_timeout': int(os.getenv('PROD_DB_POOL_TIMEOUT', '60')),  # 更长的超时时间
                'pool_recycle': int(os.getenv('PROD_DB_POOL_RECYCLE', '7200')),  # 2小时回收连接
                'max_overflow': int(os.getenv('PROD_DB_MAX_OVERFLOW', '50')),  # 更多溢出连接
                'pool_pre_ping': True,
                'echo': False,  # 生产环境禁用SQL调试
                'connect_args': {
                    'connect_timeout': 15,
                    'application_name': 'Sara_SecondHand_Shop_Prod',
                    'options': '-c statement_timeout=30000'  # 30秒语句超时
                }
            }
        else:
            # 如果生产环境仍需要SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
            
            # 生产环境SQLite配置
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_timeout': 30,
                'pool_recycle': 600,
                'pool_pre_ping': True,
                'connect_args': {
                    'timeout': 30,
                    'check_same_thread': False
                }
            }

class TestConfig(Config):
    """测试环境配置"""
    TESTING = True
    
    def __init__(self):
        """测试环境使用内存数据库和简化连接池"""
        # 测试环境使用内存数据库
        self.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        
        # 测试环境简化的连接池配置
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_recycle': 60,
            'pool_pre_ping': False,  # 测试环境不需要pre_ping
            'connect_args': {
                'timeout': 5,
                'check_same_thread': False
            }
        }

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}