"""
实用工具函数模块
提供数据验证、清理和安全功能
"""
import re
import bleach
from email_validator import validate_email, EmailNotValidError


def sanitize_html(text):
    """
    清理HTML内容，防止XSS攻击
    
    Args:
        text (str): 需要清理的HTML文本
        
    Returns:
        str: 清理后的安全文本
    """
    if not text:
        return ""
    
    # 允许的HTML标签（用于用户输入的基本格式）
    allowed_tags = []  # 不允许任何HTML标签
    allowed_attributes = {}
    
    # 清理HTML并移除所有标签
    clean_text = bleach.clean(
        text, 
        tags=allowed_tags, 
        attributes=allowed_attributes,
        strip=True  # 移除标签但保留内容
    )
    
    return clean_text.strip()


def validate_phone_number(phone):
    """
    验证电话号码格式（新西兰格式）
    
    Args:
        phone (str): 电话号码
        
    Returns:
        bool: 是否为有效的电话号码
    """
    if not phone:
        return False
        
    # 移除空格和连字符
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # 新西兰电话号码格式
    patterns = [
        r'^0\d{8,9}$',          # 本地格式：021234567
        r'^64\d{8,9}$',         # 国际格式：6421234567
        r'^\+64\d{8,9}$',       # 国际格式：+6421234567
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)


def validate_email_address(email):
    """
    验证邮箱地址格式
    
    Args:
        email (str): 邮箱地址
        
    Returns:
        tuple: (是否有效, 规范化的邮箱地址)
    """
    if not email:
        return False, ""
    
    try:
        # 使用email-validator库进行验证
        valid = validate_email(email)
        return True, valid.email
    except EmailNotValidError:
        # 如果email-validator不可用，使用正则表达式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email.strip()):
            return True, email.strip().lower()
        return False, ""


def sanitize_user_input(data):
    """
    清理用户输入数据
    
    Args:
        data (dict): 用户输入数据字典
        
    Returns:
        dict: 清理后的数据字典
    """
    if not isinstance(data, dict):
        return {}
    
    cleaned_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # 清理HTML内容
            cleaned_value = sanitize_html(value)
            # 移除首尾空白字符
            cleaned_value = cleaned_value.strip()
            # 限制长度（防止过长输入）
            if key in ['name', 'contact']:
                cleaned_value = cleaned_value[:100]
            elif key in ['message', 'notes', 'description']:
                cleaned_value = cleaned_value[:1000]
            elif key in ['customer_address']:
                cleaned_value = cleaned_value[:500]
            else:
                cleaned_value = cleaned_value[:200]
                
            cleaned_data[key] = cleaned_value
        else:
            cleaned_data[key] = value
    
    return cleaned_data


def validate_form_data(form_data, required_fields=None):
    """
    验证表单数据
    
    Args:
        form_data (dict): 表单数据
        required_fields (list): 必填字段列表
        
    Returns:
        tuple: (是否有效, 错误信息列表)
    """
    if required_fields is None:
        required_fields = []
    
    errors = []
    
    # 检查必填字段
    for field in required_fields:
        if not form_data.get(field, '').strip():
            field_names = {
                'name': '姓名',
                'customer_name': '姓名',
                'contact': '联系方式',
                'customer_contact': '联系方式',
                'customer_email': '邮箱地址',
                'message': '留言内容',
                'delivery_method': '交付方式',
                'payment_method': '支付方式'
            }
            field_display = field_names.get(field, field)
            errors.append(f'请填写{field_display}')
    
    # 验证邮箱格式
    email_fields = ['customer_email', 'email', 'contact']
    for field in email_fields:
        if field in form_data and form_data[field]:
            # 如果字段包含@符号，说明是邮箱
            if '@' in form_data[field]:
                is_valid, _ = validate_email_address(form_data[field])
                if not is_valid:
                    errors.append('请输入有效的邮箱地址')
    
    # 验证电话号码格式
    phone_fields = ['customer_phone', 'phone', 'contact']
    for field in phone_fields:
        if field in form_data and form_data[field]:
            # 如果字段不包含@符号且长度合适，说明可能是电话号码
            value = form_data[field]
            if '@' not in value and len(value) >= 8:
                if not validate_phone_number(value):
                    # 只在明确是电话字段时报错
                    if field in ['customer_phone', 'phone']:
                        errors.append('请输入有效的电话号码')
    
    return len(errors) == 0, errors


def safe_filename(filename):
    """
    生成安全的文件名
    
    Args:
        filename (str): 原始文件名
        
    Returns:
        str: 安全的文件名
    """
    if not filename:
        return ""
    
    # 移除路径分隔符和特殊字符
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # 限制长度
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    name = name[:50]  # 限制文件名长度
    
    return f"{name}.{ext}" if ext else name