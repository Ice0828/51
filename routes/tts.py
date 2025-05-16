"""TTS相关路由"""
import re
import hashlib
import random
import string
import uuid
import requests
from flask import request, redirect, url_for, session, flash, jsonify, render_template, Response

from config import Config
from models import User, Voice, Activity

def generate_custom_name(voice_name, email):
    # 移除非法字符
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', voice_name)
    
    # 如果处理后为空或长度太短，添加基于邮箱的哈希
    if len(safe_name) < 3:
        # 生成基于邮箱的哈希值
        hash_obj = hashlib.md5(email.encode())
        email_hash = hash_obj.hexdigest()[:8]
        
        # 如果safe_name为空，使用随机字母开头
        if not safe_name:
            safe_name = random.choice(string.ascii_lowercase) + email_hash
        else:
            safe_name = safe_name + "_" + email_hash
    
    # 确保第一个字符是字母
    if not safe_name[0].isalpha():
        safe_name = random.choice(string.ascii_lowercase) + safe_name
    
    # 限制长度，避免过长
    if len(safe_name) > 20:
        safe_name = safe_name[:20]
    
    return safe_name


def init_tts_routes(app):
    """初始化TTS相关路由"""
    # 音色管理页面
    @app.route('/voices')
    def voices():
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        # 获取用户的所有音色及其名称
        voices = Voice.get_user_voices(session['user_id'])
        
        return render_template('voices.html', voices=voices)
    
    # 添加音色
    @app.route('/add_voice', methods=['POST'])
    def add_voice():
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
        
        voice_uri = request.form.get('voice_uri')
        voice_name = request.form.get('voice_name')
        voice_description = request.form.get('voice_description', '')
        
        if not voice_uri:
            return jsonify({'success': False, 'message': '音色URI不能为空'})
        
        if not voice_name:
            return jsonify({'success': False, 'message': '音色名称不能为空'})
        
        # 验证URI格式（简单验证）
        if not voice_uri.startswith('speech:'):
            return jsonify({'success': False, 'message': '音色URI格式不正确'})
        
        try:
            # 获取用户邮箱以生成custom_name
            user = User.get_by_id(session['user_id'])
            user_email = user['email']
            
            # 生成符合规范的custom_name
            custom_name = generate_custom_name(voice_name, user_email)
            
            # 检查是否已存在相同URI的音色
            existing_voices = Voice.get_user_voices(session['user_id'])
            for voice in existing_voices:
                if voice['voice_uri'] == voice_uri:
                    return jsonify({'success': False, 'message': '该音色已存在'})
            
            # 添加音色
            voice = Voice(
                user_id=session['user_id'],
                voice_uri=voice_uri,
                voice_name=voice_name,
                custom_name=custom_name,
                voice_description=voice_description
            )
            voice_id = voice.create()
            
            # 添加用户活动记录
            activity = Activity(session['user_id'], 'add_voice', f'添加音色: {voice_name}')
            activity.create()
            
            return jsonify({
                'success': True, 
                'message': '音色添加成功', 
                'voice_id': voice_id
            })
            
        except Exception as e:
            print(f"添加音色错误: {e}")
            return jsonify({'success': False, 'message': f'添加音色失败: {str(e)}'})
    
    # 更新音色名称
    @app.route('/update_voice_name', methods=['POST'])
    def update_voice_name():
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
        
        voice_id = request.form.get('voice_id')
        new_name = request.form.get('name')
        new_description = request.form.get('description', '')
        
        if not voice_id or not new_name:
            return jsonify({'success': False, 'message': '参数不完整'})
        
        try:
            # 验证音色是否属于当前用户
            voice = Voice.get_by_id(voice_id)
            if not voice or voice['user_id'] != session['user_id']:
                return jsonify({'success': False, 'message': '音色不存在或无权修改'})
            
            # 更新名称
            Voice.update_name(voice_id, new_name)
            
            # 添加用户活动记录
            activity = Activity(session['user_id'], 'update_voice_name', f'更新音色: {new_name}')
            activity.create()
            
            return jsonify({'success': True, 'message': '音色信息已更新'})
            
        except Exception as e:
            print(f"更新音色信息错误: {e}")
            return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    
    # 删除音色
    @app.route('/delete_voice/<int:voice_id>', methods=['POST'])
    def delete_voice(voice_id):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        try:
            # 验证音色是否属于当前用户
            voice = Voice.get_by_id(voice_id)
            if not voice or voice['user_id'] != session['user_id']:
                flash('音色不存在或无权删除')
                return redirect(url_for('voices'))
            
            # 获取音色uri用于硅流数据库删除
            voice_uri = voice['voice_uri']
            
            # 删除数据库中的音色
            Voice.delete(voice_id)
            
            # 添加用户活动记录
            activity = Activity(session['user_id'], 'delete_voice', f'删除音色')
            activity.create()
            
            # 同时删除硅流数据库音色
            url = "https://api.siliconflow.cn/v1/audio/voice/deletions"
            headers = {
                "Authorization": f"Bearer {Config.TTS_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "uri": voice_uri
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            
            flash('音色已删除')
            
        except Exception as e:
            print(f"删除音色错误: {e}")
            flash(f'删除音色失败: {str(e)}')
        
        return redirect(url_for('voices')) 
    
    # TTS路由
    @app.route('/tts')
    def tts():
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
        
        return render_template('tts.html', voices=voice_list)

    # TTS克隆音色页面
    @app.route('/tts_clone')
    def tts_clone():
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        
        return render_template('clone.html')

    # TTS合成接口
    @app.route('/tts/synthesize', methods=['POST'])
    def tts_synthesize():
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        
        text = request.form.get('text', '')
        voice = request.form.get('voice', Config.DEFAULT_VOICE)
        
        if not text:
            return jsonify({"success": False, "error": "文本不能为空"}), 400
        
        # 调用API合成语音
        url = "https://api.siliconflow.cn/v1/audio/speech"
        
        payload = {
            "input": "使用粤语口音<|endofprompt|>" + text,
            "response_format": "mp3",
            "stream": False,
            "speed": 1,
            "gain": 0,
            "model": Config.TTS_MODEL,
            "voice": voice
        }
        
        headers = {
            "Authorization": f"Bearer {Config.TTS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # 记录用户活动
                activity = Activity(session['user_id'], 'synthesize_voice', f'合成语音: 文本长度 {len(text)} 字符')
                activity.create()
                
                # 返回音频数据
                return jsonify({
                    "success": True,
                    "audio_data": response.content.hex(),
                    "content_type": response.headers.get('Content-Type', 'audio/mp3')
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"API错误: {response.text}"
                }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"请求错误: {str(e)}"
            }), 500

    # 克隆音色接口
    @app.route('/tts/clone_voice', methods=['POST'])
    def tts_clone_voice():
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        
        voice_name = request.form.get('voice_name', '')
        reference_text = request.form.get('reference_text', '')
        voice_description = request.form.get('voice_description', '')  # 获取音色备注
        
        if not voice_name or not reference_text:
            return jsonify({"success": False, "error": "音色名称和参考文本不能为空"}), 400
        
        # 检查是否上传了音频文件
        if 'audio_file' not in request.files:
            return jsonify({"success": False, "error": "未找到音频文件"}), 400
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            return jsonify({"success": False, "error": "未选择音频文件"}), 400
        
        try:
            # 获取用户邮箱以生成custom_name
            user = User.get_by_id(session['user_id'])
            user_email = user['email']
            
            # 生成符合规范的custom_name
            custom_name = generate_custom_name(voice_name, user_email)
            
            # 调用API克隆音色
            url = "https://api.siliconflow.cn/v1/uploads/audio/voice"
            
            headers = {
                "Authorization": f"Bearer {Config.TTS_API_KEY}"
            }
            
            # 直接将音频文件数据发送到API
            files = {
                "file": (audio_file.filename, audio_file.read(), 
                         'audio/wav' if audio_file.filename.endswith('.wav') else 'audio/mp3')
            }
            
            data = {
                "model": Config.TTS_MODEL,
                "customName": custom_name,
                "text": reference_text
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                response_data = response.json()
                voice_uri = response_data.get('uri')
                
                if voice_uri:
                    # 将音色信息保存到数据库
                    voice = Voice(
                        user_id=session['user_id'],
                        voice_uri=voice_uri,
                        voice_name=voice_name,
                        custom_name=custom_name,
                        voice_description=voice_description
                    )
                    voice.create()
                    
                    # 添加用户活动记录
                    activity = Activity(session['user_id'], 'clone_voice', f'克隆音色: {voice_name}')
                    activity.create()
                    
                    return jsonify({
                        "success": True,
                        "message": f"成功创建音色: {voice_name}",
                        "voice_uri": voice_uri
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"API返回格式不正确: {response_data}"
                    }), 500
            
            return jsonify({
                "success": False,
                "error": f"API错误: {response.text}"
            }), 500
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"克隆音色失败: {str(e)}"
            }), 500

    # 下载音频接口
    @app.route('/tts/download_audio', methods=['POST'])
    def tts_download_audio():
        # 获取从前端传来的音频数据
        audio_data_hex = request.json.get('audio_data')
        content_type = request.json.get('content_type', 'audio/mp3')
        filename = request.json.get('filename', f"audio_{uuid.uuid4()}.mp3")
        
        if not audio_data_hex:
            return jsonify({"error": "未提供音频数据"}), 400
        
        # 将十六进制字符串转换回二进制数据
        audio_data = bytes.fromhex(audio_data_hex)
        
        # 创建响应对象并设置响应头，使浏览器将其作为下载文件处理
        response = Response(audio_data, mimetype=content_type)
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response 