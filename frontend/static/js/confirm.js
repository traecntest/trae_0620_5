let currentCart = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) {
        return;
    }

    const cartItemsEl = document.getElementById('cartItems');
    const totalPriceEl = document.getElementById('totalPrice');
    const deliveryTypeEls = document.querySelectorAll('input[name="deliveryType"]');
    const mealPeriodEls = document.querySelectorAll('input[name="mealPeriod"]');
    const submitBtn = document.getElementById('submitBtn');
    const backBtn = document.getElementById('backBtn');

    loadCart();
    renderCart();

    deliveryTypeEls.forEach(el => {
        el.addEventListener('change', calculateTotal);
    });

    mealPeriodEls.forEach(el => {
        el.addEventListener('change', function() {
            if (currentCart) {
                currentCart.period = this.value;
            }
        });
    });

    if (submitBtn) {
        submitBtn.addEventListener('click', submitOrder);
    }

    if (backBtn) {
        backBtn.addEventListener('click', function() {
            navigateTo('/order');
        });
    }
});

function loadCart() {
    const savedCart = localStorage.getItem('currentCart');
    if (savedCart) {
        currentCart = JSON.parse(savedCart);
    }
    
    if (!currentCart || currentCart.items.length === 0) {
        showToast('购物车为空，请先选择菜品');
        setTimeout(() => navigateTo('/order'), 1500);
        return;
    }

    const mealPeriodEls = document.querySelectorAll('input[name="mealPeriod"]');
    mealPeriodEls.forEach(el => {
        if (el.value === currentCart.period) {
            el.checked = true;
        }
    });
}

function renderCart() {
    const cartItemsEl = document.getElementById('cartItems');
    if (!cartItemsEl || !currentCart) return;

    cartItemsEl.innerHTML = '';

    currentCart.items.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.className = 'cart-item';
        itemEl.innerHTML = `
            <div class="item-info">
                <div class="item-name">${item.name}</div>
                <div class="item-price">${formatCurrency(item.price)} × ${item.quantity}</div>
            </div>
            <div class="item-total">${formatCurrency(item.price * item.quantity)}</div>
        `;
        cartItemsEl.appendChild(itemEl);
    });

    calculateTotal();
}

function calculateTotal() {
    if (!currentCart) return;

    const subtotal = currentCart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const deliveryType = document.querySelector('input[name="deliveryType"]:checked')?.value || 'dine_in';
    const deliveryFee = deliveryType === 'takeout' ? 2 : 0;
    const total = subtotal + deliveryFee;

    const totalPriceEl = document.getElementById('totalPrice');
    if (totalPriceEl) {
        totalPriceEl.textContent = formatCurrency(total);
    }
}

async function submitOrder() {
    if (!currentCart || currentCart.items.length === 0) {
        showToast('购物车为空');
        return;
    }

    const deliveryType = document.querySelector('input[name="deliveryType"]:checked')?.value;
    const mealPeriod = document.querySelector('input[name="mealPeriod"]:checked')?.value;

    if (!deliveryType) {
        showToast('请选择配送方式');
        return;
    }

    if (!mealPeriod) {
        showToast('请选择用餐时段');
        return;
    }

    const orderData = {
        items: currentCart.items.map(item => ({
            dish_id: item.dish_id,
            quantity: item.quantity
        })),
        delivery_type: deliveryType,
        meal_period: mealPeriod
    };

    const forUserId = localStorage.getItem('for_user_id');
    if (forUserId) {
        orderData.for_user_id = parseInt(forUserId);
    }

    try {
        await apiRequest('/orders', 'POST', orderData);
        showToast('订单提交成功');
        localStorage.removeItem('currentCart');
        localStorage.removeItem('for_user_id');
        setTimeout(() => {
            navigateTo('/orders');
        }, 1000);
    } catch (error) {
        showToast(error.message || '提交订单失败');
    }
}
