let familyList = [];
let pendingRequests = [];

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) {
        return;
    }

    const backBtn = document.getElementById('backBtn');
    const addFamilyBtn = document.getElementById('addFamilyBtn');
    const addModal = document.getElementById('addModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const submitFamilyBtn = document.getElementById('submitFamilyBtn');

    loadFamilyList();
    loadPendingRequests();

    if (backBtn) {
        backBtn.addEventListener('click', function() {
            navigateTo('/');
        });
    }

    if (addFamilyBtn) {
        addFamilyBtn.addEventListener('click', function() {
            addModal.style.display = 'flex';
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            addModal.style.display = 'none';
        });
    }

    if (submitFamilyBtn) {
        submitFamilyBtn.addEventListener('click', submitFamilyRequest);
    }

    addModal.addEventListener('click', function(e) {
        if (e.target === addModal) {
            addModal.style.display = 'none';
        }
    });
});

async function loadFamilyList() {
    try {
        familyList = await apiRequest('/family/list', 'GET');
        renderFamilyList();
    } catch (error) {
        showToast(error.message || '加载亲属列表失败');
    }
}

async function loadPendingRequests() {
    try {
        pendingRequests = await apiRequest('/family/pending', 'GET');
        renderPendingRequests();
    } catch (error) {
        showToast(error.message || '加载待确认请求失败');
    }
}

function renderFamilyList() {
    const familyListEl = document.getElementById('familyList');
    if (!familyListEl) return;

    if (familyList.length === 0) {
        familyListEl.innerHTML = '<div class="empty-state">暂无绑定亲属</div>';
        return;
    }

    familyListEl.innerHTML = '';

    familyList.forEach(family => {
        const relationNames = {
            'spouse': '配偶',
            'child': '子女',
            'parent': '父母',
            'sibling': '兄弟姐妹',
            'other': '其他'
        };

        const card = document.createElement('div');
        card.className = 'family-card';
        card.innerHTML = `
            <div class="family-avatar">${family.name ? family.name.charAt(0) : '?'}</div>
            <div class="family-info">
                <div class="family-name">${family.name || '未命名'}</div>
                <div class="family-phone">${family.phone}</div>
                <div class="family-relation">${relationNames[family.relation] || family.relation}</div>
            </div>
            <div class="family-actions">
                <button class="btn-order" onclick="startFamilyOrder(${family.id}, '${family.name}')">代订</button>
                <button class="btn-unbind" onclick="unbindFamily(${family.id})">解绑</button>
            </div>
        `;
        familyListEl.appendChild(card);
    });
}

function renderPendingRequests() {
    const pendingListEl = document.getElementById('pendingList');
    if (!pendingListEl) return;

    const pendingSection = document.getElementById('pendingSection');
    if (!pendingSection) return;

    if (pendingRequests.length === 0) {
        pendingSection.style.display = 'none';
        return;
    }

    pendingSection.style.display = 'block';
    pendingListEl.innerHTML = '';

    pendingRequests.forEach(request => {
        const relationNames = {
            'spouse': '配偶',
            'child': '子女',
            'parent': '父母',
            'sibling': '兄弟姐妹',
            'other': '其他'
        };

        const card = document.createElement('div');
        card.className = 'pending-card';
        card.innerHTML = `
            <div class="pending-info">
                <div class="pending-name">${request.requester_name || '新用户'}</div>
                <div class="pending-phone">${request.requester_phone}</div>
                <div class="pending-relation">申请成为您的${relationNames[request.relation] || request.relation}</div>
            </div>
            <div class="pending-actions">
                <button class="btn-accept" onclick="acceptRequest(${request.id})">接受</button>
                <button class="btn-reject" onclick="rejectRequest(${request.id})">拒绝</button>
            </div>
        `;
        pendingListEl.appendChild(card);
    });
}

async function submitFamilyRequest() {
    const phoneInput = document.getElementById('familyPhone');
    const relationSelect = document.getElementById('familyRelation');

    const phone = phoneInput.value.trim();
    const relation = relationSelect.value;

    if (!/^1\d{10}$/.test(phone)) {
        showToast('请输入正确的11位手机号码');
        return;
    }

    if (!relation) {
        showToast('请选择亲属关系');
        return;
    }

    try {
        await apiRequest('/family/request', 'POST', { phone, relation });
        showToast('申请已发送，等待对方确认');
        document.getElementById('addModal').style.display = 'none';
        phoneInput.value = '';
        relationSelect.value = '';
    } catch (error) {
        showToast(error.message || '发送申请失败');
    }
}

async function acceptRequest(requestId) {
    try {
        await apiRequest(`/family/pending/${requestId}/accept`, 'PUT');
        showToast('已接受绑定请求');
        loadFamilyList();
        loadPendingRequests();
    } catch (error) {
        showToast(error.message || '操作失败');
    }
}

async function rejectRequest(requestId) {
    try {
        await apiRequest(`/family/pending/${requestId}/reject`, 'PUT');
        showToast('已拒绝绑定请求');
        loadPendingRequests();
    } catch (error) {
        showToast(error.message || '操作失败');
    }
}

async function unbindFamily(familyId) {
    if (!confirm('确定要解除与该亲属的绑定吗？')) {
        return;
    }

    try {
        await apiRequest(`/family/${familyId}/unbind`, 'DELETE');
        showToast('已解除绑定');
        loadFamilyList();
    } catch (error) {
        showToast(error.message || '解绑失败');
    }
}

function startFamilyOrder(familyId, familyName) {
    localStorage.setItem('for_user_id', familyId);
    localStorage.setItem('for_user_name', familyName);
    navigateTo('/family/order');
}
