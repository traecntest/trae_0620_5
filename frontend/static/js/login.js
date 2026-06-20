document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phone');
    const codeInput = document.getElementById('code');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const loginBtn = document.getElementById('loginBtn');
    
    let countdown = 0;
    let countdownTimer = null;

    function validatePhone(phone) {
        return /^1\d{10}$/.test(phone);
    }

    function updateCountdown() {
        if (countdown > 0) {
            sendCodeBtn.textContent = `${countdown}秒后重新获取`;
            sendCodeBtn.disabled = true;
            countdown--;
        } else {
            sendCodeBtn.textContent = '获取验证码';
            sendCodeBtn.disabled = false;
            clearInterval(countdownTimer);
        }
    }

    sendCodeBtn.addEventListener('click', async function() {
        const phone = phoneInput.value.trim();
        
        if (!validatePhone(phone)) {
            showToast('请输入正确的11位手机号码');
            return;
        }

        try {
            await apiRequest('/auth/send-sms', 'POST', { phone }, false);
            showToast('验证码已发送，测试验证码：123456');
            countdown = 60;
            updateCountdown();
            countdownTimer = setInterval(updateCountdown, 1000);
        } catch (error) {
            showToast(error.message || '发送验证码失败');
        }
    });

    loginBtn.addEventListener('click', async function() {
        const phone = phoneInput.value.trim();
        const code = codeInput.value.trim();

        if (!validatePhone(phone)) {
            showToast('请输入正确的11位手机号码');
            return;
        }

        if (!code) {
            showToast('请输入验证码');
            return;
        }

        try {
            const data = await apiRequest('/auth/login-sms', 'POST', { phone, code }, false);
            setAuthToken(data.access_token);
            setUserInfo(data.user);
            showToast('登录成功');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } catch (error) {
            showToast(error.message || '登录失败');
        }
    });
});
