document.addEventListener('DOMContentLoaded', function() {
    // 通用函数
    function showMessage(elementId, message, isError = false) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = 'status-message ' + (isError ? 'error' : 'success');
            element.style.display = 'block';
        }
    }
    
    // 克隆音色页面功能
    const audioFileInput = document.getElementById('audio-file');
    if (audioFileInput) {
        audioFileInput.addEventListener('change', function() {
            const fileName = document.getElementById('file-name');
            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
                
                // 预览上传的音频
                const previewPlayer = document.getElementById('preview-player');
                previewPlayer.src = URL.createObjectURL(this.files[0]);
                document.getElementById('audio-preview').classList.remove('hidden');
            } else {
                fileName.textContent = '未选择文件';
            }
        });
        
        // 表单提交
        const cloneForm = document.getElementById('clone-form');
        if (cloneForm) {
            cloneForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const voiceName = document.getElementById('voice-name').value.trim();
                const referenceText = document.getElementById('reference-text').value.trim();
                const voiceDescription = document.getElementById('voice-description').value.trim();
                
                if (!voiceName || !referenceText) {
                    showMessage('clone-status', '请填写音色名称和参考文本', true);
                    return;
                }
                
                // 检查是否有音频文件或录音
                if (!audioFileInput.files.length && !recordedAudioBlob) {
                    showMessage('clone-status', '请上传音频文件或录制音频', true);
                    return;
                }
                
                const cloneBtn = document.getElementById('clone-btn');
                cloneBtn.disabled = true;
                cloneBtn.textContent = '创建中...';
                
                showMessage('clone-status', '正在创建音色，请稍候...');
                
                const formData = new FormData();
                formData.append('voice_name', voiceName);
                formData.append('reference_text', referenceText);
                formData.append('voice_description', voiceDescription);
                
                // 选择上传文件或录制的音频
                if (audioFileInput.files.length > 0) {
                    formData.append('audio_file', audioFileInput.files[0]);
                } else if (recordedAudioBlob) {
                    // 直接将Blob添加到FormData，不需要先保存为文件
                    formData.append('audio_file', recordedAudioBlob, 'recorded_audio.wav');
                }
                
                fetch('/tts/clone_voice', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    cloneBtn.disabled = false;
                    cloneBtn.textContent = '创建音色';
                    
                    if (data.success) {
                        showMessage('clone-status', data.message);
                        
                        // 重置表单
                        this.reset();
                        document.getElementById('file-name').textContent = '未选择文件';
                        document.getElementById('audio-preview').classList.add('hidden');
                        recordedAudioBlob = null;
                        
                        // 2秒后刷新页面以显示新音色
                        setTimeout(function() {
                            window.location.href = '/voices';
                        }, 2000);
                    } else {
                        showMessage('clone-status', '创建音色失败: ' + data.error, true);
                    }
                })
                .catch(error => {
                    cloneBtn.disabled = false;
                    cloneBtn.textContent = '创建音色';
                    showMessage('clone-status', '请求错误: ' + error, true);
                });
            });
        }
    }
    
    // 录音功能
    let audioContext;
    let recorder;
    let recordedAudioBlob;
    let recordingTimer;
    let recordingSeconds = 0;
    let audioStream = null; // 保存音频流以便稍后停止
    
    const recordBtn = document.getElementById('record-btn');
    const stopBtn = document.getElementById('stop-btn');
    const recordingStatus = document.getElementById('recording-status');
    
    // 显示/隐藏功能封装，使代码更清晰
    function showElement(element) {
        if(element) element.style.display = 'flex';
    }
    
    function hideElement(element) {
        if(element) element.style.display = 'none';
    }
    
    // 初始状态设置 - 直接使用style属性确保状态正确
    if(recordBtn) showElement(recordBtn);
    if(recordingStatus) hideElement(recordingStatus);
    
    if (recordBtn && stopBtn) {
        // 开始录音按钮点击事件
        recordBtn.addEventListener('click', function() {
            console.log("开始录音按钮被点击");
            
            // 初始化AudioContext
            try {
                window.AudioContext = window.AudioContext || window.webkitAudioContext;
                audioContext = new AudioContext();
            } catch (e) {
                showMessage('clone-status', '您的浏览器不支持录音功能', true);
                return;
            }
            
            // 获取音频流
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    console.log("麦克风访问成功，开始录音");
                    audioStream = stream; // 保存流的引用
                    
                    // 显示录音状态和停止按钮，隐藏开始录音按钮
                    hideElement(recordBtn);
                    showElement(recordingStatus);
                    
                    // 重置录音计时器
                    recordingSeconds = 0;
                    updateRecordingTime();
                    recordingTimer = setInterval(updateRecordingTime, 1000);
                    
                    // 创建音频输入
                    const input = audioContext.createMediaStreamSource(stream);
                    
                    // 创建Recorder实例
                    recorder = new Recorder(input, {
                        numChannels: 1, // 单声道录音
                        workerPath: 'https://cdn.rawgit.com/mattdiamond/Recorderjs/08e7abd9/dist/recorderWorker.js'
                    });
                    
                    // 开始录音
                    recorder.record();
                })
                .catch(error => {
                    console.error("麦克风访问失败:", error);
                    showMessage('clone-status', '无法访问麦克风: ' + error.message, true);
                });
        });
        
        // 停止录音按钮点击事件
        stopBtn.addEventListener('click', function() {
            console.log("停止录音按钮被点击");
            
            if (recorder && recorder.recording) {
                // 停止录音
                recorder.stop();
                
                // 停止所有麦克风轨道
                if(audioStream) {
                    audioStream.getTracks().forEach(track => track.stop());
                    audioStream = null;
                }
                
                // 清除计时器
                clearInterval(recordingTimer);
                
                // 获取录音数据
                recorder.exportWAV(function(blob) {
                    console.log("录音数据已导出");
                    recordedAudioBlob = blob;
                    
                    // 创建音频URL并预览
                    const audioUrl = URL.createObjectURL(blob);
                    const previewPlayer = document.getElementById('preview-player');
                    previewPlayer.src = audioUrl;
                    document.getElementById('audio-preview').classList.remove('hidden');
                    
                    // 恢复UI - 显示开始录音按钮，隐藏录音状态
                    showElement(recordBtn);
                    hideElement(recordingStatus);
                });
                
                // 清除录音实例
                recorder.clear();
            }
        });
    }
    
    // 更新录音时间显示
    function updateRecordingTime() {
        recordingSeconds++;
        const minutes = Math.floor(recordingSeconds / 60);
        const seconds = recordingSeconds % 60;
        const timeDisplay = document.getElementById('recording-time');
        if (timeDisplay) {
            timeDisplay.textContent = 
                (minutes < 10 ? '0' : '') + minutes + ':' + 
                (seconds < 10 ? '0' : '') + seconds;
        }
        
        // 限制录音时间为最多3分钟
        if (recordingSeconds >= 180) {
            if (stopBtn) stopBtn.click();
        }
    }
    
    // 添加调试信息，检查DOM元素
    console.log("录音按钮状态:", recordBtn ? "已找到" : "未找到");
    console.log("停止按钮状态:", stopBtn ? "已找到" : "未找到");
    console.log("录音状态容器:", recordingStatus ? "已找到" : "未找到");
}); 