@echo off
echo ===== 专注学习计时器打包工具 =====
echo.

REM 检查Python环境
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH环境变量中。
    pause
    exit /b 1
)

REM 检查并安装必要的依赖
echo 正在检查并安装必要的依赖...
python -m pip install -r requirements.txt
python -m pip install PyInstaller>=4.7 Pillow requests

REM 运行打包前测试
echo 正在运行打包前测试...
python test_before_build.py
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 打包前测试未通过，请修复问题后再尝试打包。
    pause
    exit /b 1
)

REM 创建必要的资源文件
echo 正在创建必要的资源文件...
python create_icon.py
python create_sound.py

REM 运行打包脚本
echo 正在运行打包脚本...
python build.py

echo.
echo 打包过程已完成！
pause