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

let featureChart = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAdminAuth()) {
        return;
    }

    const sidebarItems = document.querySelectorAll('.sidebar-item');
    const logoutBtn = document.getElementById('logoutBtn');
    const generateBtn = document.getElementById('generateBtn');

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

    if (generateBtn) {
        generateBtn.addEventListener('click', generatePrediction);
    }

    loadLatestPrediction();
    loadPredictionLogs();

    window.addEventListener('resize', function() {
        if (featureChart) featureChart.resize();
    });
});

async function loadLatestPrediction() {
    try {
        const data = await adminApiRequest('/prediction/latest', 'GET');
        renderPredictionResult(data);
        renderFeatureChart(data.feature_importance);
    } catch (error) {
        showToast(error.message || '加载预测数据失败');
    }
}

function renderPredictionResult(data) {
    const predictDateEl = document.getElementById('predictDate');
    const totalOrdersEl = document.getElementById('totalOrders');
    const totalRevenueEl = document.getElementById('totalRevenue');
    const breakfastOrdersEl = document.getElementById('breakfastOrders');
    const lunchOrdersEl = document.getElementById('lunchOrders');
    const dinnerOrdersEl = document.getElementById('dinnerOrders');
    const predictionTableEl = document.getElementById('predictionTable');

    if (predictDateEl) {
        predictDateEl.textContent = data.prediction_date || '';
    }
    if (totalOrdersEl) {
        totalOrdersEl.textContent = Math.round(data.total_orders || 0);
    }
    if (totalRevenueEl) {
        totalRevenueEl.textContent = formatCurrency(data.total_revenue || 0);
    }
    if (breakfastOrdersEl) {
        breakfastOrdersEl.textContent = Math.round(data.breakfast_orders || 0);
    }
    if (lunchOrdersEl) {
        lunchOrdersEl.textContent = Math.round(data.lunch_orders || 0);
    }
    if (dinnerOrdersEl) {
        dinnerOrdersEl.textContent = Math.round(data.dinner_orders || 0);
    }

    if (predictionTableEl && data.dish_predictions) {
        const tbody = predictionTableEl.querySelector('tbody');
        tbody.innerHTML = '';

        data.dish_predictions.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.dish_name}</td>
                <td>${getMealPeriodName(item.category)}</td>
                <td>${Math.round(item.predicted_quantity)}</td>
                <td>${formatCurrency(item.predicted_revenue)}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function renderFeatureChart(featureData) {
    const chartDom = document.getElementById('featureChart');
    if (!chartDom || typeof echarts === 'undefined' || !featureData) return;

    featureChart = echarts.init(chartDom);

    const features = featureData.map(item => item.feature);
    const importance = featureData.map(item => item.importance);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                return `${params[0].name}<br/>重要性: ${params[0].value.toFixed(4)}`;
            }
        },
        grid: {
            left: '20%',
            right: '10%',
            top: '10%',
            bottom: '10%'
        },
        xAxis: {
            type: 'value',
            name: '重要性',
            axisLabel: {
                formatter: '{value}'
            }
        },
        yAxis: {
            type: 'category',
            data: features,
            axisLabel: {
                interval: 0
            }
        },
        series: [{
            name: '特征重要性',
            type: 'bar',
            data: importance,
            itemStyle: {
                color: function(params) {
                    const colors = ['#1976d2', '#388e3c', '#f57c00', '#c62828', '#5e35b1', '#00838f', '#ef6c00', '#2e7d32'];
                    return colors[params.dataIndex % colors.length];
                }
            },
            label: {
                show: true,
                position: 'right',
                formatter: '{c}'
            }
        }]
    };

    featureChart.setOption(option);
}

async function loadPredictionLogs() {
    try {
        const data = await adminApiRequest('/prediction/logs', 'GET');
        renderPredictionLogs(data);
    } catch (error) {
        showToast(error.message || '加载预测日志失败');
    }
}

function renderPredictionLogs(logs) {
    const logsTableEl = document.getElementById('logsTable');
    if (!logsTableEl) return;

    const tbody = logsTableEl.querySelector('tbody');
    tbody.innerHTML = '';

    logs.forEach(log => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${log.prediction_date}</td>
            <td>${Math.round(log.predicted_orders)}</td>
            <td>${log.actual_orders !== null ? Math.round(log.actual_orders) : '-'}</td>
            <td>${log.actual_orders !== null ? Math.abs(Math.round(log.actual_orders - log.predicted_orders)) : '-'}</td>
            <td>${formatDate(log.created_at)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function generatePrediction() {
    const btn = document.getElementById('generateBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '生成中...';
    }

    try {
        await adminApiRequest('/prediction/generate', 'POST');
        showToast('预测生成成功');
        loadLatestPrediction();
        loadPredictionLogs();
    } catch (error) {
        showToast(error.message || '生成预测失败');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '重新生成预测';
        }
    }
}
