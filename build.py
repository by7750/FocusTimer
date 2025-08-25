#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专注学习计时器 - 打包脚本
用于将应用程序打包成Windows可执行程序和安装包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 确保PyInstaller已安装
try:
    import PyInstaller
except ImportError:
    print("PyInstaller未安装，正在安装...")
    subprocess.call([sys.executable, "-m", "pip", "install", "PyInstaller>=4.7"])

# 确保必要的目录存在
def ensure_directories():
    directories = [
        'build',
        'dist',
        'resources/icons',
        'resources/sounds',
        'resources/styles',
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")

# 创建默认图标如果不存在
def create_default_icon():
    icon_path = "resources/icons/icon.png"
    if not os.path.exists(icon_path):
        from PIL import Image, ImageDraw
        
        try:
            # 创建一个简单的默认图标
            img = Image.new('RGBA', (256, 256), color=(39, 174, 96, 255))
            draw = ImageDraw.Draw(img)
            # 绘制一个简单的时钟图案
            draw.ellipse((20, 20, 236, 236), outline=(255, 255, 255, 255), width=10)
            # 绘制时钟指针
            draw.line((128, 128, 128, 60), fill=(255, 255, 255, 255), width=8)
            draw.line((128, 128, 180, 128), fill=(255, 255, 255, 255), width=8)
            img.save(icon_path)
            print(f"创建默认图标: {icon_path}")
        except ImportError:
            print("警告: PIL库未安装，无法创建默认图标")
            # 创建一个空白文件作为占位符
            with open(icon_path, 'wb') as f:
                f.write(b'')

# 创建默认声音文件如果不存在
def create_default_sound():
    sound_path = "resources/sounds/default_alarm.wav"
    if not os.path.exists(sound_path):
        # 尝试从网络下载一个免费的声音文件
        try:
            import requests
            url = "https://www.soundjay.com/buttons/beep-1.wav"  # 一个免费的提示音
            response = requests.get(url)
            with open(sound_path, 'wb') as f:
                f.write(response.content)
            print(f"下载默认提示音: {sound_path}")
        except Exception as e:
            print(f"警告: 无法下载默认提示音: {e}")
            # 创建一个空白文件作为占位符
            with open(sound_path, 'wb') as f:
                f.write(b'')

# 使用PyInstaller打包应用
def build_executable():
    print("开始打包应用程序...")
    
    # PyInstaller命令行参数
    pyinstaller_args = [
        "--name=FocusTimer",  # 使用英文名称避免空格问题
        "--windowed",  # 不显示控制台窗口
        "--noconfirm",  # 覆盖输出目录
        "--add-data=resources;resources",  # 添加资源文件
        "--add-data=data;data",  # 添加数据文件
        "--icon=resources/icons/icon.png",  # 应用图标
        "--hidden-import=PyQt5.QtChart",  # 隐式导入
        "--hidden-import=PyQt5.QtWidgets",  # 确保包含所有Qt组件
        "--hidden-import=PyQt5.QtCore",  # Qt核心模块
        "--hidden-import=PyQt5.QtGui",  # Qt GUI模块
        "--hidden-import=ctypes",  # 用于DPI感知设置
        "--hidden-import=platform",  # 用于操作系统检测
        "--hidden-import=matplotlib",  # 隐式导入
        "--hidden-import=numpy",  # 隐式导入
        "--hidden-import=pygame",  # 隐式导入
        "--hidden-import=colorlog",  # 隐式导入
        "main.py"  # 主程序入口
    ]
    
    # 执行PyInstaller命令
    cmd = [sys.executable, "-m", "PyInstaller"] + pyinstaller_args
    subprocess.call(cmd)
    
    print("应用程序打包完成!")

# 创建安装包
def create_installer():
    print("开始创建安装包...")
    
    try:
        # 尝试使用NSIS创建安装包
        # 首先检查NSIS是否安装
        nsis_path = None
        possible_paths = [
            r"C:\Program Files (x86)\NSIS\makensis.exe",
            r"C:\Program Files\NSIS\makensis.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                nsis_path = path
                break
        
        if nsis_path:
            # 创建NSIS脚本
            with open("installer.nsi", "w", encoding="utf-8") as f:
                f.write("""
                !include "MUI2.nsh"
                
                ; 应用程序信息
                Name "FocusTimer"
                OutFile "FocusTimer-Setup.exe"
                
                ; 默认安装目录
                InstallDir "$PROGRAMFILES\\FocusTimer"
                
                ; 请求应用程序权限
                RequestExecutionLevel admin
                
                ; 界面设置
                !define MUI_ABORTWARNING
                !define MUI_ICON "resources\\icons\\app_icon.ico"
                
                ; 页面
                !insertmacro MUI_PAGE_WELCOME
                !insertmacro MUI_PAGE_DIRECTORY
                !insertmacro MUI_PAGE_INSTFILES
                !insertmacro MUI_PAGE_FINISH
                
                ; 语言
                !insertmacro MUI_LANGUAGE "SimpChinese"
                
                ; 安装部分
                Section "安装程序文件" SecMain
                    SetOutPath "$INSTDIR"
                    
                    ; 复制所有文件
                    File /r "dist\\FocusTimer\\*.*"
                    
                    ; 明确复制资源文件（确保图标等资源被包含）
                    SetOutPath "$INSTDIR\\resources\\icons"
                    File "resources\\icons\\app_icon.ico"
                    File "resources\\icons\\icon.png"
                    File "resources\\icons\\music_pause.png"
                    File "resources\\icons\\music_play.png"
                    File "resources\\icons\\music_stop.png"
                    File "resources\\icons\\timer_change.png"
                    File "resources\\icons\\timer_pause.png"
                    File "resources\\icons\\timer_reset.png"
                    File "resources\\icons\\timer_start.png"
                    File "resources\\icons\\timer_stop.png"
                    
                    SetOutPath "$INSTDIR\\resources\\sounds"
                    ; 如果有声音文件也在这里添加
                    
                    SetOutPath "$INSTDIR\\resources\\styles"
                    ; 如果有样式文件也在这里添加
                    
                    ; 创建开始菜单快捷方式
                    CreateDirectory "$SMPROGRAMS\\FocusTimer"
                    CreateShortcut "$SMPROGRAMS\\FocusTimer\\FocusTimer.lnk" "$INSTDIR\\FocusTimer.exe"
                    CreateShortcut "$SMPROGRAMS\\FocusTimer\\卸载.lnk" "$INSTDIR\\卸载.exe"
                    
                    ; 创建桌面快捷方式
                    CreateShortcut "$DESKTOP\\FocusTimer.lnk" "$INSTDIR\\FocusTimer.exe"
                    
                    ; 创建卸载程序
                    WriteUninstaller "$INSTDIR\\卸载.exe"
                    
                    ; 添加卸载信息到控制面板
                    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FocusTimer" "DisplayName" "FocusTimer"
                    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FocusTimer" "UninstallString" "$INSTDIR\\卸载.exe"
                    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FocusTimer" "DisplayIcon" "$INSTDIR\\FocusTimer.exe"
                    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FocusTimer" "Publisher" "FocusTimer"
                SectionEnd
                
                ; 卸载部分
                Section "Uninstall"
                    ; 删除程序文件
                    RMDir /r "$INSTDIR"
                    
                    ; 删除开始菜单快捷方式
                    RMDir /r "$SMPROGRAMS\\FocusTimer"
                    
                    ; 删除桌面快捷方式
                    Delete "$DESKTOP\\FocusTimer.lnk"
                    
                    ; 删除注册表项
                    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FocusTimer"
                SectionEnd
                """)
            
            # 执行NSIS编译，指定UTF-8编码
            subprocess.call([nsis_path, "/INPUTCHARSET", "UTF8", "installer.nsi"])
            print("安装包创建成功: FocusTimer-Setup.exe")
        else:
            print("警告: 未找到NSIS，无法创建安装包。请安装NSIS后重试。")
            print("NSIS下载地址: https://nsis.sourceforge.io/Download")
    except Exception as e:
        print(f"创建安装包失败: {e}")
        print("请手动使用NSIS或Inno Setup创建安装包。")

# 主函数
def main():
    print("===== 专注学习计时器打包工具 =====")
    
    # 确保目录存在
    ensure_directories()
    
    # 创建默认资源
    create_default_icon()
    create_default_sound()
    
    # 打包应用
    build_executable()
    
    # 创建安装包
    create_installer()
    
    print("\n打包过程完成!")
    print("可执行文件位置: dist/FocusTimer/FocusTimer.exe")
    print("如果安装包创建成功，位置为: FocusTimer-Setup.exe")

if __name__ == "__main__":
    main()