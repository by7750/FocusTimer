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
from datetime import datetime


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
        
        # 创建数据管理选项卡
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
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
        
        # 数据管理选项卡内容
        data_export_group = QGroupBox("数据导出")
        data_export_layout = QVBoxLayout(data_export_group)
        
        data_export_label = QLabel("导出学习记录数据，便于数据备份和迁移：")
        data_export_layout.addWidget(data_export_label)
        
        export_buttons_layout = QHBoxLayout()
        
        # JSON导出按钮
        json_export_btn = QPushButton("导出为JSON")
        json_export_btn.setIcon(QIcon.fromTheme("document-save"))
        json_export_btn.clicked.connect(lambda: self._export_data("json"))
        export_buttons_layout.addWidget(json_export_btn)
        
        # SQL导出按钮
        sql_export_btn = QPushButton("导出为SQL脚本")
        sql_export_btn.setIcon(QIcon.fromTheme("text-x-script"))
        sql_export_btn.clicked.connect(lambda: self._export_data("sql"))
        export_buttons_layout.addWidget(sql_export_btn)
        
        # Excel导出按钮
        excel_export_btn = QPushButton("导出为Excel")
        excel_export_btn.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        excel_export_btn.clicked.connect(lambda: self._export_data("excel"))
        export_buttons_layout.addWidget(excel_export_btn)
        
        data_export_layout.addLayout(export_buttons_layout)
        data_layout.addWidget(data_export_group)
        
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
        
        # 添加数据管理选项卡
        self.tab_widget.addTab(data_tab, "数据管理")
        
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
    
    def _export_data(self, format_type):
        """导出数据"""
        try:
            # 获取保存路径
            default_name = f"study_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format_type == "json":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出JSON数据", f"{default_name}.json", "JSON文件 (*.json)"
                )
                if file_path:
                    # 获取所有学习记录
                    sessions = self.database.get_all_sessions()
                    
                    # 转换为JSON格式
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(sessions, f, ensure_ascii=False, indent=4)
                    
                    QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
            
            elif format_type == "sql":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出SQL脚本", f"{default_name}.sql", "SQL文件 (*.sql)"
                )
                if file_path:
                    # 获取所有学习记录
                    sessions = self.database.get_all_sessions()
                    
                    # 生成SQL插入语句
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("-- 专注学习计时器数据导出\n")
                        f.write("-- 导出时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
                        
                        # 创建表结构
                        f.write("-- 创建学习记录表\n")
                        f.write("CREATE TABLE IF NOT EXISTS study_sessions (\n")
                        f.write("    id INTEGER PRIMARY KEY AUTOINCREMENT,\n")
                        f.write("    date DATE NOT NULL,\n")
                        f.write("    start_time DATETIME NOT NULL,\n")
                        f.write("    end_time DATETIME,\n")
                        f.write("    timer_type TEXT NOT NULL,\n")
                        f.write("    planned_duration INTEGER NOT NULL,\n")
                        f.write("    actual_duration INTEGER,\n")
                        f.write("    completed BOOLEAN DEFAULT FALSE,\n")
                        f.write("    notes TEXT,\n")
                        f.write("    created_at DATETIME DEFAULT CURRENT_TIMESTAMP\n")
                        f.write(");\n\n")
                        
                        # 插入数据
                        f.write("-- 插入学习记录数据\n")
                        for session in sessions:
                            f.write(f"INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, ")
                            f.write(f"planned_duration, actual_duration, completed, notes) VALUES (")
                            f.write(f"{session['id']}, '{session['date']}', '{session['start_time']}', ")
                            f.write(f"'{session['end_time']}', '{session['timer_type']}', {session['planned_duration']}, ")
                            f.write(f"{session['actual_duration']}, {1 if session['completed'] else 0}, ")
                            notes = session['notes'].replace("'", "''") if session['notes'] else ""
                            f.write(f"'{notes}');\n")
                    
                    QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
            
            elif format_type == "excel":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出Excel表格", f"{default_name}.xlsx", "Excel文件 (*.xlsx)"
                )
                if file_path:
                    # 获取所有学习记录
                    sessions = self.database.get_all_sessions()
                    
                    # 导出为Excel
                    try:
                        import pandas as pd
                        
                        # 转换为DataFrame
                        df = pd.DataFrame(sessions)
                        
                        # 重命名列
                        df = df.rename(columns={
                            'id': 'ID',
                            'date': '日期',
                            'start_time': '开始时间',
                            'end_time': '结束时间',
                            'timer_type': '计时器类型',
                            'planned_duration': '计划时长(秒)',
                            'actual_duration': '实际时长(秒)',
                            'completed': '是否完成',
                            'notes': '备注'
                        })
                        
                        # 导出到Excel
                        df.to_excel(file_path, index=False)
                        
                        QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
                    except ImportError:
                        QMessageBox.warning(self, "缺少依赖", "导出Excel需要安装pandas和openpyxl库，请使用pip安装：\npip install pandas openpyxl")
        
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出数据失败: {str(e)}")
    
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