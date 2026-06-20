document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) {
        return;
    }

    const userInfo = getUserInfo();
    const userNameEl = document.getElementById('userName');
    const todayDateEl = document.getElementById('todayDate');
    const orderBtn = document.getElementById('orderBtn');
    const ordersBtn = document.getElementById('ordersBtn');
    const familyBtn = document.getElementById('familyBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    if (userInfo && userNameEl) {
        userNameEl.textContent = userInfo.name || '用户';
    }

    if (todayDateEl) {
        const today = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
        todayDateEl.textContent = today.toLocaleDateString('zh-CN', options);
    }

    if (orderBtn) {
        orderBtn.addEventListener('click', function() {
            navigateTo('/order');
        });
    }

    if (ordersBtn) {
        ordersBtn.addEventListener('click', function() {
            navigateTo('/orders');
        });
    }

    if (familyBtn) {
        familyBtn.addEventListener('click', function() {
            navigateTo('/family');
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            logout();
        });
    }

    initVoiceButton();
});
