const API_BASE = '/api/v1';

function getAuthToken() {
    return localStorage.getItem('access_token');
}

function setAuthToken(token) {
    localStorage.setItem('access_token', token);
}

function clearAuthToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
}

function getUserInfo() {
    const info = localStorage.getItem('user_info');
    return info ? JSON.parse(info) : null;
}

function setUserInfo(info) {
    localStorage.setItem('user_info', JSON.stringify(info));
}

async function apiRequest(url, method = 'GET', data = null, includeAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (includeAuth) {
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    const options = {
        method,
        headers
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${url}`, options);
        const result = await response.json();
        
        if (result.code !== 200) {
            if (result.code === 401) {
                clearAuthToken();
                window.location.href = '/login';
            }
            throw new Error(result.message || '请求失败');
        }
        
        return result.data;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}

async function apiUpload(url, file, includeAuth = true) {
    const headers = {};
    
    if (includeAuth) {
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    const formData = new FormData();
    formData.append('audio', file);
    
    const options = {
        method: 'POST',
        headers,
        body: formData
    };
    
    try {
        const response = await fetch(`${API_BASE}${url}`, options);
        const result = await response.json();
        
        if (result.code !== 200) {
            throw new Error(result.message || '请求失败');
        }
        
        return result.data;
    } catch (error) {
        console.error('上传错误:', error);
        throw error;
    }
}

function showToast(message, duration = 2000) {
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function speak(text, rate = 0.9) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'zh-CN';
        utterance.rate = rate;
        utterance.pitch = 1;
        utterance.volume = 1;
        window.speechSynthesis.speak(utterance);
    }
}

function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function getMealPeriodName(period) {
    const names = {
        'breakfast': '早餐',
        'lunch': '午餐',
        'dinner': '晚餐'
    };
    return names[period] || period;
}

function getStatusName(status) {
    const names = {
        'pending': '待确认',
        'confirmed': '已确认',
        'completed': '已完成',
        'cancelled': '已取消'
    };
    return names[status] || status;
}

function getStatusClass(status) {
    return `status-${status}`;
}

function getDishEmoji(category) {
    const emojis = {
        'breakfast': ['🍞', '🥚', '🥛', '🍜', '🥟'],
        'lunch': ['🍚', '🍖', '🐟', '🥬', '🍲'],
        'dinner': ['🍚', '🥗', '🥘', '🍜', '🥣']
    };
    const list = emojis[category] || ['🍽️'];
    return list[Math.floor(Math.random() * list.length)];
}

function checkAuth() {
    const token = getAuthToken();
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

function logout() {
    clearAuthToken();
    showToast('已退出登录');
    setTimeout(() => {
        window.location.href = '/login';
    }, 1000);
}

function navigateTo(url) {
    window.location.href = url;
}

function getAdminToken() {
    return localStorage.getItem('admin_token');
}

function setAdminToken(token) {
    localStorage.setItem('admin_token', token);
}

function clearAdminToken() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_info');
}

function getAdminInfo() {
    const info = localStorage.getItem('admin_info');
    return info ? JSON.parse(info) : null;
}

function setAdminInfo(info) {
    localStorage.setItem('admin_info', JSON.stringify(info));
}

async function adminApiRequest(url, method = 'GET', data = null, includeAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (includeAuth) {
        const token = getAdminToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    const options = {
        method,
        headers
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${url}`, options);
        const result = await response.json();
        
        if (result.code !== 200) {
            if (result.code === 401) {
                clearAdminToken();
                window.location.href = '/admin/login';
            }
            throw new Error(result.message || '请求失败');
        }
        
        return result.data;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}

function checkAdminAuth() {
    const token = getAdminToken();
    if (!token) {
        window.location.href = '/admin/login';
        return false;
    }
    return true;
}

function adminLogout() {
    clearAdminToken();
    showToast('已退出登录');
    setTimeout(() => {
        window.location.href = '/admin/login';
    }, 1000);
}
