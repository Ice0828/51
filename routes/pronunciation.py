"""发音评估相关路由"""
import os
import json
import base64
import uuid
import random
import requests
from flask import request, jsonify, send_file, session

from config import Config
from models import Activity

def create_llm_prompt(assessment_data, reference_text):
    """构建发送给LLM的提示词"""
    # 提取关键评分信息
    accuracy_score = assessment_data.get("AccuracyScore", 0)
    fluency_score = assessment_data.get("FluencyScore", 0)
    completeness_score = assessment_data.get("CompletenessScore", 0)
    prosody_score = assessment_data.get("ProsodyScore", 0)
    pron_score = assessment_data.get("PronScore", 0)
    
    # 提取有问题的音素信息
    problematic_phonemes = []
    for word in assessment_data.get("Words", []):
        if word.get("ErrorType") in ["None", "Mispronunciation"]:
            for phoneme in word.get("Phonemes", []):
                if phoneme.get("AccuracyScore", 100) < 60:  # 低于60分的音素视为问题音素
                    problematic_phonemes.append({
                        "word": word.get("Word", ""),
                        "phoneme": phoneme.get("Phoneme", ""),
                        "score": phoneme.get("AccuracyScore", 0)
                    })
    
    # 构造提示词
    prompt = f"""你是一位友好且专业的语音教师，请对用户的发音进行评估和指导。请用中文回复。以下是用户的发音评估数据：

参考文本: {reference_text}

总体评分:
- 准确性得分: {accuracy_score}
- 流利度得分: {fluency_score}
- 完整度得分: {completeness_score}
- 韵律得分: {prosody_score}
- 发音总分: {pron_score}

存在问题的音素:
"""
    
    for item in problematic_phonemes:
        prompt += f"- 单词 '{item['word']}' 中的音素 '{item['phoneme']}', 得分: {item['score']}\n"
    
    prompt += """
请提供以下内容:
1. 对总体发音水平的简短评价 (1-2句话)
2. 针对问题发音的具体指导，包括正确发音的口型和舌位描述
3. 1-2个简短的练习建议，帮助用户改进这些特定音素的发音
最后附上鼓励性的结束语

请保持专业、友好并富有鼓励性，重点关注最需要改进的地方。你要模仿并扮演人类教师的职业，在保证条理清晰地前提下，保持说话自然，不要让人意识到你是个AI！"""
    
    return prompt

def call_llm_api(prompt):
    """调用LLM API获取发音指导反馈"""
    try:
        llm_response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": Config.LLM_API_KEY,
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": Config.LLM_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }),
            timeout=10  # 设置超时时间
        )
        
        response_data = llm_response.json()
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        else:
            return "抱歉，语音老师不在，请稍后再来。"
            
    except Exception as e:
        print(f"调用LLM API出错: {str(e)}")
        return "抱歉，语音老师不在，请稍后再来。"

def parse_phonemes(assessment_data):   
    #存储声母列表
    consonant_list = []
    #存储韵母列表
    vowel_list = []
    #存储声调列表
    tone_list = []
    
    # 提取有问题的音素信息
    problematic_phonemes = []
    for word in assessment_data.get("Words", []):
        if word.get("ErrorType") in ["None", "Mispronunciation"]:
            for phoneme in word.get("Phonemes", []):
                if phoneme.get("AccuracyScore", 100) < 60:  # 低于60分的音素视为问题音素
                    phoneme_str = phoneme.get("Phoneme", "")
                    problematic_phonemes.append(phoneme_str)
                    
                    # 分解拼音为声母、韵母和声调
                    parts = phoneme_str.split(" ")
                    if len(parts) >= 1:
                        pinyin = parts[0]
                        
                        # 提取声调（最后一个字符如果是数字）
                        tone = ""
                        if parts[-1].isdigit():
                            tone = parts[-1]
                            
                        
                        # 声母和韵母的分离
                        consonant = ""
                        vowel = ""
                        
                        # 声母列表
                        possible_consonants = ["b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", 
                                              "j", "q", "x", "zh", "ch", "sh", "r", "z", "c", "s","y","w"]
                        
                        for cons in possible_consonants:
                            if pinyin.startswith(cons):
                                if cons != "y" and cons != "w":
                                    consonant = cons
                                vowel = pinyin[len(cons):]
                                break
                        
                        # 添加到相应列表中（如果不存在）
                        if consonant and consonant not in consonant_list:
                            consonant_list.append(consonant)
                        if vowel and vowel not in vowel_list:
                            vowel_list.append(vowel)
                        if tone not in tone_list:
                                tone_list.append(tone)
    
    dict_phonemes = {
        "consonants": consonant_list,
        "vowels": vowel_list,
        "tones": tone_list
    }

    return dict_phonemes

