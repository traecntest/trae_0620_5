#!/bin/bash
echo "========================================"
echo "  数据库初始化脚本 - Linux"
echo "========================================"
echo ""

echo "[1/2] 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未检测到Python，请先安装Python 3.9+"
    exit 1
fi

echo ""
echo "[2/2] 执行数据库初始化..."
echo "注意: 这将删除所有现有数据并重新创建测试数据"
echo ""
read -p "确认继续? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

cd "$(dirname "$0")"
python3 scripts/init_db.py

echo ""
echo "========================================"
echo "  初始化完成！"
echo "========================================"
