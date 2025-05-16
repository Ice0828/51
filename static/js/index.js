var accuracyscore = document.getElementById('accuracyscore');
var fluencyscore = document.getElementById('fluencyscore');
var completenessscore = document.getElementById('completenessscore');
var prosodyscore = document.getElementById('prosodyscore');
var pronscore = document.getElementById('pronscore');
var wordsomitted = document.getElementById('wordsomitted');
var wordsinserted = document.getElementById('wordsinserted');
var omittedwords = "";
var insertedwords = "";
wordsinserted.style.display = "none";
document.getElementById("wih").style.display = "none";

var wordrow = document.getElementById('wordrow');
var phonemerow = document.getElementById('phonemerow');
var scorerow = document.getElementById('scorerow');

var reftext = document.getElementById('reftext');
var formcontainer = document.getElementById('formcontainer');
var ttbutton = document.getElementById('randomtt');
var hbutton = document.getElementById('buttonhear');
var recordingsList = document.getElementById('recordingsList');
var ttsList = document.getElementById('ttsList');
var lastgettstext;
var objectUrlMain;
var wordaudiourls = new Array;

var phthreshold1 = 80;
var phthreshold2 = 60;
var phthreshold3 = 40;
var phthreshold4 = 20;

var AudioContext = window.AudioContext || window.webkitAudioContext;;
var audioContent;
var start = false;
var stop = false;
var permission = false;
var reftextval;
var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var audioStream ; 					//MediaStreamAudioSourceNode we'll be recording
var blobpronun;
var offsetsarr;
var tflag = true;
var wordlist;

var t0 = 0;
var t1;
var at;

// 添加一个全局变量存储已合成的音频
var synthesizedAudios = [];

// 音素信息缓存
var cachedVideos = {};

window.onload = () => {
    if(tflag){
        tflag = gettoken();
        tflag = false;
    }
    
    // 检查页面上是否有必要的元素
    console.log("DOM已加载，检查关键元素:");
    console.log("reftext:", reftext);
    console.log("ttbutton:", ttbutton);
    console.log("hbutton:", hbutton);
};

function gettoken(){
    var request = new XMLHttpRequest();
    request.open('POST', '/gettoken', true);

    // Callback function for when request completes
    request.onload = () => {
        // Extract JSON data from request
        const data = JSON.parse(request.responseText);
        at = data.at;
        console.log("获取到token");
    }
    
    //send request
    request.send();
    return false;
}

function playword(k){
    var audio = document.getElementById('ttsaudio');
    audio.playbackRate = 0.5;
    audio.currentTime = (offsetsarr[k]/1000) + 0;

    var stopafter = 10000;

    if(k != offsetsarr.length -1){
        stopafter = (offsetsarr[k+1]/1000) + 0.01;
    }
    
    audio.play();

    var pausing_function = function(){
        if(this.currentTime >= stopafter) {
            this.pause();
            this.currentTime = 0;
            stopafter = 10000;        
            // remove the event listener after you paused the playback
            this.removeEventListener("timeupdate",pausing_function);
            audio.playbackRate = 0.9;
        }
    };
    
    audio.addEventListener("timeupdate", pausing_function);
   
}

function playwordind(word) {
    var audio = document.getElementById('ttsaudio');
    if (!audio) {
        console.error('无法找到音频元素');
        return;
    }

    var foundAudio = false;
    for (var i = 0; i < wordaudiourls.length; i++) {
        if (wordaudiourls[i].word == word) {
            audio.src = wordaudiourls[i].objectUrl;
            audio.playbackRate = 0.7;
            audio.play();
            foundAudio = true;
            break;
        }
    }

    if (!foundAudio) {
        console.warn('未找到单词对应的音频:', word);
        return;
    }

    var ending_function = function() {
        if (objectUrlMain) {
            audio.src = objectUrlMain;
            audio.playbackRate = 0.9;
            audio.autoplay = false;
        }
        audio.removeEventListener('ended', ending_function);
    };
    
    audio.addEventListener('ended', ending_function);
}

reftext.onclick = function() {handleWordClick()};

