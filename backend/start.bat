@echo off
echo ========================================
echo   社区老年食堂智能点餐系统 - Windows启动
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖包...
cd /d "%~dp0"
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/3] 启动服务...
echo.
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 老人端: http://localhost:8000/
echo 管理后台: http://localhost:8000/admin
echo.
echo 测试账号:
echo   管理员: 13800000000 / admin123
echo   老人用户: 13800000001 ~ 13800000005 (验证码 123456)
echo   亲属用户: 13900000001 ~ 13900000002 (验证码 123456)
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
