#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专注学习计时器 - 单例模式实现
作者: Assistant
版本: 1.0.0
"""

import sys
import os
import logging
import tempfile
import time
import win32gui
import win32con
import win32event
import win32api
import winerror
import ctypes
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

# 定义Windows消息常量
WM_SHOWAPP = win32con.WM_USER + 1

class SingletonApp:
    """
    单例应用程序类
    确保应用程序只运行一个实例，如果尝试启动第二个实例，
    则激活已运行的实例并退出当前实例。
    
    使用命名互斥锁和文件锁实现单例检测，更可靠且适用于Windows环境。
    """
    
    def __init__(self, app_id="FocusTimer.SingleInstance"):
        """
        初始化单例检测
        
        参数:
            app_id: 应用程序唯一标识符
        """
        self.app_id = app_id
        self.mutex_name = f"Global\\{app_id}"
        self.mutex = None
        self.hwnd = None
        self.logger = logging.getLogger(__name__)
        
        # 创建一个定时器，用于定期检查窗口是否存在
        self.check_timer = None
    
    def is_running(self):
        """
        检查应用程序是否已经在运行
        
        返回:
            bool: 如果应用程序已经在运行，则返回True，否则返回False
        """
        try:
            # 尝试创建一个命名互斥锁
            self.mutex = win32event.CreateMutex(None, False, self.mutex_name)
            last_error = win32api.GetLastError()
            
            # 如果互斥锁已经存在，则应用程序已经在运行
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                self.logger.info("检测到应用程序已经在运行")
                return True
            else:
                self.logger.info("应用程序实例是首次运行")
                return False
        except Exception as e:
            self.logger.error(f"检查应用程序实例时出错: {e}")
            return False
    
    def activate_running_instance(self):
        """
        激活已运行的应用程序实例
        
        返回:
            bool: 如果成功激活已运行的实例，则返回True，否则返回False
        """
        try:
            # 查找主窗口
            hwnd = win32gui.FindWindow(None, "专注学习计时器")
            if hwnd:
                # 如果窗口被最小化，则恢复它
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # 将窗口置于前台
                win32gui.SetForegroundWindow(hwnd)
                
                # 发送自定义消息以通知应用程序显示
                win32gui.PostMessage(hwnd, WM_SHOWAPP, 0, 0)
                
                self.logger.info("已激活运行中的应用程序实例")
                return True
            else:
                self.logger.warning("找不到运行中的应用程序窗口")
                
                # 如果找不到窗口，可能是因为窗口还没有创建完成
                # 或者窗口被隐藏了，我们可以尝试多次查找
                if not self.check_timer and QApplication.instance():
                    self.check_timer = QTimer()
                    self.check_timer.timeout.connect(self._check_window_exists)
                    self.check_timer.start(500)  # 每500毫秒检查一次
                    self.logger.info("启动窗口检查定时器")
                    
                    # 5秒后停止检查
                    QTimer.singleShot(5000, self._stop_check_timer)
                
                return False
        except Exception as e:
            self.logger.error(f"激活运行中的应用程序实例时出错: {e}")
            return False
    
    def _check_window_exists(self):
        """
        检查窗口是否存在，如果存在则激活它
        """
        try:
            hwnd = win32gui.FindWindow(None, "专注学习计时器")
            if hwnd:
                # 如果窗口被最小化，则恢复它
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # 将窗口置于前台
                win32gui.SetForegroundWindow(hwnd)
                
                # 发送自定义消息以通知应用程序显示
                win32gui.PostMessage(hwnd, WM_SHOWAPP, 0, 0)
                
                self.logger.info("已找到并激活运行中的应用程序实例")
                self._stop_check_timer()
        except Exception as e:
            self.logger.error(f"检查窗口是否存在时出错: {e}")
    
    def _stop_check_timer(self):
        """
        停止窗口检查定时器
        """
        if self.check_timer:
            self.check_timer.stop()
            self.check_timer = None
            self.logger.info("停止窗口检查定时器")
    
    def register_window_class(self, window_instance):
        """
        注册窗口以接收来自其他实例的消息
        
        参数:
            window_instance: 主窗口实例
        """
        self.hwnd = window_instance.winId()
        self.logger.info(f"注册窗口以接收单例消息: {self.hwnd}")