function handleWordClick(){
    const activeTextarea = document.activeElement;
    var k=activeTextarea.selectionStart;
    
    reftextval = reftext.value;
    wordlist = reftextval.split(" ");

    var c = 0;
    var i = 0;
    for (i = 0; i < wordlist.length; i++) {
        c += wordlist[i].length;
        if(c >= k){
            playwordind(wordlist[i]);
            //playword(i);
            break;
        }
        c += 1;
      }

}

var soundAllowed = function (stream) {
    permission = true;
    audioContent = new AudioContext({sampleRate: 16000});
    gumStream = stream;
    audioStream = audioContent.createMediaStreamSource( stream );
    rec = new Recorder(audioStream,{numChannels:1})

	//start the recording process
	rec.record()
}

var soundNotAllowed = function (error) {
    h.innerHTML = "You must allow your microphone.";
    console.log(error);
}

//function for onclick of hear pronunciation button - 修改为使用app项目的TTS功能
hbutton.onclick = function () {
    reftextval = reftext.value.trim();
    
    // 检查文本是否为空
    if (!reftextval) {
        alert("请输入要合成的文本！");
        return false;
    }
    
    var selectedVoice = document.getElementById('voice-select').value; // 获取选中的音色
    var selectedVoiceName = document.getElementById('voice-select').options[document.getElementById('voice-select').selectedIndex].text;
    
    // 检查是否已经合成过相同文本和音色的组合
    var isDuplicate = false;
    for (var i = 0; i < synthesizedAudios.length; i++) {
        if (synthesizedAudios[i].text === reftextval && synthesizedAudios[i].voice === selectedVoice) {
            isDuplicate = true;
            break;
        }
    }
    
    if (isDuplicate) {
        alert("这段文本已经用该音色合成过了。请选择其他音色或修改文本。");
        return false;
    }
    
    document.getElementById("ttsloader").style.display = "block";

    var request = new XMLHttpRequest();
    request.open('POST', '/tts/synthesize', true);

    // Callback function for when request completes
    request.onload = () => {
        console.log("TTS合成请求响应接收完成");
        document.getElementById("ttsloader").style.display = "none";
        
        try {
            var data = JSON.parse(request.responseText);
            
            if (data.success) {
                console.log("TTS合成成功");
                // 将十六进制字符串转换回二进制数据
                const audioBytes = new Uint8Array(data.audio_data.match(/[\da-f]{2}/gi).map(h => parseInt(h, 16)));
                const audioBlob = new Blob([audioBytes], {type: data.content_type});
                
                // 创建音频URL
                var objectUrl = URL.createObjectURL(audioBlob);
                
                // 保存到已合成音频数组
                synthesizedAudios.push({
                    text: reftextval,
                    voice: selectedVoice,
                    voiceName: selectedVoiceName,
                    audioUrl: objectUrl,
                    contentType: data.content_type
                });
                
                // 更新显示所有已合成的音频
                updateAudioList();
                
                // 当前播放的音频URL
                objectUrlMain = objectUrl;
            } else {
                console.error("TTS生成失败:", data.error);
                alert("语音合成失败: " + (data.error || "未知错误"));
            }
        } catch (e) {
            console.error("解析TTS响应时出错:", e);
            alert("语音合成过程中出错，请重试");
        }
    };
    
    request.onerror = function() {
        document.getElementById("ttsloader").style.display = "none";
        console.error("TTS请求失败");
        alert("语音合成请求失败，请检查网络连接");
    };
    
    const dat = new FormData();
    dat.append("text", reftextval);    
    dat.append("voice", selectedVoice);
    
    //send request
    console.log("发送TTS合成请求，文本:", reftextval);
    request.send(dat);

    return false;
}

