"""
Sara二手售卖网站 - 文件上传处理模块
实现图片上传、压缩和管理功能
"""

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024
# 图片压缩质量
IMAGE_QUALITY = 85
# 最大图片尺寸
MAX_IMAGE_SIZE = (1200, 1200)
# 缩略图尺寸
THUMBNAIL_SIZE = (300, 300)


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_filename(original_filename):
    """生成安全的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def get_upload_path(filename):
    """获取上传文件的完整路径"""
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    return os.path.join(upload_folder, filename)


def get_image_url(filename):
    """获取图片的URL"""
    return f"/static/uploads/{filename}"


def validate_image_file(file):
    """验证上传的图片文件"""
    errors = []
    
    # 检查文件是否存在
    if not file or file.filename == '':
        errors.append('请选择文件')
        return False, errors
    
    # 检查文件扩展名
    if not allowed_file(file.filename):
        errors.append(f'不支持的文件格式，支持格式：{", ".join(ALLOWED_EXTENSIONS)}')
        return False, errors
    
    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        errors.append(f'文件大小超过限制，最大允许 {MAX_FILE_SIZE // (1024*1024)}MB')
        return False, errors
    
    if file_size == 0:
        errors.append('文件为空')
        return False, errors
    
    return True, errors


def process_image(file, filename):
    """处理图片：压缩和调整尺寸"""
    try:
        # 打开图片
        with Image.open(file) as img:
            # 转换为RGB模式（处理RGBA和其他模式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整图片尺寸（保持宽高比）
            img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # 保存处理后的图片
            filepath = get_upload_path(filename)
            img.save(filepath, 'JPEG', quality=IMAGE_QUALITY, optimize=True)
            
            logger.info(f'图片处理成功: {filename}')
            return True, None
            
    except Exception as e:
        logger.error(f'图片处理失败: {str(e)}')
        return False, f'图片处理失败: {str(e)}'


def create_thumbnail(filename):
    """创建缩略图"""
    try:
        # 构建文件路径
        original_path = get_upload_path(filename)
        name, ext = os.path.splitext(filename)
        thumbnail_filename = f"{name}_thumb{ext}"
        thumbnail_path = get_upload_path(thumbnail_filename)
        
        # 创建缩略图
        with Image.open(original_path) as img:
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=IMAGE_QUALITY, optimize=True)
            
        logger.info(f'缩略图创建成功: {thumbnail_filename}')
        return thumbnail_filename
        
    except Exception as e:
        logger.error(f'缩略图创建失败: {str(e)}')
        return None


def upload_image(file):
    """
    上传图片的主要函数
    返回: (成功标志, 文件名或错误信息, 缩略图文件名)
    """
    try:
        # 验证文件
        is_valid, errors = validate_image_file(file)
        if not is_valid:
            return False, errors[0], None
        
        # 生成安全文件名
        filename = generate_filename(file.filename)
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 处理图片
        success, error = process_image(file, filename)
        if not success:
            return False, error, None
        
        # 创建缩略图
        thumbnail_filename = create_thumbnail(filename)
        
        logger.info(f'文件上传成功: {filename}')
        return True, filename, thumbnail_filename
        
    except Exception as e:
        logger.error(f'文件上传失败: {str(e)}')
        return False, f'上传失败: {str(e)}', None


def delete_image(filename):
    """删除图片文件"""
    try:
        if not filename:
            return True
        
        # 删除原图
        filepath = get_upload_path(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f'图片删除成功: {filename}')
        
        # 删除缩略图
        name, ext = os.path.splitext(filename)
        thumbnail_filename = f"{name}_thumb{ext}"
        thumbnail_path = get_upload_path(thumbnail_filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f'缩略图删除成功: {thumbnail_filename}')
        
        return True
        
    except Exception as e:
        logger.error(f'图片删除失败: {str(e)}')
        return False


def get_image_info(filename):
    """获取图片信息"""
    try:
        filepath = get_upload_path(filename)
        if not os.path.exists(filepath):
            return None
        
        with Image.open(filepath) as img:
            return {
                'filename': filename,
                'url': get_image_url(filename),
                'size': img.size,
                'format': img.format,
                'mode': img.mode,
                'file_size': os.path.getsize(filepath)
            }
    except Exception as e:
        logger.error(f'获取图片信息失败: {str(e)}')
        return None