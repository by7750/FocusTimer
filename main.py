#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专注学习计时器 - 主程序入口
作者: Assistant
版本: 1.0.0
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

# 项目模块导入
from ui.main_window import MainWindow
from config.settings import Settings
from config.database import Database
from core.singleton import SingletonApp


class FocusTimerApp:
    """专注计时器应用程序主类"""

    def __init__(self):
        """初始化应用程序"""
        self.app = None
        self.main_window = None
        self.settings = None
        self.database = None
        self.singleton = SingletonApp()
        self.setup_logging()
        self.setup_directories()

    def setup_logging(self):
        """设置日志系统"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('focus_timer.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """创建必要的目录结构"""
        directories = [
            'data',
            'data/backups',
            'resources/sounds',
            'resources/icons',
            'logs'
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                self.logger.info(f"创建目录: {directory}")

    def initialize_components(self):
        """初始化核心组件"""
        try:
            # 初始化设置管理器
            self.settings = Settings()
            self.logger.info("设置管理器初始化完成")

            # 初始化数据库
            self.database = Database()
            self.logger.info("数据库初始化完成")

            return True
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            return False

    def create_application(self):
        """创建QT应用程序"""
        # 在创建QApplication之前设置高DPI缩放属性
        self.setup_high_dpi_scaling()
        
        self.app = QApplication(sys.argv)

        # 设置应用程序基本信息
        self.app.setApplicationName("专注学习计时器")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("FocusTimer")

        # 设置应用程序图标（如果存在）
        icon_path = "resources/icons/app_icon.ico"
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.app.setFont(font)

        self.logger.info("Qt应用程序创建完成")
        
    def setup_high_dpi_scaling(self):
        """设置高DPI缩放支持"""
        # 检测操作系统版本
        import platform
        if platform.system() == "Windows":
            # 获取Windows版本
            win_version = platform.version()
            self.logger.info(f"Windows版本: {win_version}")
            
            # 设置Qt的高DPI缩放属性
            # 这些设置需要在创建QApplication前设置
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # Windows 10特定的兼容性设置
            if "10." in win_version:
                self.logger.info("应用Windows 10兼容性设置")
                # 设置Windows 10下的DPI感知模式
                if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
                    QApplication.setHighDpiScaleFactorRoundingPolicy(
                        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
                    )
                # 设置进程DPI感知（需要在Windows上使用）
                try:
                    from ctypes import windll
                    windll.user32.SetProcessDPIAware()
                except Exception as e:
                    self.logger.warning(f"设置DPI感知失败: {e}")

    def create_main_window(self):
        """创建主窗口"""
        try:
            self.main_window = MainWindow(
                settings=self.settings,
                database=self.database
            )
            self.main_window.show()
            self.logger.info("主窗口创建完成")
            return True
        except Exception as e:
            self.logger.error(f"主窗口创建失败: {e}")
            return False

    def run(self):
        """运行应用程序"""
        self.logger.info("启动专注学习计时器应用程序...")
        
        # 检查是否已有实例在运行
        if self.singleton.is_running():
            self.logger.info("检测到应用程序已经在运行，正在激活已有实例...")
            if self.singleton.activate_running_instance():
                self.logger.info("已激活运行中的实例，当前实例将退出")
                return 0
            else:
                self.logger.warning("无法激活运行中的实例，将继续启动新实例")

        # 创建Qt应用程序
        self.create_application()

        # 初始化核心组件
        if not self.initialize_components():
            self.logger.error("核心组件初始化失败，程序退出")
            return 1

        # 创建主窗口
        if not self.create_main_window():
            self.logger.error("主窗口创建失败，程序退出")
            return 1
            
        # 注册窗口以接收单例消息
        self.singleton.register_window_class(self.main_window)

        # 启动应用程序事件循环
        try:
            exit_code = self.app.exec_()
            self.logger.info(f"应用程序正常退出，退出码: {exit_code}")
            return exit_code
        except Exception as e:
            self.logger.error(f"应用程序运行时发生错误: {e}")
            return 1
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理应用程序资源...")

        # 保存设置
        if self.settings:
            self.settings.save()
            self.logger.info("设置已保存")

        # 关闭数据库连接
        if self.database:
            self.database.close()
            self.logger.info("数据库连接已关闭")


def main():
    """主函数"""
    # 设置高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建并运行应用程序
    app = FocusTimerApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())