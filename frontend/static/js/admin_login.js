document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');

    loginBtn.addEventListener('click', async function() {
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username) {
            showToast('请输入用户名');
            return;
        }

        if (!password) {
            showToast('请输入密码');
            return;
        }

        try {
            const data = await apiRequest('/auth/login-admin', 'POST', { username, password }, false);
            localStorage.setItem('admin_token', data.access_token);
            localStorage.setItem('admin_info', JSON.stringify(data.admin));
            showToast('登录成功');
            setTimeout(() => {
                window.location.href = '/admin/dashboard';
            }, 1000);
        } catch (error) {
            showToast(error.message || '登录失败');
        }
    });
});
