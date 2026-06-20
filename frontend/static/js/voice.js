class VoiceAssistant {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isSupported = 'MediaRecorder' in window && 'getUserMedia' in navigator.mediaDevices;
    }

    async startRecording() {
        if (!this.isSupported) {
            showToast('您的浏览器不支持录音功能');
            return false;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.audioChunks.push(e.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(track => track.stop());
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processAudio(audioBlob);
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            return true;
        } catch (error) {
            console.error('录音启动失败:', error);
            showToast('无法访问麦克风，请检查权限设置');
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
    }

    async processAudio(audioBlob) {
        try {
            showToast('正在识别语音...');
            
            const result = await apiUpload('/voice/recognize', audioBlob);
            
            if (result && result.text) {
                speak(`识别结果：${result.text}`);
                this.handleVoiceCommand(result.parsed, result.text);
            } else {
                showToast('未能识别语音内容，请重试');
                speak('未能识别语音内容，请重试');
            }
        } catch (error) {
            console.error('语音识别失败:', error);
            showToast('语音识别失败，请重试');
        }
    }

    handleVoiceCommand(parsed, rawText) {
        if (!parsed || !parsed.dishes || parsed.dishes.length === 0) {
            showToast('未识别到菜品，请重新说出您要的菜品');
            speak('未识别到菜品，请重新说出您要的菜品');
            return;
        }

        const dishNames = parsed.dishes.map(d => d.dish_name).join('、');
        const periodName = getMealPeriodName(parsed.period);
        
        showToast(`识别成功：${periodName} ${dishNames}`);
        speak(`已为您选择${periodName}的${dishNames}，请确认下单`);

        if (window.currentCart) {
            window.currentCart.period = parsed.period;
            
            parsed.dishes.forEach(parsedDish => {
                const existingItem = window.currentCart.items.find(
                    item => item.dish_id === parsedDish.dish_id
                );
                
                if (existingItem) {
                    existingItem.quantity += parsedDish.quantity;
                } else {
                    if (window.dishList) {
                        const dish = window.dishList.find(d => d.id === parsedDish.dish_id);
                        if (dish) {
                            window.currentCart.items.push({
                                dish_id: dish.id,
                                name: dish.name,
                                price: dish.price,
                                quantity: parsedDish.quantity,
                                image: dish.image
                            });
                        }
                    }
                }
            });
            
            if (typeof updateCartDisplay === 'function') {
                updateCartDisplay();
            }
        }
    }

    toggleRecording(buttonElement) {
        if (!this.isRecording) {
            this.startRecording().then(success => {
                if (success) {
                    buttonElement.classList.add('recording');
                    buttonElement.innerHTML = '🔴';
                    speak('请说话');
                }
            });
        } else {
            this.stopRecording();
            buttonElement.classList.remove('recording');
            buttonElement.innerHTML = '🎤';
        }
    }
}

const voiceAssistant = new VoiceAssistant();

function initVoiceButton() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            voiceAssistant.toggleRecording(voiceBtn);
        });
    }
}