// 更新音频列表显示
function updateAudioList() {
    // 清空已有内容
    ttsList.innerHTML = '';
    
    // 如果没有合成的音频，不显示任何内容
    if (synthesizedAudios.length === 0) {
        return;
    }
    
    // 创建音频列表容器
    var audioListContainer = document.createElement('div');
    audioListContainer.className = 'audio-list-container';
    
    // 创建标题
    var title = document.createElement('div');
    title.className = 'audio-list-title';
    title.innerText = '已合成的音频';
    audioListContainer.appendChild(title);
    
    // 添加所有合成的音频
    for (var i = 0; i < synthesizedAudios.length; i++) {
        var audioItem = synthesizedAudios[i];
        
        var audioContainer = document.createElement('div');
        audioContainer.className = 'audio-container';
        
        // 创建音频标题
        var audioTitle = document.createElement('div');
        audioTitle.className = 'audio-title';
        audioTitle.innerText = '音色: ' + audioItem.voiceName;
        audioContainer.appendChild(audioTitle);
        
        // 创建音频元素
        var au = document.createElement('audio');
        au.controls = true;
        au.src = audioItem.audioUrl;
        if (i === synthesizedAudios.length - 1) {
            au.autoplay = true;  // 只有最新合成的音频自动播放
            au.id = "ttsaudio";  // 只给最新的音频设置ID
        }
        
        audioContainer.appendChild(au);
        
        // 添加到列表
        audioListContainer.appendChild(audioContainer);
    }
    
    // 添加到页面
    ttsList.appendChild(audioListContainer);
}

function getttsforword(word, voice){
    var request = new XMLHttpRequest();
    request.open('POST', '/tts/synthesize', true);

    // Callback function for when request completes
    request.onload = () => {
        var data = JSON.parse(request.responseText);
        
        if (data.success) {
            // 将十六进制字符串转换回二进制数据
            const audioBytes = new Uint8Array(data.audio_data.match(/[\da-f]{2}/gi).map(h => parseInt(h, 16)));
            const audioBlob = new Blob([audioBytes], {type: data.content_type});
            
            // 创建音频URL
            var objectUrl = URL.createObjectURL(audioBlob);
            wordaudiourls.push({word, objectUrl});
        }
    }
    
    const dat = new FormData();
    dat.append("text", word);    
    dat.append("voice", voice);
    
    //send request
    request.send(dat);
}

//function for onclick of get tongue twister button
ttbutton.onclick = function () {
    console.log("点击获取绕口令按钮");
    var request = new XMLHttpRequest();
    request.open('POST', '/gettonguetwister', true);

    // Callback function for when request completes
    request.onload = () => {
        console.log("绕口令请求响应接收完成:", request.responseText);
        try {
            // Extract JSON data from request
            const data = JSON.parse(request.responseText);
            console.log("解析的绕口令数据:", data);
            reftextval = data.tt;
            reftext.value = reftextval;
            reftext.innerText = reftextval;
        } catch (e) {
            console.error("解析绕口令响应时出错:", e);
        }
    }
    
    request.onerror = function() {
        console.error("绕口令请求失败");
    };
    
    //send request
    console.log("发送绕口令请求");
    request.send();

    return false;
}

//function for handling main button clicks
document.getElementById('buttonmic').onclick = function () {
   
    if (reftext.value.length == 0){
        alert("参考文本不能为空！");
    }
    else{
        if (stop) {
            window.location.reload();
        }
        else if (start) {

            start = false;
            stop = true;
            this.innerHTML = "<span class='fa fa-refresh'></span>刷新";
            this.className = "green-button";
            rec.stop();
    
            //stop microphone access
            gumStream.getAudioTracks()[0].stop();
    
            //create the wav blob and pass it on to createDownloadLink
            rec.exportWAV(createDownloadLink);

            // 恢复获取绕口令按钮状态
            ttbutton.disabled = false;
            ttbutton.className = "blue-button";
        }
        else {
            if (!permission) {
                navigator.mediaDevices.getUserMedia({audio:true})
                    .then(soundAllowed)
                    .catch(soundNotAllowed);
            }

            start = true;
            reftext.readonly = true;
            reftext.disabled = true;
            ttbutton.disabled = true;
            ttbutton.style.display = "none";  // 隐藏获取绕口令按钮
            reftextval = reftext.value;
    
            this.innerHTML = "<span class='fa fa-stop'></span>停止";
            this.className = "red-button";
        }
    }
    };
    

