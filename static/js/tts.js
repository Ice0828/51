// 主页功能
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
    
    // 主页合成语音功能
    const synthesizeBtn = document.getElementById('synthesize-btn');
    if (synthesizeBtn) {
        synthesizeBtn.addEventListener('click', function() {
            const text = document.getElementById('text-input').value.trim();
            const voice = document.getElementById('voice-select').value;
            
            if (!text) {
                showMessage('status-message', '请输入要转换的文本', true);
                return;
            }
            
            synthesizeBtn.disabled = true;
            synthesizeBtn.textContent = '生成中...';
            
            // 显示结果容器
            document.getElementById('result-container').classList.remove('hidden');
            showMessage('status-message', '正在生成语音，请稍候...');
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('voice', voice);
            
            fetch('/tts/synthesize', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                synthesizeBtn.disabled = false;
                synthesizeBtn.textContent = '生成语音';
                
                if (data.success) {
                    // 保存音频数据到全局变量以便后续下载
                    window.lastAudioData = {
                        audio_data: data.audio_data,
                        content_type: data.content_type,
                        filename: `语音_${new Date().toISOString().replace(/[:.]/g, '-')}.mp3`
                    };
                    
                    // 将十六进制字符串转换回二进制数据
                    const audioBytes = new Uint8Array(data.audio_data.match(/[\da-f]{2}/gi).map(h => parseInt(h, 16)));
                    const audioBlob = new Blob([audioBytes], {type: data.content_type});
                    
                    // 创建音频URL并播放
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audioPlayer = document.getElementById('audio-player');
                    audioPlayer.src = audioUrl;
                    audioPlayer.play();
                    
                    // 添加下载按钮（如果不存在）
                    if (!document.getElementById('download-btn')) {
                        const downloadBtn = document.createElement('button');
                        downloadBtn.id = 'download-btn';
                        downloadBtn.textContent = '下载音频';
                        downloadBtn.className = 'download-btn';
                        downloadBtn.addEventListener('click', downloadAudio);
                        
                        const audioContainer = document.querySelector('.audio-player');
                        audioContainer.appendChild(downloadBtn);
                    }
                    
                    showMessage('status-message', '语音生成成功！');
                } else {
                    showMessage('status-message', '语音生成失败: ' + data.error, true);
                }
            })
            .catch(error => {
                synthesizeBtn.disabled = false;
                synthesizeBtn.textContent = '生成语音';
                showMessage('status-message', '请求错误: ' + error, true);
            });
        });
    }
    
    // 下载音频函数
    function downloadAudio() {
        if (!window.lastAudioData) {
            showMessage('status-message', '没有可下载的音频', true);
            return;
        }
        
        // 创建一个a标签并点击下载
        const audioBytes = new Uint8Array(window.lastAudioData.audio_data.match(/[\da-f]{2}/gi).map(h => parseInt(h, 16)));
        const audioBlob = new Blob([audioBytes], {type: window.lastAudioData.content_type});
        const downloadUrl = URL.createObjectURL(audioBlob);
        
        const downloadLink = document.createElement('a');
        downloadLink.href = downloadUrl;
        downloadLink.download = window.lastAudioData.filename;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }
}); 