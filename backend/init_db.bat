@echo off
echo ========================================
echo   数据库初始化脚本 - Windows
echo ========================================
echo.

echo [1/2] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo.
echo [2/2] 执行数据库初始化...
echo 注意: 这将删除所有现有数据并重新创建测试数据
echo.
set /p confirm=确认继续? (y/n): 
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)

cd /d "%~dp0"
python scripts\init_db.py

echo.
echo ========================================
echo   初始化完成！
echo ========================================
pause
