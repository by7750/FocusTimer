#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
负责应用程序的主界面和页面管理
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QPushButton, QLabel, QFrame,
                             QSystemTrayIcon, QMenu, QAction, QMessageBox,
                             QApplication)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QAbstractNativeEventFilter
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPalette, QColor

import sys
import os
import platform
import logging
import ctypes
import win32con
from datetime import datetime
from typing import Optional, Tuple, Any, Union

# 项目模块导入
from ui.timer_widget import TimerWidget
from ui.settings_widget import SettingsWidget
from ui.stats_widget import StatsWidget
from config.settings import Settings
from config.database import Database
from core.audio_manager import AudioManager

# 定义Windows消息常量
WM_SHOWAPP = win32con.WM_USER + 1

# 原生事件过滤器，用于处理Windows消息
class NativeEventFilter(QAbstractNativeEventFilter):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.logger = logging.getLogger(__name__)
        
    def nativeEventFilter(self, eventType, message):
        # 将消息转换为整数值
        try:
            msg = ctypes.c_uint(int(message)).value
            # 检查是否是我们的自定义消息
            if msg == WM_SHOWAPP:
                self.logger.info("收到WM_SHOWAPP消息，激活窗口")
                self.window.show_window()
                return True, 0
        except Exception as e:
            self.logger.error(f"处理原生事件时出错: {e}")
        
        return False, 0


