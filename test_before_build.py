#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包前测试脚本
用于检查应用程序的基本功能是否正常
"""

import os
import sys
import importlib
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_module(module_name):
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_name)
        logger.info(f"✓ 模块 {module_name} 导入成功")
        return True
    except ImportError as e:
        logger.error(f"✗ 模块 {module_name} 导入失败: {e}")
        return False

def check_file(file_path):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        logger.info(f"✓ 文件 {file_path} 存在")
        return True
    else:
        logger.error(f"✗ 文件 {file_path} 不存在")
        return False

def check_directory(dir_path):
    """检查目录是否存在"""
    if os.path.isdir(dir_path):
        logger.info(f"✓ 目录 {dir_path} 存在")
        return True
    else:
        logger.error(f"✗ 目录 {dir_path} 不存在")
        return False

def main():
    """主函数"""
    logger.info("开始打包前测试...")
    
    # 检查必要的模块
    required_modules = [
        'PyQt5',
        'PyQt5.QtChart',
        'pygame',
        'matplotlib',
        'numpy',
    ]
    
    modules_ok = True
    for module in required_modules:
        if not check_module(module):
            modules_ok = False
    
    # 检查必要的文件
    required_files = [
        'main.py',
        'requirements.txt',
        'config/settings.py',
        'config/database.py',
        'ui/main_window.py',
        'ui/timer_widget.py',
        'ui/settings_widget.py',
        'ui/stats_widget.py',
        'core/timer.py',
        'core/audio_manager.py',
    ]
    
    files_ok = True
    for file in required_files:
        if not check_file(file):
            files_ok = False
    
    # 检查必要的目录
    required_dirs = [
        'resources',
        'resources/icons',
        'resources/sounds',
        'data',
    ]
    
    dirs_ok = True
    for directory in required_dirs:
        if not check_directory(directory):
            dirs_ok = False
    
    # 创建必要的资源文件
    try:
        logger.info("创建必要的资源文件...")
        # 运行创建图标脚本
        if os.path.exists('create_icon.py'):
            logger.info("运行创建图标脚本...")
            os.system('python create_icon.py')
        
        # 运行创建声音脚本
        if os.path.exists('create_sound.py'):
            logger.info("运行创建声音脚本...")
            os.system('python create_sound.py')
    except Exception as e:
        logger.error(f"创建资源文件失败: {e}")
    
    # 测试应用程序是否可以启动
    try:
        logger.info("测试应用程序启动...")
        # 导入主模块
        from main import FocusTimerApp
        logger.info("✓ 主模块导入成功")
        
        # 创建应用程序实例（不运行）
        app = FocusTimerApp()
        logger.info("✓ 应用程序实例创建成功")
        
        app_ok = True
    except Exception as e:
        logger.error(f"应用程序启动测试失败: {e}")
        app_ok = False
    
    # 总结测试结果
    logger.info("\n测试结果汇总:")
    logger.info(f"模块检查: {'通过' if modules_ok else '失败'}")
    logger.info(f"文件检查: {'通过' if files_ok else '失败'}")
    logger.info(f"目录检查: {'通过' if dirs_ok else '失败'}")
    logger.info(f"应用启动: {'通过' if app_ok else '失败'}")
    
    if modules_ok and files_ok and dirs_ok and app_ok:
        logger.info("\n✓ 所有测试通过，可以进行打包")
        return 0
    else:
        logger.error("\n✗ 测试未通过，请修复上述问题后再进行打包")
        return 1

if __name__ == "__main__":
    sys.exit(main())