from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, make_response, send_file

from config import Config
from models import init_db, User, Voice, Activity
from routes import init_routes

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
init_db()

# 初始化路由
init_routes(app)

# 应用首页
@app.route('/')
def index():
    # 如果未登录，则重定向到登录页面
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    # 获取用户的所有音色
    voices = Voice.get_user_voices(session['user_id'])
    
    # 创建新的音色列表，始终包含默认音色
    voice_list = [{"id": 0, "voice_uri": Config.DEFAULT_VOICE, "voice_name": "默认音色"}]
    
    # 添加用户的自定义音色
    for voice in voices:
        voice_list.append(dict(voice))
    
    return render_template('index.html', voices=voice_list)


if __name__ == '__main__':
    app.run(debug=True, port=5001)