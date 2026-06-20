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

let heatmapChart = null;
let trendChart = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!checkAdminAuth()) {
        return;
    }

    const sidebarItems = document.querySelectorAll('.sidebar-item');
    const logoutBtn = document.getElementById('logoutBtn');

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

    loadKanbanData();
    loadHeatmapData();
    loadWeeklyTrendData();

    window.addEventListener('resize', function() {
        if (heatmapChart) heatmapChart.resize();
        if (trendChart) trendChart.resize();
    });
});

async function loadKanbanData() {
    try {
        const data = await adminApiRequest('/admin/dashboard/stats', 'GET');
        renderKanbanCards(data);
    } catch (error) {
        showToast(error.message || '加载统计数据失败');
    }
}

function renderKanbanCards(data) {
    const todayOrdersEl = document.getElementById('todayOrders');
    const todayRevenueEl = document.getElementById('todayRevenue');
    const todayUsersEl = document.getElementById('todayUsers');
    const pendingOrdersEl = document.getElementById('pendingOrders');

    if (todayOrdersEl) {
        todayOrdersEl.textContent = data.today_orders || 0;
    }
    if (todayRevenueEl) {
        todayRevenueEl.textContent = formatCurrency(data.today_revenue || 0);
    }
    if (todayUsersEl) {
        todayUsersEl.textContent = data.today_users || 0;
    }
    if (pendingOrdersEl) {
        pendingOrdersEl.textContent = data.pending_orders || 0;
    }
}

async function loadHeatmapData() {
    try {
        const data = await adminApiRequest('/admin/dashboard/heatmap', 'GET');
        renderHeatmapChart(data);
    } catch (error) {
        showToast(error.message || '加载热力图数据失败');
    }
}

function renderHeatmapChart(data) {
    const chartDom = document.getElementById('heatmapChart');
    if (!chartDom || typeof echarts === 'undefined') return;

    heatmapChart = echarts.init(chartDom);

    const hours = data.hours || ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', 
                                  '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'];
    const days = data.days || data.date_range || ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    const heatData = data.data || data.echarts_data || [];

    const option = {
        tooltip: {
            position: 'top',
            formatter: function(params) {
                return `${days[params.value[1]]} ${hours[params.value[0]]}<br/>订单数: ${params.value[2]}`;
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '10%',
            bottom: '15%'
        },
        xAxis: {
            type: 'category',
            data: hours,
            splitArea: { show: true }
        },
        yAxis: {
            type: 'category',
            data: days,
            splitArea: { show: true }
        },
        visualMap: {
            min: 0,
            max: Math.max(...heatData.map(d => d[2]), 10),
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '0%',
            inRange: {
                color: ['#e0f7fa', '#80deea', '#26c6da', '#00acc1', '#00838f']
            }
        },
        series: [{
            name: '订单热力图',
            type: 'heatmap',
            data: heatData,
            label: {
                show: true,
                fontSize: 12
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };

    heatmapChart.setOption(option);
}

async function loadWeeklyTrendData() {
    try {
        const data = await adminApiRequest('/admin/dashboard/trend', 'GET');
        renderTrendChart(data);
    } catch (error) {
        showToast(error.message || '加载周趋势数据失败');
    }
}

function renderTrendChart(data) {
    const chartDom = document.getElementById('trendChart');
    if (!chartDom || typeof echarts === 'undefined') return;

    trendChart = echarts.init(chartDom);

    const dates = data.dates || (data.trend && data.trend.map(d => d.date)) || [];
    const orders = data.orders || (data.trend && data.trend.map(d => d.orders)) || [];
    const revenue = data.revenue || (data.trend && data.trend.map(d => d.revenue)) || [];

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['订单数', '营收'],
            top: '0%'
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '15%',
            bottom: '10%'
        },
        xAxis: {
            type: 'category',
            data: dates,
            boundaryGap: false
        },
        yAxis: [
            {
                type: 'value',
                name: '订单数',
                position: 'left',
                axisLabel: {
                    formatter: '{value} 单'
                }
            },
            {
                type: 'value',
                name: '营收',
                position: 'right',
                axisLabel: {
                    formatter: '¥{value}'
                }
            }
        ],
        series: [
            {
                name: '订单数',
                type: 'line',
                yAxisIndex: 0,
                data: orders,
                smooth: true,
                itemStyle: {
                    color: '#1976d2'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(25, 118, 210, 0.3)' },
                            { offset: 1, color: 'rgba(25, 118, 210, 0.05)' }
                        ]
                    }
                }
            },
            {
                name: '营收',
                type: 'line',
                yAxisIndex: 1,
                data: revenue,
                smooth: true,
                itemStyle: {
                    color: '#388e3c'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(56, 142, 60, 0.3)' },
                            { offset: 1, color: 'rgba(56, 142, 60, 0.05)' }
                        ]
                    }
                }
            }
        ]
    };

    trendChart.setOption(option);
}