function fillDetails(words){
    for (var wi in words){
        var w = words[wi];
        var countp = 0;

        if(w.ErrorType == "Omission"){
            omittedwords += w.Word;
            omittedwords += ', ';
            
            var tdda = document.createElement('td');
            tdda.innerText = '-';
            phonemerow.appendChild(tdda);

            var tddb = document.createElement('td');
            tddb.innerText = '-';
            scorerow.appendChild(tddb);

            var tdw = document.createElement('td');
            tdw.innerText = w.Word;
            tdw.style.backgroundColor = "orange"; 
            wordrow.appendChild(tdw);
        }
        else if(w.ErrorType == "Insertion"){
                insertedwords += w.Word;
                insertedwords += ', ';
        }
        else if(w.ErrorType == "None" || w.ErrorType == "Mispronunciation"){
            for (var phonei in w.Phonemes){
                var p =w.Phonemes[phonei]

                var tdp = document.createElement('td');
                tdp.innerText = p.Phoneme;
                if(p.AccuracyScore >= phthreshold1){
                    tdp.style.backgroundColor = "green";  
                }
                else if(p.AccuracyScore >= phthreshold2){
                    tdp.style.backgroundColor = "lightgreen";  
                }
                else if(p.AccuracyScore >= phthreshold3){
                    tdp.style.backgroundColor = "yellow";  
                }
                else{
                    tdp.style.backgroundColor = "red"; 
                }
                phonemerow.appendChild(tdp);

                var tds = document.createElement('td');
                tds.innerText = p.AccuracyScore;
                scorerow.appendChild(tds);
                countp = Number(phonei)+1;
            }
            var tdw = document.createElement('td');
            tdw.innerText = w.Word;
            var x = document.createElement("SUP");
            var t = document.createTextNode(countp);
            x.appendChild(t);
            tdw.appendChild(x);
            if(w.ErrorType == "Mispronunciation"){
                tdw.style.backgroundColor = "orange"; 
            }
            wordrow.appendChild(tdw);
        }
    }
}

function fillData(data){
    accuracyscore.innerHTML = data.NBest[0].AccuracyScore;
    fluencyscore.innerHTML = data.NBest[0].FluencyScore;
    completenessscore.innerHTML = data.NBest[0].CompletenessScore;
    prosodyscore.innerHTML = data.NBest[0].ProsodyScore;
    pronscore.innerHTML = data.NBest[0].PronScore;
    
    fillDetails(data.NBest[0].Words);
    if(data.NBest[0].Words.some(w => w.ErrorType === "Omission")){
        wordsomitted.innerHTML = omittedwords;
    }
    else{
        wordsomitted.innerHTML = "None";
    }
    if(insertedwords != ""){
        wordsinserted.style.display = "";
        document.getElementById("wih").style.display = "";
        wordsinserted.innerHTML = insertedwords;
    }
    
    // 处理音素信息
    if (data.phonemes_info) {
        displayPhonemesInfo(data.phonemes_info);
    }

    // 获取LLM反馈
    if (data.RecognitionStatus === "Success" && data.NBest && data.NBest.length > 0) {
        getLLMFeedback(data.NBest[0], reftextval);
    }
}

function createDownloadLink(blob) {
    
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('p');

    //add controls to the <audio> element
    au.controls = true;
    au.src = url;

    //add the new audio element to li
    li.appendChild(au);
        
    //add the li element to the ol
    if(recordingsList.hasChildNodes()){
        recordingsList.lastChild.remove();
    }
    recordingsList.appendChild(li);
    
    t1 = performance.now();

    var fd = new FormData();
    fd.append("audio_data",blob, "file");
    fd.append("reftext",reftextval);
    
    document.getElementById("recordloader").style.display = "block";

    var oReq = new XMLHttpRequest();
    oReq.open("POST", "/ackaud", true);
    oReq.onload = function(oEvent) {
        
        if (oReq.status == 200) {
            try{
                var data = JSON.parse(oReq.response);
            }
            catch{
                document.getElementById("recordloader").style.display = "none";
                console.log("Error:", oReq.response);
                return;
            }
            
            document.getElementById("recordloader").style.display = "none";
            document.getElementById("summarytable").style.display = "flex";
            fillData(data);            
            t0 = 0;
            t1 = 0;
        }
        
    };
    
    oReq.send(fd);
}

