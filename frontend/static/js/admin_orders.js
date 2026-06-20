function getAdminToken() {
    return localStorage.getItem('admin_token');
}

function checkAdminAuth() {
    const token = getAdminToken();
    if (!token) {
        window.location.href = '/admin/login';
        return false;
    }
    return true;
}

async function adminApiRequest(url, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    const token = getAdminToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
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
                localStorage.removeItem('admin_token');
                localStorage.removeItem('admin_info');
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

let orderList = [];
let currentFilters = {
    status: 'all',
    date: ''
};

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAdminAuth()) {
        return;
    }

    const sidebarItems = document.querySelectorAll('.sidebar-item');
    const logoutBtn = document.getElementById('logoutBtn');
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    const exportBtn = document.getElementById('exportBtn');
    const detailModal = document.getElementById('detailModal');
    const closeDetailBtn = document.getElementById('closeDetailBtn');

    sidebarItems.forEach(item => {
        item.addEventListener('click', function() {
            const href = this.dataset.href;
            if (href) {
                window.location.href = href;
            }
        });
    });

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_info');
            showToast('已退出登录');
            setTimeout(() => {
                window.location.href = '/admin/login';
            }, 1000);
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentFilters.status = this.value;
            loadOrders();
        });
    }

    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            currentFilters.date = this.value;
            loadOrders();
        });
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportOrders);
    }

    if (closeDetailBtn) {
        closeDetailBtn.addEventListener('click', function() {
            detailModal.style.display = 'none';
        });
    }

    detailModal.addEventListener('click', function(e) {
        if (e.target === detailModal) {
            detailModal.style.display = 'none';
        }
    });

    loadOrders();
});

async function loadOrders() {
    try {
        let url = '/orders/all';
        const params = [];
        
        if (currentFilters.status && currentFilters.status !== 'all') {
            params.push(`status=${currentFilters.status}`);
        }
        if (currentFilters.date) {
            params.push(`date=${currentFilters.date}`);
        }
        
        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        const data = await adminApiRequest(url, 'GET');
        orderList = data.orders || data.list || [];
        renderOrderTable();
    } catch (error) {
        showToast(error.message || '加载订单列表失败');
    }
}

function renderOrderTable() {
    const tableBody = document.querySelector('#orderTable tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    orderList.forEach(order => {
        const statusClass = getStatusClass(order.status);
        const statusName = getStatusName(order.status);
        const mealPeriodName = getMealPeriodName(order.meal_period);
        const deliveryTypeName = (order.dining_type === 'takeout' || order.dining_type === 'take_out') ? '外带' : '堂食';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${order.id}</td>
            <td>${order.user_name || '-'}</td>
            <td>${order.user_phone || '-'}</td>
            <td>${formatDate(order.created_at)}</td>
            <td>${mealPeriodName}</td>
            <td>${deliveryTypeName}</td>
            <td>${formatCurrency(order.total_amount)}</td>
            <td><span class="status-tag ${statusClass}">${statusName}</span></td>
            <td>${order.pickup_code || '-'}</td>
            <td>
                <button class="btn-view" onclick="viewOrderDetail(${order.id})">详情</button>
                ${order.status === 'pending' ? `<button class="btn-confirm" onclick="updateOrderStatus(${order.id}, 'confirmed')">确认</button>` : ''}
                ${order.status === 'confirmed' ? `<button class="btn-complete" onclick="updateOrderStatus(${order.id}, 'completed')">完成</button>` : ''}
                ${(order.status === 'pending' || order.status === 'confirmed') ? `<button class="btn-cancel" onclick="updateOrderStatus(${order.id}, 'cancelled')">取消</button>` : ''}
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

function viewOrderDetail(orderId) {
    const order = orderList.find(o => o.id === orderId);
    if (!order) return;

    const statusClass = getStatusClass(order.status);
    const statusName = getStatusName(order.status);
    const mealPeriodName = getMealPeriodName(order.meal_period);
    const deliveryTypeName = order.delivery_type === 'takeout' ? '外带' : '堂食';

    document.getElementById('detailOrderId').textContent = order.id;
    document.getElementById('detailUserName').textContent = order.user_name || '-';
    document.getElementById('detailUserPhone').textContent = order.user_phone || '-';
    document.getElementById('detailCreatedAt').textContent = formatDate(order.created_at);
    document.getElementById('detailMealPeriod').textContent = mealPeriodName;
    document.getElementById('detailDeliveryType').textContent = deliveryTypeName;
    document.getElementById('detailStatus').className = `status-tag ${statusClass}`;
    document.getElementById('detailStatus').textContent = statusName;
    document.getElementById('detailPickupCode').textContent = order.pickup_code || '-';
    document.getElementById('detailTotal').textContent = formatCurrency(order.total_amount);

    const itemsContainer = document.getElementById('detailItems');
    itemsContainer.innerHTML = '';

    order.items.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.className = 'detail-item';
        itemEl.innerHTML = `
            <span>${item.dish_name}</span>
            <span>×${item.quantity}</span>
            <span>${formatCurrency(item.unit_price || item.price)}</span>
            <span>${formatCurrency(item.subtotal || (item.unit_price || item.price) * item.quantity)}</span>
        `;
        itemsContainer.appendChild(itemEl);
    });

    document.getElementById('detailModal').style.display = 'flex';
}

async function updateOrderStatus(orderId, status) {
    const statusMessages = {
        'confirmed': '确认订单',
        'completed': '完成订单',
        'cancelled': '取消订单'
    };

    if (!confirm(`确定要${statusMessages[status]}吗？`)) {
        return;
    }

    try {
        await adminApiRequest(`/orders/${orderId}/status`, 'PUT', { status });
        showToast(`${statusMessages[status]}成功`);
        loadOrders();
    } catch (error) {
        showToast(error.message || '操作失败');
    }
}

async function exportOrders() {
    try {
        let url = '/orders/export';
        const params = [];
        
        if (currentFilters.status && currentFilters.status !== 'all') {
            params.push(`status=${currentFilters.status}`);
        }
        if (currentFilters.date) {
            params.push(`date=${currentFilters.date}`);
        }
        
        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        const token = getAdminToken();
        const response = await fetch(`${API_BASE}${url}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('导出失败');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `orders_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        showToast('导出成功');
    } catch (error) {
        showToast(error.message || '导出失败');
    }
}
