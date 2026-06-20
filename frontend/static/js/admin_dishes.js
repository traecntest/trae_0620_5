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

let dishList = [];
let editingDishId = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAdminAuth()) {
        return;
    }

    const sidebarItems = document.querySelectorAll('.sidebar-item');
    const logoutBtn = document.getElementById('logoutBtn');
    const addDishBtn = document.getElementById('addDishBtn');
    const dishModal = document.getElementById('dishModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const saveDishBtn = document.getElementById('saveDishBtn');

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

    if (addDishBtn) {
        addDishBtn.addEventListener('click', function() {
            editingDishId = null;
            document.getElementById('modalTitle').textContent = '添加菜品';
            document.getElementById('dishName').value = '';
            document.getElementById('dishPrice').value = '';
            document.getElementById('dishCategory').value = '';
            document.getElementById('dishDesc').value = '';
            dishModal.style.display = 'flex';
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            dishModal.style.display = 'none';
        });
    }

    if (saveDishBtn) {
        saveDishBtn.addEventListener('click', saveDish);
    }

    dishModal.addEventListener('click', function(e) {
        if (e.target === dishModal) {
            dishModal.style.display = 'none';
        }
    });

    loadDishes();
});

async function loadDishes() {
    try {
        dishList = await adminApiRequest('/dishes', 'GET');
        renderDishTable();
    } catch (error) {
        showToast(error.message || '加载菜品列表失败');
    }
}

function renderDishTable() {
    const tableBody = document.querySelector('#dishTable tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    dishList.forEach(dish => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${dish.id}</td>
            <td>${dish.name}</td>
            <td>${getMealPeriodName(dish.category)}</td>
            <td>${formatCurrency(dish.price)}</td>
            <td>${dish.description || '-'}</td>
            <td>
                <label class="switch">
                    <input type="checkbox" ${dish.is_available ? 'checked' : ''} onchange="toggleDishStatus(${dish.id}, this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
            <td>
                <button class="btn-edit" onclick="editDish(${dish.id})">编辑</button>
                <button class="btn-delete" onclick="deleteDish(${dish.id})">删除</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

function editDish(dishId) {
    const dish = dishList.find(d => d.id === dishId);
    if (!dish) return;

    editingDishId = dishId;
    document.getElementById('modalTitle').textContent = '编辑菜品';
    document.getElementById('dishName').value = dish.name;
    document.getElementById('dishPrice').value = dish.price;
    document.getElementById('dishCategory').value = dish.category;
    document.getElementById('dishDesc').value = dish.description || '';
    document.getElementById('dishModal').style.display = 'flex';
}

async function saveDish() {
    const name = document.getElementById('dishName').value.trim();
    const price = parseFloat(document.getElementById('dishPrice').value);
    const category = document.getElementById('dishCategory').value;
    const description = document.getElementById('dishDesc').value.trim();

    if (!name) {
        showToast('请输入菜品名称');
        return;
    }

    if (isNaN(price) || price <= 0) {
        showToast('请输入有效的价格');
        return;
    }

    if (!category) {
        showToast('请选择菜品分类');
        return;
    }

    const dishData = {
        name,
        price,
        category,
        description
    };

    try {
        if (editingDishId) {
            await adminApiRequest(`/dishes/${editingDishId}`, 'PUT', dishData);
            showToast('菜品更新成功');
        } else {
            await adminApiRequest('/dishes', 'POST', dishData);
            showToast('菜品添加成功');
        }

        document.getElementById('dishModal').style.display = 'none';
        loadDishes();
    } catch (error) {
        showToast(error.message || '保存菜品失败');
    }
}

async function toggleDishStatus(dishId, isAvailable) {
    try {
        await adminApiRequest(`/dishes/${dishId}/toggle`, 'PUT', { is_available: isAvailable });
        showToast(isAvailable ? '菜品已上架' : '菜品已下架');
        loadDishes();
    } catch (error) {
        showToast(error.message || '操作失败');
        loadDishes();
    }
}

async function deleteDish(dishId) {
    if (!confirm('确定要删除这个菜品吗？')) {
        return;
    }

    try {
        await adminApiRequest(`/dishes/${dishId}`, 'DELETE');
        showToast('菜品已删除');
        loadDishes();
    } catch (error) {
        showToast(error.message || '删除失败');
    }
}