// 获取LLM反馈的函数
function getLLMFeedback(assessment_data, reference_text) {
    const container = document.getElementById('llm-feedback-container');
    const loadingDiv = document.getElementById('llm-loading');
    const feedbackDiv = document.getElementById('llm-feedback');
    
    // 显示容器和加载提示
    container.style.display = 'block';
    loadingDiv.style.display = 'flex';
    feedbackDiv.innerHTML = '';
    
    const request = new XMLHttpRequest();
    request.open('POST', '/get_llm_feedback', true);
    request.setRequestHeader('Content-Type', 'application/json');

    request.onload = function() {
        // 隐藏加载提示
        loadingDiv.style.display = 'none';
        
        if (request.status === 200) {
            try {
                const response = JSON.parse(request.responseText);
                if (response.success) {
                    displayLLMFeedback(response.llm_feedback);
                } else {
                    console.error("获取LLM反馈失败:", response.error);
                    feedbackDiv.innerHTML = '<p class="error-message">获取发音指导失败，请稍后重试</p>';
                }
            } catch (e) {
                console.error("解析LLM响应时出错:", e);
                feedbackDiv.innerHTML = '<p class="error-message">解析反馈时出错，请稍后重试</p>';
            }
        } else {
            console.error("LLM请求失败:", request.status);
            feedbackDiv.innerHTML = '<p class="error-message">请求失败，请稍后重试</p>';
        }
    };

    request.onerror = function() {
        // 隐藏加载提示
        loadingDiv.style.display = 'none';
        console.error("LLM请求出错");
        feedbackDiv.innerHTML = '<p class="error-message">网络错误，请稍后重试</p>';
    };

    // 发送请求
    request.send(JSON.stringify({
        assessment_data: assessment_data,
        reference_text: reference_text
    }));
}

// 展示LLM反馈的函数
function displayLLMFeedback(feedback) {
    const feedbackDiv = document.getElementById('llm-feedback');
    
    // 先将内容初始化为空
    feedbackDiv.innerHTML = '';
    
    // 使用字符累积器而不是直接往DOM添加
    let textAccumulator = '';
    let i = 0;
    const speed = 20; // 打字速度
    const text = feedback;
    
    // 打字机效果处理
    function typeWriter() {
        if (i < text.length) {
            // 累积字符
            textAccumulator += text.charAt(i);
            
            // 使用marked.js解析为HTML并显示
            try {
                feedbackDiv.innerHTML = marked.parse(textAccumulator);
            } catch (e) {
                // 如果解析出错，就直接显示原文
                feedbackDiv.innerHTML = textAccumulator;
                console.error('Markdown解析错误:', e);
            }
            
            i++;
            setTimeout(typeWriter, speed);
        } else {
            // 打字结束后，确保最终内容被正确渲染为Markdown
            try {
                feedbackDiv.innerHTML = marked.parse(text);
            } catch (e) {
                feedbackDiv.innerHTML = text;
                console.error('最终Markdown解析错误:', e);
            }
            
            // 移除打字机效果
            feedbackDiv.classList.remove('loading-text');
            feedbackDiv.classList.add('done-text');
            
            // 添加链接点击处理
            handleMarkdownLinks();
        }
    }
    
    // 处理Markdown中的链接
    function handleMarkdownLinks() {
        const links = feedbackDiv.querySelectorAll('a');
        links.forEach(link => {
            // 确保外部链接在新窗口打开
            if (link.hostname !== window.location.hostname) {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }
        });
    }
    
    // 开始打字效果
    typeWriter();
}

// 添加音色选择变化事件监听
document.addEventListener('DOMContentLoaded', function() {
    var voiceSelect = document.getElementById('voice-select');
    if (voiceSelect) {
        voiceSelect.addEventListener('change', function() {
            if (this.value === 'clone_voice') {
                // 如果选择了克隆音色选项，跳转到克隆音色页面
                window.location.href = '/tts_clone';
                
                // 重置选择框，选中之前选择的值
                setTimeout(function() {
                    if (voiceSelect.selectedIndex > 0) {
                        voiceSelect.selectedIndex = voiceSelect.selectedIndex - 1;
                    } else {
                        voiceSelect.selectedIndex = 0;
                    }
                }, 100);
            }
        });
    }
});

