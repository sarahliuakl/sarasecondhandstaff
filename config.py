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
        """初始化配置时设置数据库URI"""
        if self.DATABASE_TYPE == 'postgresql':
            # PostgreSQL配置
            username = os.getenv('DB_USERNAME', 'sara_user')
            password = os.getenv('DB_PASSWORD', 'sara123')
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'sara_secondhand')
            
            self.SQLALCHEMY_DATABASE_URI = f'postgresql://{username}:{password}@{host}:{port}/{database}'
        else:
            # SQLite配置（默认）
            basedir = os.path.abspath(os.path.dirname(__file__))
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    def __init__(self):
        """生产环境默认使用PostgreSQL"""
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
        else:
            # 如果生产环境仍需要SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "sara_shop.db")}'
        
        super().__init__()

class TestConfig(Config):
    """测试环境配置"""
    TESTING = True
    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}