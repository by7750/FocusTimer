# 专注学习计时器打包工具
Write-Host "===== 专注学习计时器打包工具 =====" -ForegroundColor Green
Write-Host ""

# 检查Python环境
try {
    python --version | Out-Null
} catch {
    Write-Host "错误: 未找到Python，请确保Python已安装并添加到PATH环境变量中。" -ForegroundColor Red
    Read-Host "按任意键继续..."
    exit 1
}

# 检查并安装必要的依赖
Write-Host "正在检查并安装必要的依赖..." -ForegroundColor Cyan
python -m pip install -r requirements.txt
python -m pip install PyInstaller -U
python -m pip install Pillow requests

# 运行打包前测试
Write-Host "正在运行打包前测试..." -ForegroundColor Cyan
python test_before_build.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 打包前测试未通过，请修复问题后再尝试打包。" -ForegroundColor Red
    Read-Host "按任意键继续..."
    exit 1
}

# 创建必要的资源文件
Write-Host "正在创建必要的资源文件..." -ForegroundColor Cyan
python create_icon.py
python create_sound.py

# 运行打包脚本
Write-Host "正在运行打包脚本..." -ForegroundColor Cyan
python build.py

Write-Host ""
Write-Host "打包过程已完成！" -ForegroundColor Green
Read-Host "按任意键继续..."