def init_pronunciation_routes(app):
    """初始化发音评估相关路由"""
    
    @app.route("/gettonguetwister", methods=["POST"])
    def gettonguetwister():
        try:
            tonguetwisters = [
                "石室诗士施氏，嗜狮，誓食十狮。氏时时适市视狮。十时，适十狮适市。是时，适施氏适市。氏视十狮，恃矢势，使是十狮逝世。氏拾是十狮尸，适石室。石室湿，氏使侍拭石室。石室拭，氏始试食是十狮尸。食时，始识十狮尸，实十石狮尸。试释是事。",
                "四是四，十是十，十四是十四，四十是四十。说好四和十得靠舌头和牙齿",
                "白石白又滑，搬来白石搭白塔。白石塔，白石塔，白石搭石塔，白塔白石搭",
                "黑化肥发灰会挥发，灰化肥挥发会发黑"
            ]
            selected_tt = random.choice(tonguetwisters)
            print(f"绕口令API请求成功，返回：{selected_tt[:10]}...")
            return jsonify({"tt": selected_tt})
        except Exception as e:
            print(f"绕口令API请求出错：{str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/gettoken", methods=["POST"])
    def gettoken():
        fetch_token_url = f'https://{Config.AZURE_CONFIG["region"]}.api.cognitive.microsoft.com/sts/v1.0/issueToken'
        headers = {
            'Ocp-Apim-Subscription-Key': Config.AZURE_CONFIG["subscription_key"]
        }
        response = requests.post(fetch_token_url, headers=headers)
        access_token = response.text
        return jsonify({"at": access_token})

    @app.route("/ackaud", methods=["POST"])
    def ackaud():
        f = request.files['audio_data']
        reference_text = request.form.get("reftext")

        # a generator which reads audio data chunk by chunk
        def get_chunk(audio_source, chunk_size=1024):
            yield Config.WAVE_HEADER_16K_16BIT_MONO
            while True:
                chunk = audio_source.read(chunk_size)
                if not chunk:
                    break
                yield chunk

        # build pronunciation assessment parameters
        enable_prosody_assessment = True
        phoneme_alphabet = "SAPI"  # IPA or SAPI
        enable_miscue = True
        nbest_phoneme_count = 5
        pron_assessment_params_json = (
            '{"GradingSystem":"HundredMark","Dimension":"Comprehensive","ReferenceText":"%s","EnableProsodyAssessment":"%s",'
            '"PhonemeAlphabet":"%s","EnableMiscue":"%s","NBestPhonemeCount":"%s"}'
            % (reference_text, enable_prosody_assessment, phoneme_alphabet, enable_miscue, nbest_phoneme_count)
        )
        pron_assessment_params_base64 = base64.b64encode(bytes(pron_assessment_params_json, "utf-8"))
        pron_assessment_params = str(pron_assessment_params_base64, "utf-8")

        session_id = uuid.uuid4().hex

        # build request
        azure_config = Config.AZURE_CONFIG
        url = f"https://{azure_config['region']}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        url = f"{url}?format=detailed&language={azure_config['language']}&X-ConnectionId={session_id}"
        headers = {
            "Accept": "application/json;text/xml",
            "Connection": "Keep-Alive",
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Ocp-Apim-Subscription-Key": azure_config['subscription_key'],
            "Pronunciation-Assessment": pron_assessment_params,
            "Transfer-Encoding": "chunked",
            "Expect": "100-continue",
        }

        audioFile = f
        # send request with chunked data
        response = requests.post(url=url, data=get_chunk(audioFile), headers=headers)
        audioFile.close()
        
        # 获取微软的评估结果
        ms_response = response.json()
        
        # 如果识别成功，解析音素信息
        if ms_response.get("RecognitionStatus") == "Success" and len(ms_response.get("NBest", [])) > 0:
            # 解析音素信息
            phonemes_info = parse_phonemes(ms_response["NBest"][0])
            ms_response["phonemes_info"] = phonemes_info
        
        # 记录用户活动
        if 'user_id' in session:
            activity = Activity(session['user_id'], 'pronunciation_assessment', '完成发音评估')
            activity.create()
        
        return ms_response

    @app.route("/get_phoneme_video/<phoneme>", methods=["GET"])
    def get_phoneme_video(phoneme):
        """获取音素示范视频"""
        try:
            # 安全检查，避免路径遍历攻击
            if '..' in phoneme or '/' in phoneme:
                return jsonify({"error": "非法的音素名称"}), 400
            
            # 构建视频文件路径
            video_path = os.path.join('static', 'videos', f"{phoneme}.mp4")
            
            # 检查文件是否存在
            if not os.path.exists(video_path):
                return jsonify({"error": f"未找到音素 '{phoneme}' 的示范视频"}), 404
            
            # 返回视频文件
            return send_file(video_path, mimetype='video/mp4')
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/get_llm_feedback", methods=["POST"])
    def get_llm_feedback():
        try:
            # 获取前端传来的数据
            assessment_data = request.json.get("assessment_data")
            reference_text = request.json.get("reference_text")
            
            if not assessment_data or not reference_text:
                return jsonify({"error": "缺少必要参数"}), 400
                
            # 构建LLM提示词
            prompt = create_llm_prompt(assessment_data, reference_text)
            
            # 调用LLM API
            llm_feedback = call_llm_api(prompt)
            
            # 记录用户活动
            if 'user_id' in session:
                activity = Activity(session['user_id'], 'get_feedback', '获取发音指导')
                activity.create()
            
            return jsonify({
                "success": True,
                "llm_feedback": llm_feedback
            })
            
        except Exception as e:
            print(f"获取LLM反馈时出错: {str(e)}")
            return jsonify({
                "success": False,
                "error": "获取发音指导失败，请稍后重试"
            }), 500 