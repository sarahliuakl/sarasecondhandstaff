from flask import session, request, current_app, url_for, redirect
from flask_babel import Babel, get_locale, get_timezone
from functools import wraps
import os

# 支持的语言列表
LANGUAGES = {
    'zh_CN': '中文',
    'en': 'English'
}

babel = Babel()

def init_babel(app):
    """初始化Babel配置"""
    # 设置默认语言和时区
    app.config['LANGUAGES'] = LANGUAGES
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'Pacific/Auckland'
    
    # 使用Flask-Babel 4.0的正确方式初始化
    babel.init_app(
        app,
        default_locale='en',
        default_timezone='Pacific/Auckland',
        default_translation_directories='translations',
        locale_selector=get_user_locale,
        timezone_selector=get_user_timezone
    )

def get_user_locale():
    """获取用户语言偏好"""
    # 1. 检查URL中的语言前缀
    if request.endpoint and hasattr(request, 'view_args') and request.view_args:
        lang = request.view_args.get('lang')
        if lang and lang in LANGUAGES:
            session['language'] = lang
            return lang
        # 兼容旧的 'zh'，自动切换为 'zh_CN'
        if lang == 'zh':
            session['language'] = 'zh_CN'
            return 'zh_CN'
    
    # 2. 检查session中的语言设置
    if 'language' in session and session['language'] in LANGUAGES:
        return session['language']
    # 兼容旧的 'zh'
    if 'language' in session and session['language'] == 'zh':
        session['language'] = 'zh_CN'
        return 'zh_CN'
    
    # 3. 检查浏览器Accept-Language头
    return request.accept_languages.best_match(LANGUAGES.keys()) or 'zh_CN'

def get_user_timezone():
    """获取用户时区"""
    user = getattr(request, 'user', None)
    if user is not None:
        return user.timezone
    return 'Pacific/Auckland'

# 在Flask-Babel 4.0中，需要在应用上下文中注册选择器

def get_supported_languages():
    """获取支持的语言列表"""
    return LANGUAGES

def set_language(language):
    """设置当前用户的语言"""
    if language in LANGUAGES:
        session['language'] = language
        return True
    return False

def localized_url(endpoint, **values):
    """生成本地化的URL"""
    lang = get_locale().language if get_locale() else 'en'
    return url_for(endpoint, lang=lang, **values)

def redirect_to_localized_url(endpoint, **values):
    """重定向到本地化URL"""
    return redirect(localized_url(endpoint, **values))

def require_lang(f):
    """装饰器：确保路由包含语言前缀"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'lang' not in kwargs:
            # 如果没有语言前缀，重定向到带语言前缀的URL
            lang = get_user_locale()
            return redirect(url_for(request.endpoint, lang=lang, **request.view_args or {}))
        return f(*args, **kwargs)
    return decorated_function