// 显示音素信息的函数
function displayPhonemesInfo(phonemesInfo) {
    const demoContainer = document.getElementById('phoneme-demo-container');
    const consonantsList = document.getElementById('consonants-list');
    const vowelsList = document.getElementById('vowels-list');
    const tonesList = document.getElementById('tones-list');
    
    // 清空现有内容
    consonantsList.innerHTML = '';
    vowelsList.innerHTML = '';
    tonesList.innerHTML = '';
    
    // 显示容器
    demoContainer.style.display = 'block';
    
    // 填充声母列表
    if (phonemesInfo.consonants && phonemesInfo.consonants.length > 0) {
        phonemesInfo.consonants.forEach(consonant => {
            const item = document.createElement('div');
            item.className = 'phoneme-item';
            item.textContent = consonant;
            item.setAttribute('data-phoneme', consonant);
            item.setAttribute('data-type', 'consonant');
            item.onclick = function() { playPhonemeVideo(consonant); };
            consonantsList.appendChild(item);
        });
    } else {
        consonantsList.innerHTML = '<p>未发现问题声母</p>';
    }
    
    // 填充韵母列表
    if (phonemesInfo.vowels && phonemesInfo.vowels.length > 0) {
        phonemesInfo.vowels.forEach(vowel => {
            const item = document.createElement('div');
            item.className = 'phoneme-item';
            item.textContent = vowel;
            item.setAttribute('data-phoneme', vowel);
            item.setAttribute('data-type', 'vowel');
            item.onclick = function() { playPhonemeVideo(vowel); };
            vowelsList.appendChild(item);
        });
    } else {
        vowelsList.innerHTML = '<p>未发现问题韵母</p>';
    }
    
    // 填充声调列表
    if (phonemesInfo.tones && phonemesInfo.tones.length > 0) {
        phonemesInfo.tones.forEach(tone => {
            const item = document.createElement('div');
            item.className = 'phoneme-item';
            item.textContent = '声调' + tone;
            item.setAttribute('data-phoneme', 'tone' + tone);
            item.setAttribute('data-type', 'tone');
            item.onclick = function() { playPhonemeVideo('tone' + tone); };
            tonesList.appendChild(item);
        });
    } else {
        tonesList.innerHTML = '<p>未发现问题声调</p>';
    }
    
    // 添加标签切换功能
    const tabs = document.querySelectorAll('.phoneme-tabs .tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有标签和内容的活动状态
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.phoneme-list').forEach(list => list.classList.remove('active'));
            
            // 添加当前标签和对应内容的活动状态
            this.classList.add('active');
            const tabName = this.getAttribute('data-tab');
            document.getElementById(tabName + '-list').classList.add('active');
        });
    });
}

// 播放音素示范视频
function playPhonemeVideo(phoneme) {
    const videoPlayer = document.getElementById('phoneme-video');
    const instruction = document.querySelector('#video-player .instruction');
    
    // 移除所有活动状态
    document.querySelectorAll('.phoneme-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 添加当前音素的活动状态
    document.querySelector(`[data-phoneme="${phoneme}"]`).classList.add('active');
    
    // 构建视频URL，使用API端点
    const videoUrl = `/get_phoneme_video/${phoneme}`;
    
    // 显示视频播放器，隐藏指导文字
    videoPlayer.style.display = 'block';
    instruction.style.display = 'none';
    
    // 检查是否已缓存该视频
    if (cachedVideos[phoneme]) {
        videoPlayer.src = cachedVideos[phoneme];
        videoPlayer.play();
        return;
    }
    
    // 设置加载中的提示
    videoPlayer.poster = '/static/img/loading.gif';
    
    // 加载并播放视频
    videoPlayer.src = videoUrl;
    videoPlayer.load();
    
    // 视频加载成功后播放
    videoPlayer.onloadeddata = function() {
        videoPlayer.poster = '';
        videoPlayer.play();
        // 缓存视频URL
        cachedVideos[phoneme] = videoUrl;
    };
    
    // 处理视频加载错误
    videoPlayer.onerror = function() {
        console.error(`无法加载视频: ${videoUrl}`);
        instruction.textContent = `无法加载"${phoneme}"的示范视频`;
        instruction.style.display = 'block';
        videoPlayer.style.display = 'none';
    };
}