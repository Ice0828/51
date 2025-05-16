"""用户认证相关路由"""
import re
import random
import string
import smtplib
from flask import request, redirect, url_for, session, flash, jsonify, render_template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from config import Config
from models import User, Activity

# 存储验证码的字典
verification_codes = {}

# 生成随机验证码
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

# 从发件人邮箱获取SMTP配置
def get_smtp_config():
    sender_email = Config.EMAIL_CONFIG['sender']['email']
    domain = sender_email.split('@')[-1].lower()
    
    if '163.com' in domain:
        return Config.EMAIL_CONFIG['smtp']['163']
    elif 'qq.com' in domain:
        return Config.EMAIL_CONFIG['smtp']['qq']
    elif 'gmail.com' in domain:
        return Config.EMAIL_CONFIG['smtp']['gmail']
    elif 'outlook.com' in domain or 'hotmail.com' in domain:
        return Config.EMAIL_CONFIG['smtp']['outlook']
    else:
        return Config.EMAIL_CONFIG['smtp']['163']

# 发送验证码邮件
def send_verification_email(email, code, email_enabled=True):
    print(f"验证码: {code} 已发送到邮箱: {email}")
    
    if not email_enabled:
        return True
    
    try:
        smtp_config = get_smtp_config()
        sender_email = Config.EMAIL_CONFIG['sender']['email']
        sender_password = Config.EMAIL_CONFIG['sender']['password']
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "验证码"
        
        body = f"您的验证码是：{code}"
        msg.attach(MIMEText(body, 'plain'))
        
        if smtp_config.get('use_ssl', False):
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
        else:
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
        
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

# 验证验证码
def verify_code(email, code):
    if email not in verification_codes:
        return False
    
    saved_data = verification_codes[email]
    if saved_data['expiry'] < datetime.now():
        # 验证码已过期
        return False
    
    if saved_data['code'] != code:
        # 验证码不匹配
        return False
    
    # 验证成功后删除验证码
    del verification_codes[email]
    return True

def init_auth_routes(app):
    """初始化用户认证相关路由"""
    
    @app.route('/request_verification_code', methods=['POST'])
    def request_verification_code():
        email = request.form.get('email')
        if not email:
            return jsonify({'success': False, 'message': '邮箱不能为空'})
        
        # 验证邮箱格式
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})
        
        # 检查邮箱是否已被注册
        user = User.get_by_email(email)
        if user:
            return jsonify({'success': False, 'message': '该邮箱已被注册'})
        
        # 生成验证码并保存
        code = generate_verification_code()
        expiry = datetime.now() + timedelta(seconds=60)
        verification_codes[email] = {'code': code, 'expiry': expiry}
        
        # 发送验证码邮件
        success = send_verification_email(email, code, app.config['EMAIL_ENABLED'])
        
        if success:
            return jsonify({'success': True, 'message': '验证码已发送，60秒内有效'})
        else:
            return jsonify({'success': False, 'message': '验证码发送失败，请稍后重试'})
    
    @app.route('/verify_code_ajax', methods=['POST'])
    def verify_code_ajax():
        email = request.form.get('email')
        code = request.form.get('code')
        
        if not email or not code:
            return jsonify({
                'valid': False,
                'expired': False,
                'message': '邮箱和验证码不能为空'
            })
        
        if email not in verification_codes:
            return jsonify({
                'valid': False,
                'expired': True,
                'message': '验证码已失效，请重新获取'
            })
        
        saved_data = verification_codes[email]
        
        # 检查是否过期
        if saved_data['expiry'] < datetime.now():
            return jsonify({
                'valid': False,
                'expired': True, 
                'message': '验证码已过期，请重新获取'
            })
        
        # 检查验证码是否匹配
        if saved_data['code'] != code:
            return jsonify({
                'valid': False,
                'expired': False,
                'message': '验证码不正确'
            })
        
        # 验证成功，但不删除验证码，等提交表单时再删除
        return jsonify({
            'valid': True,
            'expired': False,
            'message': '验证码有效'
        })
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            verification_code = request.form['verification_code']
            nationality = request.form.get('nationality', '')
            native_language = request.form.get('native_language', '')
            
            # 验证验证码
            if not verify_code(email, verification_code):
                return jsonify({
                    'success': False,
                    'message': '验证码无效或已过期',
                    'redirect': None
                })
            
            # 检查用户名或邮箱是否已存在
            existing_username = User.get_by_username(username)
            existing_email = User.get_by_email(email)
            
            if existing_username or existing_email:
                return jsonify({
                    'success': False,
                    'message': '用户名或邮箱已被占用',
                    'redirect': None
                })
            
            # 创建新用户
            try:
                user = User(username=username, email=email, password=password)
                user_id = user.create()
                
                # 更新附加信息
                User.update_profile(user_id, {
                    'nationality': nationality,
                    'native_language': native_language
                })
                
                # 记录用户活动
                activity = Activity(user_id, 'register', '用户注册')
                activity.create()
                
                return jsonify({
                    'success': True,
                    'message': '注册成功，请登录',
                    'redirect': url_for('login')
                })
            except Exception as e:
                print(f"注册失败: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'注册失败: {str(e)}',
                    'redirect': None
                })
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user = User.get_by_email(email)
            
            if user and User.verify_password(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                
                # 记录用户活动
                activity = Activity(user['id'], 'login', '用户登录')
                activity.create()
                
                flash('登录成功')
                return redirect(url_for('index'))
            else:
                flash('邮箱或密码错误')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        if 'user_id' in session:
            # 记录用户活动
            activity = Activity(session['user_id'], 'logout', '用户退出登录')
            activity.create()
        
        session.pop('user_id', None)
        session.pop('username', None)
        flash('您已退出登录')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        user = User.get_by_id(session['user_id'])
        
        if not user:
            flash('用户不存在')
            return redirect(url_for('logout'))
        
        return render_template('dashboard.html', user=dict(user))
    
    @app.route('/update_profile', methods=['POST'])
    def update_profile():
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        profile_data = {
            'email': request.form['email'],
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'nationality': request.form.get('nationality', ''),
            'native_language': request.form.get('native_language', '')
        }
        
        try:
            User.update_profile(session['user_id'], profile_data)
            
            # 记录用户活动
            activity = Activity(session['user_id'], 'update_profile', '更新个人信息')
            activity.create()
            
            flash('个人信息已更新')
        except Exception as e:
            flash(f'更新失败: {str(e)}')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/delete_user/<int:user_id>', methods=['POST'])
    def delete_user(user_id):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        # 只允许删除自己的账户
        if session['user_id'] != user_id:
            flash('无权进行此操作')
            return redirect(url_for('dashboard'))
        
        try:
            User.delete(user_id)
            flash('账户已删除')
        except Exception as e:
            flash(f'删除失败: {str(e)}')
        
        return redirect(url_for('logout')) 