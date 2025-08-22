#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置页面模块
负责应用程序设置管理
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QCheckBox,
                             QTabWidget, QFormLayout, QLineEdit, QFileDialog,
                             QListWidget, QListWidgetItem, QGroupBox, QDialog,
                             QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

import os
import logging
from typing import Dict, List, Optional


class TimerTypeDialog(QDialog):
    """计时器类型编辑对话框"""
    
    def __init__(self, name="", duration=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑计时器类型")
        self.resize(300, 150)
        
        # 创建表单布局
        layout = QFormLayout(self)
        
        # 名称输入
        self.name_edit = QLineEdit(name)
        layout.addRow("名称:", self.name_edit)
        
        # 时长输入（分钟）
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)  # 1分钟到3小时
        self.duration_spin.setValue(duration // 60)  # 秒转分钟
        self.duration_spin.setSuffix(" 分钟")
        layout.addRow("时长:", self.duration_spin)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_values(self):
        """获取输入值"""
        return {
            "name": self.name_edit.text(),
            "duration": self.duration_spin.value() * 60  # 分钟转秒
        }


class SettingsWidget(QWidget):
    """设置页面组件"""
    
    # 设置变更信号
    settings_changed = pyqtSignal(str, object)
    
    def __init__(self, settings, database, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        self._build_ui()
        self._load_settings()
    
    def _build_ui(self):
        """构建界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("设置")
        title_label.setObjectName("pageTitle")
        main_layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建计时器设置选项卡
        timer_tab = QWidget()
        timer_layout = QVBoxLayout(timer_tab)
        
        # 计时器类型管理
        timer_group = QGroupBox("计时器类型")
        timer_group_layout = QVBoxLayout(timer_group)
        
        # 计时器类型列表
        self.timer_list = QListWidget()
        self.timer_list.setAlternatingRowColors(True)
        timer_group_layout.addWidget(self.timer_list)
        
        # 计时器类型操作按钮
        timer_buttons_layout = QHBoxLayout()
        
        self.add_timer_btn = QPushButton("添加")
        self.add_timer_btn.clicked.connect(self._add_timer_type)
        timer_buttons_layout.addWidget(self.add_timer_btn)
        
        self.edit_timer_btn = QPushButton("编辑")
        self.edit_timer_btn.clicked.connect(self._edit_timer_type)
        timer_buttons_layout.addWidget(self.edit_timer_btn)
        
        self.delete_timer_btn = QPushButton("删除")
        self.delete_timer_btn.clicked.connect(self._delete_timer_type)
        timer_buttons_layout.addWidget(self.delete_timer_btn)
        
        timer_group_layout.addLayout(timer_buttons_layout)
        timer_layout.addWidget(timer_group)
        
        # 自动切换设置
        auto_switch_group = QGroupBox("自动切换")
        auto_switch_layout = QVBoxLayout(auto_switch_group)
        
        self.auto_switch_check = QCheckBox("完成后自动切换到下一个计时器")
        auto_switch_layout.addWidget(self.auto_switch_check)
        
        timer_layout.addWidget(auto_switch_group)
        
        # 添加计时器选项卡
        self.tab_widget.addTab(timer_tab, "计时器")
        
        # 创建提醒设置选项卡
        notification_tab = QWidget()
        notification_layout = QVBoxLayout(notification_tab)
        
        # 声音提醒设置
        sound_group = QGroupBox("声音提醒")
        sound_layout = QFormLayout(sound_group)
        
        self.sound_enabled_check = QCheckBox("启用声音提醒")
        sound_layout.addRow(self.sound_enabled_check)
        
        sound_file_layout = QHBoxLayout()
        self.sound_file_edit = QLineEdit()
        self.sound_file_edit.setReadOnly(True)
        sound_file_layout.addWidget(self.sound_file_edit)
        
        self.browse_sound_btn = QPushButton("浏览...")
        self.browse_sound_btn.clicked.connect(self._browse_sound_file)
        sound_file_layout.addWidget(self.browse_sound_btn)
        
        sound_layout.addRow("提醒音乐:", sound_file_layout)
        notification_layout.addWidget(sound_group)
        
        # 弹窗提醒设置
        popup_group = QGroupBox("弹窗提醒")
        popup_layout = QVBoxLayout(popup_group)
        
        self.popup_enabled_check = QCheckBox("启用弹窗提醒")
        popup_layout.addWidget(self.popup_enabled_check)
        
        self.show_main_window_check = QCheckBox("计时结束后显示主窗口")
        popup_layout.addWidget(self.show_main_window_check)
        
        notification_layout.addWidget(popup_group)
        
        # 添加提醒选项卡
        self.tab_widget.addTab(notification_tab, "提醒")
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.reset_btn = QPushButton("重置为默认")
        self.reset_btn.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(self.reset_btn)
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 加载计时器类型
            self._load_timer_types()
            
            # 加载自动切换设置
            auto_switch = self.settings.get('timer.auto_switch', False)
            self.auto_switch_check.setChecked(auto_switch)
            
            # 加载声音提醒设置
            sound_enabled = self.settings.get('notification.sound.enabled', True)
            self.sound_enabled_check.setChecked(sound_enabled)
            
            sound_file = self.settings.get('notification.sound.file', '')
            self.sound_file_edit.setText(sound_file)
            
            # 加载弹窗提醒设置
            popup_enabled = self.settings.get('notification.popup.enabled', True)
            self.popup_enabled_check.setChecked(popup_enabled)
            
            # 加载计时结束后显示主窗口设置
            show_main_window = self.settings.get('notification.show_main_window', True)
            self.show_main_window_check.setChecked(show_main_window)
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
    
    def _load_timer_types(self):
        """加载计时器类型"""
        self.timer_list.clear()
        
        timer_types = self.settings.get_timer_types()
        for timer_type in timer_types:
            item = QListWidgetItem(f"{timer_type['name']} ({timer_type['duration'] // 60} 分钟)")
            item.setData(Qt.UserRole, timer_type)
            self.timer_list.addItem(item)
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 保存自动切换设置
            self.settings.set('timer.auto_switch', self.auto_switch_check.isChecked())
            
            # 保存声音提醒设置
            self.settings.set('notification.sound.enabled', self.sound_enabled_check.isChecked())
            self.settings.set('notification.sound.file', self.sound_file_edit.text())
            
            # 保存弹窗提醒设置
            self.settings.set('notification.popup.enabled', self.popup_enabled_check.isChecked())
            self.settings.set('notification.show_main_window', self.show_main_window_check.isChecked())
            
            # 保存设置到文件
            self.settings.save()
            
            # 发送设置变更信号
            self.settings_changed.emit("all", None)
            
            QMessageBox.information(self, "保存成功", "设置已保存")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置失败: {e}")
    
    def _reset_settings(self):
        """重置为默认设置"""
        reply = QMessageBox.question(self, "确认重置", "确定要重置所有设置为默认值吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 重置设置
                self.settings.reset_to_defaults()
                
                # 重新加载设置
                self._load_settings()
                
                # 发送设置变更信号
                self.settings_changed.emit("all", None)
                
                QMessageBox.information(self, "重置成功", "设置已重置为默认值")
                
            except Exception as e:
                self.logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "重置失败", f"重置设置失败: {e}")
    
    def _add_timer_type(self):
        """添加计时器类型"""
        dialog = TimerTypeDialog(parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                QMessageBox.warning(self, "输入错误", "名称不能为空")
                return
            
            try:
                # 添加计时器类型
                timer_type = {
                    "id": values["name"].lower().replace(" ", "_"),
                    "name": values["name"],
                    "duration": values["duration"],
                    "color": "#4CAF50",
                    "icon": "timer"
                }
                self.settings.add_timer_type(timer_type)
                
                # 重新加载计时器类型
                self._load_timer_types()
                
                # 发送设置变更信号
                self.settings_changed.emit("timer.types", None)
                
            except Exception as e:
                self.logger.error(f"添加计时器类型失败: {e}")
                QMessageBox.critical(self, "添加失败", f"添加计时器类型失败: {e}")
    
    def _edit_timer_type(self):
        """编辑计时器类型"""
        current_item = self.timer_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "选择错误", "请先选择一个计时器类型")
            return
        
        timer_type = current_item.data(Qt.UserRole)
        dialog = TimerTypeDialog(timer_type["name"], timer_type["duration"], parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                QMessageBox.warning(self, "输入错误", "名称不能为空")
                return
            
            try:
                # 更新计时器类型
                updates = {
                    "name": values["name"],
                    "duration": values["duration"]
                }
                self.settings.update_timer_type(timer_type["id"], updates)
                
                # 重新加载计时器类型
                self._load_timer_types()
                
                # 发送设置变更信号
                self.settings_changed.emit("timer.types", None)
                
            except Exception as e:
                self.logger.error(f"编辑计时器类型失败: {e}")
                QMessageBox.critical(self, "编辑失败", f"编辑计时器类型失败: {e}")
    
    def _delete_timer_type(self):
        """删除计时器类型"""
        current_item = self.timer_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "选择错误", "请先选择一个计时器类型")
            return
        
        timer_type = current_item.data(Qt.UserRole)
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", f"确定要删除计时器类型 '{timer_type['name']}' 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 删除计时器类型
                self.settings.remove_timer_type(timer_type["id"])
                
                # 重新加载计时器类型
                self._load_timer_types()
                
                # 发送设置变更信号
                self.settings_changed.emit("timer.types", None)
                
            except Exception as e:
                self.logger.error(f"删除计时器类型失败: {e}")
                QMessageBox.critical(self, "删除失败", f"删除计时器类型失败: {e}")
    
    def _browse_sound_file(self):
        """浏览音乐文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择提醒音乐", "", "音频文件 (*.mp3 *.wav);;所有文件 (*.*)"
        )
        
        if file_path:
            self.sound_file_edit.setText(file_path)