class NavigationBar(QFrame):
    """导航栏组件"""

    # 页面切换信号
    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = "timer"
        self.buttons = {}
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        """设置界面"""
        self.setFixedHeight(60)
        self.setFrameStyle(QFrame.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # 应用标题
        title_label = QLabel("专注学习计时器")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 弹性空间
        layout.addStretch()

        # 导航按钮
        nav_pages = [
            ("timer", "计时器", "⏰"),
            ("stats", "统计", "📊"),
            ("todo", "待办事项", "📝"),
            ("settings", "设置", "⚙️")
        ]

        for page_id, page_name, icon in nav_pages:
            btn = QPushButton(f"{icon} {page_name}")
            btn.setObjectName(f"navBtn_{page_id}")
            btn.setFixedSize(100, 40)
            btn.clicked.connect(lambda checked, p=page_id: self.switch_page(p))

            self.buttons[page_id] = btn
            layout.addWidget(btn)

        # 设置默认选中状态
        self.update_button_states()

    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            NavigationBar {
                background-color: #ffffff;
                border-bottom: 2px solid #e0e0e0;
            }

            QLabel#titleLabel {
                color: #2c3e50;
                font-weight: bold;
            }

            QPushButton {
                background-color: #f5f5f5;
                color: #2c3e50;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #e0e0e0;
            }

            QPushButton:pressed {
                background-color: #d0d0d0;
            }

            QPushButton[selected="true"] {
                background-color: #3498db;
                color: white;
                border: 1px solid #3498db;
            }
        """)

    def switch_page(self, page_id: str):
        """切换页面"""
        if page_id != self.current_page:
            self.current_page = page_id
            self.update_button_states()
            self.page_changed.emit(page_id)

    def update_button_states(self):
        """更新按钮状态"""
        for page_id, btn in self.buttons.items():
            is_selected = page_id == self.current_page
            btn.setProperty("selected", is_selected)
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self, settings: Settings, database: Database):
        super().__init__()
        
        # 在创建QApplication后，窗口显示前设置高DPI缩放
        # 注意：必须在super().__init__()之后调用
        self.setup_high_dpi_scaling()

        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # 音频管理器
        self.audio_manager = AudioManager()

        # 页面组件
        self.timer_widget = None
        self.settings_widget = None
        self.stats_widget = None
        
        # 当前会话ID
        self.current_session_id = None
        
        # 当前计时器信息（用于延迟创建会话）
        self.current_timer_type = None
        self.current_planned_duration = None
        self.current_timer_start_time = None

        # 系统托盘
        self.tray_icon = None

        # 界面组件
        self.navigation_bar = None
        self.stacked_widget = None

        self.setup_window()
        self.setup_ui()
        self.setup_system_tray()
        self.setup_connections()
        self.restore_window_state()
        
        # 安装原生事件过滤器，用于处理单例消息
        self.native_event_filter = NativeEventFilter(self)
        QApplication.instance().installNativeEventFilter(self.native_event_filter)
        self.logger.info("已安装原生事件过滤器，用于处理单例消息")

    def setup_window(self):
        """设置窗口基本属性"""
        self.setWindowTitle("专注学习计时器")
        self.setMinimumSize(800, 600)

        # 设置窗口图标
        icon_path = "resources/icons/app_icon.ico"
        if QIcon(icon_path).pixmap(16, 16).isNull():
            # 如果图标不存在，创建一个简单的默认图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#27ae60"))
            self.setWindowIcon(QIcon(pixmap))
        else:
            self.setWindowIcon(QIcon(icon_path))
            
        # 设置窗口标志，确保在Windows 10上正确显示
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 检测Windows版本并应用特定设置
        if platform.system() == "Windows" and "10." in platform.version():
            # Windows 10特定设置
            self.logger.info("应用Windows 10窗口特定设置")
            # 设置窗口属性以确保正确的DPI缩放
            self.setAttribute(Qt.WA_NativeWindow, True)
            # 禁用自动缩放，使用我们自己的缩放逻辑
            self.setAttribute(Qt.WA_DontCreateNativeAncestors, False)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }

            QStackedWidget {
                background-color: #ecf0f1;
                border: none;
            }
        """)

    def setup_ui(self):
        """设置用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 导航栏
        self.navigation_bar = NavigationBar()
        main_layout.addWidget(self.navigation_bar)

        # 页面堆栈
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 创建页面
        self.create_pages()

    def create_pages(self):
        """创建各个页面"""
        # 计时器页面
        self.timer_widget = TimerWidget(self.settings, self.database)
        # 设置音频管理器
        self.timer_widget.set_audio_manager(self.audio_manager)
        self.stacked_widget.addWidget(self.timer_widget)

        # 统计页面
        self.stats_widget = StatsWidget(self.settings, self.database)
        self.stacked_widget.addWidget(self.stats_widget)

        # 待办事项页面
        from ui.todo_widget import TodoWidget
        self.todo_widget = TodoWidget(self.settings, self.database)
        self.stacked_widget.addWidget(self.todo_widget)

        # 设置页面
        self.settings_widget = SettingsWidget(self.settings, self.database)
        self.stacked_widget.addWidget(self.settings_widget)

        # 页面映射
        self.page_mapping = {
            "timer": 0,
            "stats": 1,
            "todo": 2,
            "settings": 3
        }

        # 设置默认页面
        self.stacked_widget.setCurrentIndex(0)

    def setup_system_tray(self):
        """设置系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("系统托盘不可用")
            return

        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示/隐藏窗口
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        # 快速操作
        start_study_action = QAction("开始学习", self)
        start_study_action.triggered.connect(self.quick_start_study)
        tray_menu.addAction(start_study_action)

        start_rest_action = QAction("开始休息", self)
        start_rest_action.triggered.connect(self.quick_start_rest)
        tray_menu.addAction(start_rest_action)

        tray_menu.addSeparator()

        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 双击托盘图标显示窗口
        self.tray_icon.activated.connect(self.on_tray_activated)

        # 显示托盘图标
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "专注学习计时器",
            "应用程序已最小化到系统托盘",
            QSystemTrayIcon.Information,
            2000
        )

    def setup_connections(self):
        """设置信号连接"""
        # 导航栏页面切换
        self.navigation_bar.page_changed.connect(self.switch_page)

        # 设置页面的信号连接
        if self.settings_widget:
            self.settings_widget.settings_changed.connect(self.on_settings_changed)

        # 计时器页面的信号连接
        if self.timer_widget:
            self.timer_widget.timer_finished.connect(self.on_timer_finished)
            self.timer_widget.timer_started.connect(self.on_timer_started)

    def switch_page(self, page_id: str):
        """切换页面"""
        if page_id in self.page_mapping:
            index = self.page_mapping[page_id]
            self.stacked_widget.setCurrentIndex(index)
            self.logger.info(f"切换到页面: {page_id}")

            # 页面激活时的特殊处理
            if page_id == "stats":
                self.stats_widget.refresh_data()

    def on_settings_changed(self, setting_key: str, value):
        """设置变更处理"""
        self.logger.info(f"设置变更: {setting_key} = {value}")

        # 根据设置变更更新相关组件
        if setting_key.startswith("timer."):
            if self.timer_widget:
                self.timer_widget.update_settings()

        elif setting_key.startswith("notification."):
            # 更新通知设置
            pass

        elif setting_key.startswith("ui."):
            # 更新UI设置
            self.update_ui_settings()

    def on_timer_started(self, timer_type: str, planned_duration: int, start_time=None):
        """计时器开始处理"""
        # 获取计时器类型名称
        timer_type_obj = self.settings.get_timer_type_by_id(timer_type)
        timer_name = timer_type_obj.get('name', '未知')
        self.logger.info(f"计时器开始: {timer_name}({timer_type}), 计划时长: {planned_duration}秒, 开始时间: {start_time}")
        
        # 记录计时器类型、计划时长和开始时间，但不立即创建会话
        # 只有在计时器完成或手动停止时才创建会话记录
        self.current_timer_type = timer_type
        self.current_planned_duration = planned_duration
        self.current_timer_start_time = start_time
    
    def on_timer_finished(self, timer_type: str, duration: int, auto_completed: bool = True):
        """计时器完成处理"""
        self.logger.info(f"计时器完成: {timer_type}, 时长: {duration}秒, 自动完成: {auto_completed}")

        # 获取计时器类型名称
        timer_type_obj = self.settings.get_timer_type_by_id(timer_type)
        timer_name = timer_type_obj.get('name', '未知')
        
        # 只有学习计时器且时长大于0时才记录
        session_id_for_note = None
        if timer_type == 'study' and duration > 0:
            try:
                # 在计时器完成时创建并结束会话
                # 使用之前保存的计时器类型和计划时长
                # 获取当前时间作为结束时间
                end_time = datetime.now()
                
                # 创建会话，使用保存的计时器开始时间
                session_id = self.database.start_session(self.current_timer_type, self.current_planned_duration, self.current_timer_start_time)
                self.logger.info(f"创建学习会话: ID={session_id}, 类型={self.current_timer_type}, 计划时长={self.current_planned_duration}秒, 开始时间={self.current_timer_start_time}")
                
                # 立即结束会话，使用实际计时的时长
                self.database.end_session(session_id, completed=True, actual_duration=duration)
                self.logger.info(f"结束学习会话: ID={session_id}, 实际时长={duration}秒, 结束时间={end_time}")
                
                # 保存会话ID用于备注
                session_id_for_note = session_id
                
                # 刷新统计页面数据（如果已加载）
                if self.stats_widget:
                    self.stats_widget.refresh_data()
                    
                # 重置当前计时器信息
                self.current_timer_type = None
                self.current_planned_duration = None
                self.current_timer_start_time = None
            except Exception as e:
                self.logger.error(f"记录学习时间失败: {e}")

        # 播放提醒音（先播放音乐，再显示弹窗）
        # 对所有计时器类型，在自动完成时都播放提示音
        if self.settings.get("notification.sound_enabled", True) and auto_completed:
            self.play_notification_sound()
            
        # 显示通知弹窗（对所有计时器类型）
        if self.settings.get("notification.popup_enabled", True):
            self.show_completion_notification(timer_type, duration, session_id_for_note)

            
        # 根据设置决定是否显示主窗口
        if self.settings.get("notification.show_main_window", True) and not self.isVisible():
            self.show_window()

        # 如果窗口被最小化或隐藏，显示系统托盘通知
        if (self.isMinimized() or not self.isVisible()) and self.tray_icon:
            message = f"{timer_name}计时完成！时长：{duration // 60}分{duration % 60}秒"
            self.tray_icon.showMessage(
                "计时完成",
                message,
                QSystemTrayIcon.Information,
                5000
            )

    def show_completion_notification(self, timer_type: str, duration: int, session_id=None):
        """显示完成通知弹窗"""
        minutes = duration // 60
        seconds = duration % 60

        timer_name = "学习" if timer_type == "study" else "休息"
        message = f"{timer_name}时间结束！\n持续时间：{minutes}分{seconds}秒"
        
        # 只有学习计时器才需要备注
        if timer_type == "study" and session_id is not None:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QComboBox, QFormLayout
            
            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("计时完成")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # 添加消息标签
            msg_label = QLabel(message)
            msg_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
            layout.addWidget(msg_label)
            
            # 创建表单布局
            form_layout = QFormLayout()
            layout.addLayout(form_layout)
            
            # 添加备注输入框
            note_input = QLineEdit()
            note_input.setPlaceholderText("记录这段时间做了什么...")
            note_input.setStyleSheet("padding: 8px;")
            form_layout.addRow("添加备注:", note_input)
            
            # 获取当前日期的TODO列表
            session_date = datetime.now().date()
            todo_items = self.database.get_todo_items(session_date.isoformat())
            
            # 添加TODO关联下拉框
            todo_combo = QComboBox()
            todo_combo.setStyleSheet("padding: 8px;")
            todo_combo.addItem("无关联", None)
            
            # 添加TODO项目到下拉框
            for todo in todo_items:
                todo_combo.addItem(todo['content'], todo['id'])
            
            form_layout.addRow("关联待办事项:", todo_combo)
            
            # 添加按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            # 设置对话框样式
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #ecf0f1;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QLabel {
                    font-size: 14px; 
                    color: #2c3e50;
                }
            """)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取备注内容
                note = note_input.text().strip()
                
                # 获取选中的TODO ID
                todo_id = todo_combo.currentData()
                
                try:
                    # 更新会话备注
                    if note:
                        self.database.update_session_notes(session_id, note)
                        self.logger.info(f"已添加会话备注: ID={session_id}, 备注={note}")
                    
                    # 更新关联的TODO
                    if todo_id is not None:
                        # 使用数据库方法更新关联的TODO
                        self.database.update_session_todo(session_id, todo_id)
                        self.logger.info(f"已关联TODO: 会话ID={session_id}, TODO ID={todo_id}")
                except Exception as e:
                    self.logger.error(f"更新会话信息失败: {e}")
        else:
            # 非学习计时器使用简单消息框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("计时完成")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)

            # 设置弹窗样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ecf0f1;
                    font-size: 14px;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                }
            """)

            msg_box.exec_()

    def play_notification_sound(self):
        """播放提醒音"""
        # 首先尝试从notification.sound.file获取音频文件路径
        sound_file = self.settings.get("notification.sound.file")
        
        # 如果没有找到，尝试从notification.sound_file获取（兼容旧版本配置）
        if not sound_file:
            sound_file = self.settings.get("notification.sound_file")
            
        if sound_file and os.path.exists(sound_file):
            try:
                # 使用音频管理器播放声音
                self.audio_manager.play_sound(sound_file)
                self.logger.info(f"播放提醒音: {sound_file}")
                
                # 如果计时器页面可见，更新音乐播放状态
                if self.stacked_widget.currentIndex() == self.page_mapping.get("timer", 0) and self.timer_widget:
                    self.timer_widget.is_music_playing = True
                    self.timer_widget.current_music_file = sound_file
                    self.timer_widget.play_music_button.setText("暂停音乐")
                    self.timer_widget.stop_music_button.setEnabled(True)
            except Exception as e:
                self.logger.error(f"播放提醒音失败: {e}")
                # 使用系统默认声音作为备选
                try:
                    import winsound
                    winsound.MessageBeep()
                except:
                    pass
        else:
            # 没有配置声音文件，使用系统默认声音
            try:
                import winsound
                winsound.MessageBeep()
            except ImportError:
                self.logger.warning("无法播放提醒音：winsound模块不可用")
            except Exception as e:
                self.logger.error(f"播放提醒音失败: {e}")

    def update_ui_settings(self):
        """更新UI设置"""
        # 更新字体大小
        font_size = self.settings.get("ui.font_size", 12)
        font = QFont("Microsoft YaHei", font_size)
        self.setFont(font)

        # 更新透明度
        opacity = self.settings.get("ui.opacity", 1.0)
        self.setWindowOpacity(opacity)

    def on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """显示并激活窗口（用于处理单例消息）"""
        self.logger.info("显示并激活窗口")
        # 如果窗口被最小化，则恢复它
        if self.isMinimized():
            self.showNormal()
        # 显示窗口
        self.show()
        # 激活窗口（置于前台）
        self.activateWindow()
        self.raise_()

    def quick_start_study(self):
        """快速开始学习"""
        self.show_window()
        self.switch_page("timer")
        if self.timer_widget:
            self.timer_widget.start_timer(type_id="study")

    def quick_start_rest(self):
        """快速开始休息"""
        self.show_window()
        self.switch_page("timer")
        if self.timer_widget:
            self.timer_widget.start_timer(type_id="rest")

    def setup_high_dpi_scaling(self):
        """设置高DPI缩放支持"""
        # 检测操作系统版本
        if platform.system() == "Windows":
            # 获取Windows版本
            win_version = platform.version()
            # 不使用logger，因为此时logger可能还未初始化
            print(f"Windows版本: {win_version}")
            
            # 设置Qt的高DPI缩放属性
            # 这些设置需要在创建QApplication后，显示窗口前设置
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # Windows 10特定的兼容性设置
            if "10." in win_version:
                print("应用Windows 10兼容性设置")
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
                    print(f"设置DPI感知失败: {e}")
    
    def restore_window_state(self):
        """恢复窗口状态"""
        window_size = self.settings.get("app.window_size", [800, 600])
        self.resize(window_size[0], window_size[1])

        window_position = self.settings.get("app.window_position")
        if window_position:
            self.move(window_position[0], window_position[1])
        else:
            # 居中显示
            screen = self.screen().availableGeometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )

    def save_window_state(self):
        """保存窗口状态"""
        self.settings.set("app.window_size", [self.width(), self.height()])
        self.settings.set("app.window_position", [self.x(), self.y()])

    def quit_application(self):
        """退出应用程序"""
        # 保存窗口状态
        self.save_window_state()

        # 停止当前计时器
        if self.timer_widget and self.timer_widget.is_running:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "计时器正在运行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

            self.timer_widget.stop_timer()

        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()

        # 直接退出应用程序，而不是调用close()
        QApplication.quit()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 关闭窗口时，隐藏窗口但保持托盘运行
        if self.tray_icon:
            event.ignore()
            self.hide()
            
            # 首次关闭窗口时显示提示
            if not self.settings.get("app.close_tip_shown", False):
                self.settings.set("app.close_tip_shown", True)
                self.tray_icon.showMessage(
                    "专注学习计时器",
                    "程序已隐藏到系统托盘，双击托盘图标可重新显示窗口。",
                    QSystemTrayIcon.Information,
                    3000
                )
        else:
            # 保存窗口状态
            self.save_window_state()
            event.accept()

    def changeEvent(self, event):
        """窗口状态变化事件"""
        if event.type() == event.WindowStateChange:
            # 当窗口最小化时，不再隐藏窗口，让其正常最小化到任务栏
            pass

        super().changeEvent(event)