let currentCart = null;
let dishList = [];
let currentCategory = 'all';
let elderList = [];
let selectedElderId = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) {
        return;
    }

    window.currentCart = currentCart;
    window.dishList = dishList;
    window.updateCartDisplay = updateCartDisplay;

    const elderSelect = document.getElementById('elderSelect');
    const categoryBtns = document.querySelectorAll('.category-btn');
    const dishListEl = document.getElementById('dishList');
    const cartCountEl = document.getElementById('cartCount');
    const cartTotalEl = document.getElementById('cartTotal');
    const nextBtn = document.getElementById('nextBtn');
    const backBtn = document.getElementById('backBtn');

    const savedElderId = localStorage.getItem('for_user_id');
    const savedElderName = localStorage.getItem('for_user_name');
    if (savedElderId && savedElderName) {
        selectedElderId = parseInt(savedElderId);
    }

    initCart();
    loadElderList();
    loadDishes();

    if (elderSelect) {
        elderSelect.addEventListener('change', function() {
            selectedElderId = parseInt(this.value);
            localStorage.setItem('for_user_id', selectedElderId);
            const selectedOption = this.options[this.selectedIndex];
            localStorage.setItem('for_user_name', selectedOption.text);
        });
    }

    categoryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            categoryBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            renderDishes();
        });
    });

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (!selectedElderId) {
                showToast('请选择代订老人');
                return;
            }
            if (!currentCart || currentCart.items.length === 0) {
                showToast('请先选择菜品');
                return;
            }
            saveCart();
            navigateTo('/order/confirm');
        });
    }

    if (backBtn) {
        backBtn.addEventListener('click', function() {
            localStorage.removeItem('for_user_id');
            localStorage.removeItem('for_user_name');
            navigateTo('/family');
        });
    }

    initVoiceButton();
});

async function loadElderList() {
    try {
        elderList = await apiRequest('/family/list', 'GET');
        renderElderSelect();
    } catch (error) {
        showToast(error.message || '加载老人列表失败');
    }
}

function renderElderSelect() {
    const elderSelect = document.getElementById('elderSelect');
    if (!elderSelect) return;

    elderSelect.innerHTML = '<option value="">请选择代订老人</option>';

    elderList.forEach(elder => {
        const option = document.createElement('option');
        option.value = elder.id;
        option.textContent = `${elder.name} (${elder.phone})`;
        if (selectedElderId === elder.id) {
            option.selected = true;
        }
        elderSelect.appendChild(option);
    });
}

function initCart() {
    const savedCart = localStorage.getItem('currentCart');
    if (savedCart) {
        currentCart = JSON.parse(savedCart);
    } else {
        currentCart = {
            items: [],
            period: getCurrentMealPeriod()
        };
    }
    updateCartDisplay();
}

function getCurrentMealPeriod() {
    const hour = new Date().getHours();
    if (hour < 10) return 'breakfast';
    if (hour < 16) return 'lunch';
    return 'dinner';
}

async function loadDishes() {
    try {
        dishList = await apiRequest('/dishes', 'GET');
        window.dishList = dishList;
        renderDishes();
    } catch (error) {
        showToast(error.message || '加载菜品失败');
    }
}

function renderDishes() {
    const dishListEl = document.getElementById('dishList');
    if (!dishListEl) return;

    const filteredDishes = currentCategory === 'all' 
        ? dishList 
        : dishList.filter(d => d.category === currentCategory);

    dishListEl.innerHTML = '';

    filteredDishes.forEach(dish => {
        if (!dish.is_available) return;

        const cartItem = currentCart.items.find(item => item.dish_id === dish.id);
        const quantity = cartItem ? cartItem.quantity : 0;

        const dishCard = document.createElement('div');
        dishCard.className = 'dish-card';
        dishCard.innerHTML = `
            <div class="dish-image">${getDishEmoji(dish.category)}</div>
            <div class="dish-info">
                <div class="dish-name">${dish.name}</div>
                <div class="dish-desc">${dish.description || ''}</div>
                <div class="dish-price">${formatCurrency(dish.price)}</div>
            </div>
            <div class="dish-actions">
                ${quantity > 0 ? `
                    <button class="btn-minus" data-id="${dish.id}">-</button>
                    <span class="quantity">${quantity}</span>
                ` : ''}
                <button class="btn-plus" data-id="${dish.id}">+</button>
            </div>
        `;

        dishListEl.appendChild(dishCard);
    });

    bindDishEvents();
}

function bindDishEvents() {
    document.querySelectorAll('.btn-plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const dishId = parseInt(this.dataset.id);
            addToCart(dishId);
        });
    });

    document.querySelectorAll('.btn-minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const dishId = parseInt(this.dataset.id);
            removeFromCart(dishId);
        });
    });
}

function addToCart(dishId) {
    const dish = dishList.find(d => d.id === dishId);
    if (!dish) return;

    const existingItem = currentCart.items.find(item => item.dish_id === dishId);
    if (existingItem) {
        existingItem.quantity++;
    } else {
        currentCart.items.push({
            dish_id: dish.id,
            name: dish.name,
            price: dish.price,
            quantity: 1,
            image: dish.image
        });
    }

    saveCart();
    renderDishes();
    updateCartDisplay();
}

function removeFromCart(dishId) {
    const existingItem = currentCart.items.find(item => item.dish_id === dishId);
    if (!existingItem) return;

    existingItem.quantity--;
    if (existingItem.quantity <= 0) {
        currentCart.items = currentCart.items.filter(item => item.dish_id !== dishId);
    }

    saveCart();
    renderDishes();
    updateCartDisplay();
}

function saveCart() {
    localStorage.setItem('currentCart', JSON.stringify(currentCart));
}

function updateCartDisplay() {
    const cartCountEl = document.getElementById('cartCount');
    const cartTotalEl = document.getElementById('cartTotal');

    const totalItems = currentCart.items.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = currentCart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    if (cartCountEl) {
        cartCountEl.textContent = totalItems;
        cartCountEl.style.display = totalItems > 0 ? 'inline-block' : 'none';
    }

    if (cartTotalEl) {
        cartTotalEl.textContent = formatCurrency(totalPrice);
    }

    window.currentCart = currentCart;
}
