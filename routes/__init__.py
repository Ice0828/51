"""路由模块"""

def init_routes(app):
    """初始化所有路由"""
    # 导入并注册认证相关路由
    from . import auth
    auth.init_auth_routes(app)

    # 导入并注册发音评估相关路由
    from . import pronunciation
    pronunciation.init_pronunciation_routes(app) 
    
    # 导入并注册音色相关路由
    from . import tts
    tts.init_tts_routes(app)
    
    