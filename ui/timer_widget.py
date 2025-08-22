#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计时器组件模块
负责显示圆形倒计时进度
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRectF, QSize
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QIcon

import logging
import os
from datetime import datetime
from typing import Optional, Dict, List


class TimerWidget(QWidget):
    """圆形倒计时组件"""

    # 计时器信号
    timer_finished = pyqtSignal(str, int, bool)  # 参数：计时器类型ID, 持续时间（秒）, 是否自动完成
    timer_started = pyqtSignal(str, int, object)   # 参数：计时器类型ID, 计划时长（秒）, 开始时间

    def __init__(self, settings, database, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # 计时器设置
        self.total_seconds = 0  # 总时长（秒）
        self.remaining_seconds = 0  # 剩余时长（秒）
        self.is_running = False  # 是否正在运行
        self.is_paused = False  # 是否暂停
        self.current_timer_type = ""  # 当前计时器类型ID
        
        # 时间记录
        self.start_time = None  # 开始时间
        self.pause_time = None  # 暂停时间
        self.total_pause_duration = 0  # 累计暂停时长（秒）
        
        # 音乐播放设置
        self.audio_manager = None  # 音频管理器，由主窗口设置
        self.is_music_playing = False  # 是否正在播放音乐
        self.current_music_file = ""  # 当前播放的音乐文件
        
        # 样式设置
        self.background_color = QColor(240, 240, 240)  # 背景色
        self.ring_color = QColor(200, 200, 200)  # 圆环颜色
        self.progress_color = QColor(100, 149, 237)  # 进度颜色
        self.text_color = QColor(50, 50, 50)  # 文本颜色
        
        # 创建计时器
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1秒更新一次
        self.timer.timeout.connect(self._update_time)
        
        # 设置最小尺寸
        self.setMinimumSize(300, 300)
        
        # 构建UI
        self._build_ui()
        
        # 加载计时器类型
        self._load_timer_types()
        
        # 加载当前计时器类型
        self._load_current_timer_type()
        
    def _build_ui(self):
        """构建UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 计时器类型选择下拉框
        self.timer_type_combo = QComboBox()
        self.timer_type_combo.setMinimumHeight(30)
        self.timer_type_combo.currentIndexChanged.connect(self._on_timer_type_changed)
        main_layout.addWidget(self.timer_type_combo)
        
        # 添加空白区域，让计时器显示在中间
        main_layout.addStretch(1)
        
        # 计时器控制按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 开始/暂停按钮
        self.start_pause_button = QPushButton("开始")
        self.start_pause_button.setMinimumSize(80, 40)
        self.start_pause_button.clicked.connect(self._on_start_pause_clicked)
        button_layout.addWidget(self.start_pause_button)
        
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setMinimumSize(80, 40)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.setMinimumSize(80, 40)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self.reset_button)
        
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        
        # 音乐控制按钮区域
        music_layout = QHBoxLayout()
        music_layout.setSpacing(10)
        
        # 播放/暂停音乐按钮
        self.play_music_button = QPushButton("播放音乐")
        self.play_music_button.setMinimumSize(80, 40)
        self.play_music_button.clicked.connect(self._on_play_music_clicked)
        music_layout.addWidget(self.play_music_button)
        
        # 停止音乐按钮
        self.stop_music_button = QPushButton("停止音乐")
        self.stop_music_button.setMinimumSize(80, 40)
        self.stop_music_button.clicked.connect(self._on_stop_music_clicked)
        self.stop_music_button.setEnabled(False)
        music_layout.addWidget(self.stop_music_button)
        
        main_layout.addLayout(music_layout)
        
        # 设置样式
        self._setup_styles()
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                color: #aaa;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
    
    def _load_timer_types(self):
        """加载计时器类型"""
        self.timer_type_combo.clear()
        timer_types = self.settings.get_timer_types()
        
        for timer_type in timer_types:
            self.timer_type_combo.addItem(timer_type.get('name'), timer_type.get('id'))
    
    def _load_current_timer_type(self):
        """加载当前计时器类型"""
        current_type = self.settings.get_current_timer_type()
        current_id = current_type.get('id', 'study')
        
        # 设置下拉框选中项
        for i in range(self.timer_type_combo.count()):
            if self.timer_type_combo.itemData(i) == current_id:
                self.timer_type_combo.setCurrentIndex(i)
                break
        
        # 设置计时器时间
        self.set_timer_type(current_id)
    
    def set_timer_type(self, type_id: str):
        """设置计时器类型"""
        timer_type = self.settings.get_timer_type_by_id(type_id)
        if timer_type:
            self.current_timer_type = type_id
            self.total_seconds = timer_type.get('duration', 0)
            self.remaining_seconds = self.total_seconds
            self.progress_color = QColor(timer_type.get('color', '#4CAF50'))
            self.update()
    
    def _on_timer_type_changed(self, index: int):
        """计时器类型变更处理"""
        if index >= 0:
            type_id = self.timer_type_combo.itemData(index)
            self.set_timer_type(type_id)
            self.settings.set_current_timer_type(type_id)
            
            # 确保切换计时器类型后，计时器处于停止状态
            self.is_running = False
            self.is_paused = False
            self.timer.stop()
            self.start_pause_button.setText("开始")
            self.stop_button.setEnabled(False)
    
    def _on_start_pause_clicked(self):
        """开始/暂停按钮点击处理"""
        if self.is_running:
            self.pause_timer()
        else:
            self.start_timer()
    
    def _on_stop_clicked(self):
        """停止按钮点击处理"""
        self.stop_timer()
    
    def _on_reset_clicked(self):
        """重置按钮点击处理"""
        self.reset_timer()
    
    def set_total_time(self, seconds: int):
        """设置总时长"""
        self.total_seconds = max(0, seconds)
        self.remaining_seconds = self.total_seconds
        self.update()
        
    def set_remaining_time(self, seconds: int):
        """设置剩余时长"""
        self.remaining_seconds = max(0, min(seconds, self.total_seconds))
        self.update()
        
    def start_timer(self, type_id: str = None):
        """开始计时"""
        # 如果指定了计时器类型，先切换
        if type_id:
            for i in range(self.timer_type_combo.count()):
                if self.timer_type_combo.itemData(i) == type_id:
                    self.timer_type_combo.setCurrentIndex(i)
                    break
        
        if self.remaining_seconds > 0:
            self.is_running = True
            self.is_paused = False
            self.timer.start()
            self.update()
            
            # 更新按钮状态
            self.start_pause_button.setText("暂停")
            self.stop_button.setEnabled(True)
            
            # 记录开始时间（如果是首次开始，而不是从暂停恢复）
            if self.start_time is None:
                self.start_time = datetime.now()
                self.total_pause_duration = 0
                # 发送计时器开始信号，包含开始时间
                self.timer_started.emit(self.current_timer_type, self.total_seconds, self.start_time)
            else:
                # 从暂停恢复，计算暂停时长并累加
                if self.pause_time is not None:
                    pause_duration = (datetime.now() - self.pause_time).total_seconds()
                    self.total_pause_duration += pause_duration
                    self.pause_time = None
            
    def pause_timer(self):
        """暂停计时"""
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            self.timer.stop()
            self.update()
            
            # 记录暂停时间
            self.pause_time = datetime.now()
            
            # 更新按钮状态
            self.start_pause_button.setText("继续")
            
    def stop_timer(self):
        """停止计时"""
        # 先暂停计时器，确保时间立即停止
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        self.update()
        
        # 更新按钮状态
        self.start_pause_button.setText("开始")
        self.stop_button.setEnabled(False)
        
        # 计算实际学习时间（总时间减去剩余时间）
        elapsed_time = self.total_seconds - self.remaining_seconds
        
        # 只有学习计时器且已经计时了一段时间才发送信号
        if self.current_timer_type == 'study' and elapsed_time > 0 and self.start_time is not None:
            # 如果当前处于暂停状态，使用暂停时间作为结束时间
            # 否则使用当前时间作为结束时间
            end_time = self.pause_time if self.pause_time else datetime.now()
            # 计算实际学习时间（总时间减去剩余时间）
            # elapsed_time = (end_time - self.start_time).total_seconds() - self.total_pause_duration
            
            # 发送计时器完成信号，手动停止时auto_completed=False
            self.timer_finished.emit(self.current_timer_type, elapsed_time, False)
        
        # 重置时间记录
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        
    def reset_timer(self):
        """重置计时器"""
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        self.update()
        
        # 重置时间记录
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        
        # 更新按钮状态
        self.start_pause_button.setText("开始")
        self.stop_button.setEnabled(False)
        
    def _update_time(self):
        """更新时间"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update()
            
            # 检查是否完成
            if self.remaining_seconds == 0:
                self.is_running = False
                self.is_paused = False
                self.timer.stop()
                
                # 更新按钮状态
                self.start_pause_button.setText("开始")
                self.stop_button.setEnabled(False)
                
                # 计算实际学习时间（总时间减去剩余时间）
                elapsed_time = self.total_seconds - self.remaining_seconds
                
                # 记录完成的计时器类型和时长，对所有计时器类型都发送信号
                # 发送计时器完成信号，自动完成时auto_completed=True
                self.timer_finished.emit(self.current_timer_type, self.total_seconds, True)
                
                # 重置时间记录
                self.start_time = None
                self.pause_time = None
                self.total_pause_duration = 0
                
                # 如果设置了自动切换，切换到下一个计时器类型
                if self.settings.get("timer.auto_switch", False):
                    self._switch_to_next_timer_type()
                    
                    # 不再自动开始下一个计时器，始终保持就绪状态
                    # 用户需要手动点击开始按钮才能开始计时
                    # if self.settings.get("timer.auto_start_next", False):
                    #     self.start_timer()
    
    def _switch_to_next_timer_type(self):
        """切换到下一个计时器类型
        如果当前是学习计时器，则切换到休息计时器
        如果当前是休息计时器，则切换到学习计时器
        如果是其他计时器，则重置当前计时器
        注意：此方法只切换计时器类型，不会自动开始计时
        """
        current_type_id = self.current_timer_type
        
        # 如果是学习计时器，切换到休息计时器
        if current_type_id == "study":
            for i in range(self.timer_type_combo.count()):
                if self.timer_type_combo.itemData(i) == "rest":
                    self.timer_type_combo.setCurrentIndex(i)
                    self.logger.info("从学习计时器切换到休息计时器")
                    # 确保计时器处于就绪状态
                    self.is_running = False
                    self.is_paused = False
                    self.timer.stop()
                    self.start_pause_button.setText("开始")
                    self.stop_button.setEnabled(False)
                    return
        
        # 如果是休息计时器，切换到学习计时器
        elif current_type_id == "rest":
            for i in range(self.timer_type_combo.count()):
                if self.timer_type_combo.itemData(i) == "study":
                    self.timer_type_combo.setCurrentIndex(i)
                    self.logger.info("从休息计时器切换到学习计时器")
                    # 确保计时器处于就绪状态
                    self.is_running = False
                    self.is_paused = False
                    self.timer.stop()
                    self.start_pause_button.setText("开始")
                    self.stop_button.setEnabled(False)
                    return
        
        # 如果是其他计时器，重置当前计时器
        self.logger.info(f"重置计时器类型: {current_type_id}")
        self.reset_timer()
                
    def _format_time(self) -> str:
        """格式化时间显示"""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        
        # 计算中心点和半径
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 60  # 留出边距，考虑到按钮区域
        
        # 绘制背景
        painter.fillRect(event.rect(), self.background_color)
        
        # 绘制外圆环
        pen = QPen(self.ring_color)
        pen.setWidth(10)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))
        
        # 计算进度角度
        if self.total_seconds > 0:
            progress = self.remaining_seconds / self.total_seconds
            angle = int(360 * progress)
        else:
            angle = 0
            
        # 绘制进度圆环
        pen = QPen(self.progress_color)
        pen.setWidth(10)
        painter.setPen(pen)
        
        # 从12点钟方向开始，顺时针绘制
        painter.drawArc(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2), 
                       90 * 16, -angle * 16)  # Qt中角度单位是1/16度
        
        # 绘制时间文本
        time_text = self._format_time()
        font = QFont("Arial", int(radius / 3))
        painter.setFont(font)
        painter.setPen(self.text_color)
        painter.drawText(QRectF(center_x - radius, center_y - radius / 2, radius * 2, radius), 
                        Qt.AlignCenter, time_text)
        
        # 绘制状态文本
        if self.is_running:
            status_text = "运行中"
        elif self.is_paused:
            status_text = "已暂停"
        else:
            status_text = "就绪"
            
        font = QFont("Arial", int(radius / 6))
        painter.setFont(font)
        painter.drawText(QRectF(center_x - radius, center_y + radius / 4, radius * 2, radius / 2), 
                        Qt.AlignCenter, status_text)
        
        # 绘制计时器类型名称
        timer_type = self.settings.get_timer_type_by_id(self.current_timer_type)
        type_name = timer_type.get('name', '')
        
        font = QFont("Arial", int(radius / 6))
        painter.setFont(font)
        painter.drawText(QRectF(center_x - radius, center_y - radius, radius * 2, radius / 2), 
                        Qt.AlignCenter, type_name)
        
    def sizeHint(self) -> QSize:
        """推荐尺寸"""
        return QSize(400, 500)
        
    def update_settings(self):
        """更新设置"""
        # 保存当前选中的计时器类型ID
        current_id = self.current_timer_type
        
        # 重新加载计时器类型
        self._load_timer_types()
        
        # 如果当前正在运行，不要改变计时器类型
        if self.is_running or self.is_paused:
            return
            
        # 如果之前有选中的计时器类型，尝试恢复选中状态
        if current_id:
            # 检查该ID是否仍然存在
            timer_type = self.settings.get_timer_type_by_id(current_id)
            if timer_type:
                # 设置下拉框选中项
                for i in range(self.timer_type_combo.count()):
                    if self.timer_type_combo.itemData(i) == current_id:
                        self.timer_type_combo.setCurrentIndex(i)
                        break
                # 更新计时器设置
                self.set_timer_type(current_id)
            else:
                # 如果之前选中的计时器类型已被删除，加载当前设置的计时器类型
                self._load_current_timer_type()
        else:
            # 如果之前没有选中的计时器类型，加载当前设置的计时器类型
            self._load_current_timer_type()
            
    def set_audio_manager(self, audio_manager):
        """设置音频管理器"""
        self.audio_manager = audio_manager
        
    def _on_play_music_clicked(self):
        """播放/暂停音乐按钮点击处理"""
        if not self.audio_manager:
            self.logger.warning("音频管理器未初始化")
            return
            
        if self.is_music_playing:
            # 如果正在播放，则暂停
            self.pause_music()
        else:
            # 如果未播放，则开始播放
            self.play_music()
            
    def _on_stop_music_clicked(self):
        """停止音乐按钮点击处理"""
        self.stop_music()
        
    def play_music(self):
        """播放音乐"""
        if not self.audio_manager:
            self.logger.warning("音频管理器未初始化")
            return False
            
        # 获取音乐文件路径
        sound_file = self.settings.get("notification.sound.file")
        if not sound_file:
            sound_file = self.settings.get("notification.sound_file")
            
        if not sound_file or not os.path.exists(sound_file):
            self.logger.warning(f"音乐文件不存在: {sound_file}")
            return False
            
        # 确保先停止当前播放的音乐
        self.audio_manager.stop_sound()
        
        # 播放音乐
        self.logger.info(f"尝试播放音乐文件: {sound_file}")
        success = self.audio_manager.play_sound(sound_file, loop=True)
        if success:
            self.is_music_playing = True
            self.current_music_file = sound_file
            self.play_music_button.setText("暂停音乐")
            self.stop_music_button.setEnabled(True)
            self.logger.info(f"成功开始播放音乐: {sound_file}")
            return True
        else:
            self.logger.error("播放音乐失败")
            return False
            
    def pause_music(self):
        """暂停音乐"""
        if not self.audio_manager or not self.is_music_playing:
            return
            
        self.audio_manager.stop_sound()
        self.is_music_playing = False
        self.play_music_button.setText("播放音乐")
        self.logger.info("暂停音乐播放")
        
    def stop_music(self):
        """停止音乐"""
        if not self.audio_manager:
            return
            
        self.audio_manager.stop_sound()
        self.is_music_playing = False
        self.current_music_file = ""
        self.play_music_button.setText("播放音乐")
        self.stop_music_button.setEnabled(False)
        self.logger.info("停止音乐播放")