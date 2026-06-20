let orderList = [];

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) {
        return;
    }

    const backBtn = document.getElementById('backBtn');
    const orderListEl = document.getElementById('orderList');

    loadOrders();

    if (backBtn) {
        backBtn.addEventListener('click', function() {
            navigateTo('/');
        });
    }
});

async function loadOrders() {
    try {
        const data = await apiRequest('/orders', 'GET');
        orderList = data.orders || data.list || [];
        renderOrders();
    } catch (error) {
        showToast(error.message || '加载订单失败');
    }
}

function renderOrders() {
    const orderListEl = document.getElementById('orderList');
    if (!orderListEl) return;

    if (orderList.length === 0) {
        orderListEl.innerHTML = '<div class="empty-state">暂无订单</div>';
        return;
    }

    orderListEl.innerHTML = '';

    orderList.forEach(order => {
        const orderCard = document.createElement('div');
        orderCard.className = 'order-card';
        
        const statusClass = getStatusClass(order.status);
        const statusName = getStatusName(order.status);
        const mealPeriodName = getMealPeriodName(order.meal_period);
        const deliveryTypeName = (order.dining_type === 'takeout' || order.dining_type === 'take_out') ? '外带' : '堂食';

        const itemsHtml = order.items.map(item => `
            <div class="order-item">
                <span>${item.dish_name}</span>
                <span>×${item.quantity}</span>
                <span>${formatCurrency(item.unit_price || item.price)}</span>
            </div>
        `).join('');

        const pickCodeDisplay = order.pickup_code && order.status === 'confirmed' 
            ? `<div class="pickup-code" onclick="showPickupCode('${order.pickup_code}')">
                 取餐码：<span class="code-text">${order.pickup_code}</span>
               </div>`
            : '';

        const cancelBtn = (order.status === 'pending' || order.status === 'confirmed')
            ? `<button class="btn-cancel" onclick="cancelOrder(${order.id})">取消订单</button>`
            : '';

        orderCard.innerHTML = `
            <div class="order-header">
                <span class="order-date">${formatDate(order.created_at)}</span>
                <span class="order-status ${statusClass}">${statusName}</span>
            </div>
            <div class="order-meta">
                <span>${mealPeriodName}</span>
                <span>·</span>
                <span>${deliveryTypeName}</span>
            </div>
            <div class="order-items">
                ${itemsHtml}
            </div>
            ${pickCodeDisplay}
            <div class="order-footer">
                <span class="order-total">合计：${formatCurrency(order.total_amount)}</span>
                ${cancelBtn}
            </div>
        `;

        orderListEl.appendChild(orderCard);
    });
}

function showPickupCode(code) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    };
    modal.innerHTML = `
        <div class="modal-content pickup-code-modal">
            <div class="modal-title">取餐码</div>
            <div class="pickup-code-large">${code}</div>
            <button class="btn-primary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
        </div>
    `;
    document.body.appendChild(modal);
}

async function cancelOrder(orderId) {
    if (!confirm('确定要取消这个订单吗？')) {
        return;
    }

    try {
        await apiRequest(`/orders/${orderId}/cancel`, 'PUT');
        showToast('订单已取消');
        loadOrders();
    } catch (error) {
        showToast(error.message || '取消订单失败');
    }
}
