"""
工具函数测试
"""
import pytest
from src.utils import sanitize_user_input, validate_form_data, validate_email_address


class TestSanitizeInput:
    """输入清理测试"""
    
    def test_sanitize_normal_input(self):
        """测试正常输入清理"""
        data = {
            'name': '  张三  ',
            'email': '  test@example.com  ',
            'message': '这是一条消息'
        }
        
        result = sanitize_user_input(data)
        
        assert result['name'] == '张三'
        assert result['email'] == 'test@example.com'
        assert result['message'] == '这是一条消息'
    
    def test_sanitize_html_input(self):
        """测试HTML输入清理"""
        data = {
            'message': '<script>alert("xss")</script>正常内容',
            'description': '<p>段落内容</p><script>恶意脚本</script>'
        }
        
        result = sanitize_user_input(data)
        
        # 应该移除script标签但保留正常内容
        assert '<script>' not in result['message']
        assert '正常内容' in result['message']
        assert '<script>' not in result['description']
    
    def test_sanitize_empty_values(self):
        """测试空值清理"""
        data = {
            'name': '',
            'email': None,
            'message': '   '
        }
        
        result = sanitize_user_input(data)
        
        assert result['name'] == ''
        assert result['email'] == ''  # None应该被转换为空字符串
        assert result['message'] == ''  # 空白字符应该被清理
    
    def test_sanitize_non_string_values(self):
        """测试非字符串值清理"""
        data = {
            'price': 100.50,
            'quantity': 5,
            'active': True,
            'tags': ['tag1', 'tag2']
        }
        
        result = sanitize_user_input(data)
        
        # 非字符串值应该保持原样
        assert result['price'] == 100.50
        assert result['quantity'] == 5
        assert result['active'] == True
        assert result['tags'] == ['tag1', 'tag2']


class TestValidateFormData:
    """表单数据验证测试"""
    
    def test_validate_all_required_fields_present(self):
        """测试所有必填字段都存在"""
        data = {
            'name': '张三',
            'email': 'test@example.com',
            'message': '测试消息'
        }
        required_fields = ['name', 'email', 'message']
        
        is_valid, errors = validate_form_data(data, required_fields)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_missing_required_fields(self):
        """测试缺少必填字段"""
        data = {
            'name': '张三',
            'email': ''  # 空值
            # 缺少message字段
        }
        required_fields = ['name', 'email', 'message']
        
        is_valid, errors = validate_form_data(data, required_fields)
        
        assert is_valid == False
        assert len(errors) == 2  # email为空 + message缺失
        assert any('email' in error for error in errors)
        assert any('message' in error for error in errors)
    
    def test_validate_empty_required_fields(self):
        """测试必填字段为空"""
        data = {
            'name': '',
            'email': '   ',  # 只有空格
            'message': None
        }
        required_fields = ['name', 'email', 'message']
        
        is_valid, errors = validate_form_data(data, required_fields)
        
        assert is_valid == False
        assert len(errors) == 3  # 所有字段都有问题
    
    def test_validate_no_required_fields(self):
        """测试没有必填字段的情况"""
        data = {'optional': 'value'}
        required_fields = []
        
        is_valid, errors = validate_form_data(data, required_fields)
        
        assert is_valid == True
        assert len(errors) == 0


class TestValidateEmailAddress:
    """邮箱地址验证测试"""
    
    def test_valid_email_addresses(self):
        """测试有效邮箱地址"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.nz',
            'admin123@test-site.org',
            'contact+info@company.com'
        ]
        
        for email in valid_emails:
            is_valid, normalized = validate_email_address(email)
            assert is_valid == True
            assert normalized == email.lower().strip()
    
    def test_invalid_email_addresses(self):
        """测试无效邮箱地址"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user..name@domain.com',
            'user@domain',
            '',
            None,
            'user name@domain.com'  # 空格
        ]
        
        for email in invalid_emails:
            is_valid, normalized = validate_email_address(email)
            assert is_valid == False
    
    def test_email_normalization(self):
        """测试邮箱规范化"""
        test_cases = [
            ('  Test@Example.COM  ', 'test@example.com'),
            ('USER@DOMAIN.ORG', 'user@domain.org'),
            ('Mixed.Case@Email.Com', 'mixed.case@email.com')
        ]
        
        for original, expected in test_cases:
            is_valid, normalized = validate_email_address(original)
            assert is_valid == True
            assert normalized == expected
    
    def test_email_edge_cases(self):
        """测试邮箱边界情况"""
        # 最短有效邮箱
        is_valid, normalized = validate_email_address('a@b.co')
        assert is_valid == True
        
        # 很长的邮箱
        long_email = 'a' * 50 + '@' + 'b' * 50 + '.com'
        is_valid, normalized = validate_email_address(long_email)
        assert is_valid == True
        
        # 特殊字符
        is_valid, normalized = validate_email_address('test+tag@example.com')
        assert is_valid == True


class TestUtilsIntegration:
    """工具函数集成测试"""
    
    def test_sanitize_and_validate_integration(self):
        """测试清理和验证的集成使用"""
        # 模拟表单提交数据
        raw_data = {
            'name': '  <script>alert("xss")</script>张三  ',
            'email': '  TEST@EXAMPLE.COM  ',
            'message': '这是一条<b>消息</b>',
            'optional': ''
        }
        
        # 第一步：清理输入
        clean_data = sanitize_user_input(raw_data)
        
        # 第二步：验证必填字段
        required_fields = ['name', 'email', 'message']
        is_valid, errors = validate_form_data(clean_data, required_fields)
        
        assert is_valid == True
        assert len(errors) == 0
        
        # 第三步：验证邮箱
        email_valid, normalized_email = validate_email_address(clean_data['email'])
        
        assert email_valid == True
        assert normalized_email == 'test@example.com'
        
        # 验证清理效果
        assert '<script>' not in clean_data['name']
        assert '张三' in clean_data['name']
    
    def test_complete_form_processing_workflow(self):
        """测试完整的表单处理工作流"""
        # 模拟用户提交的联系表单
        form_data = {
            'name': '  李四<script>  ',
            'contact': '  LI4@GMAIL.COM  ',
            'message': '我想咨询<b>笔记本电脑</b>的详情'
        }
        
        # 完整处理流程
        clean_data = sanitize_user_input(form_data)
        is_valid, errors = validate_form_data(clean_data, ['name', 'contact', 'message'])
        
        if is_valid and '@' in clean_data['contact']:
            email_valid, normalized_email = validate_email_address(clean_data['contact'])
            if email_valid:
                clean_data['contact'] = normalized_email
        
        # 验证最终结果
        assert is_valid == True
        assert clean_data['name'] == '李四'  # 移除了script和空格
        assert clean_data['contact'] == 'li4@gmail.com'  # 规范化邮箱
        assert '<b>' in clean_data['message']  # 保留安全的HTML标签
        assert '<script>' not in clean_data['message']  # 移除危险标签