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
import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, date


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
        # 确保UI完全构建后再加载设置
        self._load_settings()
        # 加载音频文件列表
        self._load_sound_files()
    
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
        
        # 数据导入组
        data_import_group = QGroupBox("数据导入")
        data_import_layout = QVBoxLayout(data_import_group)
        
        data_import_label = QLabel("从文件导入学习记录数据，支持JSON、Excel、SQL格式：")
        data_import_layout.addWidget(data_import_label)
        
        # 模板下载按钮
        template_layout = QHBoxLayout()
        template_label = QLabel("下载数据模板：")
        template_layout.addWidget(template_label)
        
        excel_template_btn = QPushButton("Excel模板")
        excel_template_btn.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        excel_template_btn.clicked.connect(lambda: self._download_template("excel"))
        template_layout.addWidget(excel_template_btn)
        
        template_layout.addStretch()
        data_import_layout.addLayout(template_layout)
        
        import_buttons_layout = QHBoxLayout()
        
        # JSON导入按钮
        json_import_btn = QPushButton("导入JSON文件")
        json_import_btn.setIcon(QIcon.fromTheme("document-open"))
        json_import_btn.clicked.connect(lambda: self._import_data("json"))
        import_buttons_layout.addWidget(json_import_btn)
        

        
        # Excel导入按钮
        excel_import_btn = QPushButton("导入Excel文件")
        excel_import_btn.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        excel_import_btn.clicked.connect(lambda: self._import_data("excel"))
        import_buttons_layout.addWidget(excel_import_btn)
        
        data_import_layout.addLayout(import_buttons_layout)
        data_layout.addWidget(data_import_group)
        
        # 创建提醒设置选项卡
        notification_tab = QWidget()
        notification_layout = QVBoxLayout(notification_tab)
        
        # 声音提醒设置
        sound_group = QGroupBox("声音提醒")
        sound_layout = QFormLayout(sound_group)
        
        self.sound_enabled_check = QCheckBox("启用声音提醒")
        sound_layout.addRow(self.sound_enabled_check)
        
        # 音频文件选择布局
        sound_file_layout = QHBoxLayout()
        self.sound_file_combo = QComboBox()
        self.sound_file_combo.setEditable(False)
        sound_file_layout.addWidget(self.sound_file_combo)
        
        self.import_sound_btn = QPushButton("导入音频")
        self.import_sound_btn.clicked.connect(self._import_sound_file)
        sound_file_layout.addWidget(self.import_sound_btn)
        
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
    
    def _download_template(self, format_type):
        """下载数据模板文件"""
        try:
            if format_type == "excel":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "保存Excel模板", "学习记录模板.xlsx", "Excel文件 (*.xlsx)"
                )
                if file_path:
                    try:
                        import pandas as pd
                        
                        # 创建示例数据，包含所有数据库字段
                        sample_data = [{
                            'ID': 1,
                            '日期': '2024-01-01',
                            '开始时间': '09:00',
                            '结束时间': '10:00',
                            '计时器类型': 'study',
                            '计划时长(秒)': 3600,
                            '实际时长(秒)': 3600,
                            '已完成': True,
                            '备注': '示例学习记录',
                            '关联待办ID': '',
                            '待办内容': '',
                            '创建时间': '2024-01-01 09:00:00'
                        }]
                        
                        df = pd.DataFrame(sample_data)
                        df.to_excel(file_path, index=False, engine='openpyxl')
                        
                        QMessageBox.information(self, "模板下载成功", f"Excel模板已保存到: {file_path}")
                    except ImportError:
                        QMessageBox.warning(self, "缺少依赖", "Excel模板功能需要安装pandas和openpyxl库")
        
        except Exception as e:
            self.logger.error(f"下载模板失败: {e}")
            QMessageBox.critical(self, "下载失败", f"下载模板时发生错误: {str(e)}")
    
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
            
            # 加载音频文件列表
            self._load_sound_files()
            
            # 设置当前选中的音频文件
            sound_file = self.settings.get('notification.sound.file', '')
            if sound_file and os.path.exists(sound_file):
                filename = os.path.basename(sound_file)
                index = self.sound_file_combo.findText(filename)
                if index >= 0:
                    self.sound_file_combo.setCurrentIndex(index)
            
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
            
            # 保存选中的音频文件完整路径
            selected_file = self.sound_file_combo.currentText()
            if selected_file:
                # 构建完整文件路径
                sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "sounds")
                full_path = os.path.join(sounds_dir, selected_file)
                self.settings.set('notification.sound.file', full_path)
            else:
                self.settings.set('notification.sound.file', '')
            
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
                    
                    # 转换数据格式以匹配导入模板，包含数据库中所有属性的字段名
                    # 确保字段顺序与导入模板一致
                    export_sessions = []
                    for session in sessions:
                        export_session = {
                            "date": session["date"],
                            "start_time": session["start_time"],
                            "end_time": session["end_time"],
                            "timer_type": session.get("timer_type", "study"),
                            "planned_duration": session["planned_duration"],
                            "actual_duration": session["actual_duration"],
                            "completed": session["completed"],
                            "notes": session.get("notes", ""),
                            "todo_id": session.get("todo_id"),
                            "todo_content": session.get("todo_content", ""),
                            "id": session["id"]
                        }
                        export_sessions.append(export_session)
                    
                    # 转换为JSON格式
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_sessions, f, ensure_ascii=False, indent=4)
                    
                    QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
            
            elif format_type == "sql":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出SQL脚本", f"{default_name}.sql", "SQL文件 (*.sql)"
                )
                if file_path:
                    # 获取所有学习记录
                    sessions = self.database.get_all_sessions()
                    
                    # 生成SQL脚本，包含表结构和数据
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("-- 专注学习计时器数据导出\n")
                        f.write("-- 导出时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
                        
                        # 创建表结构
                        f.write("""CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    timer_type TEXT NOT NULL,
    planned_duration INTEGER NOT NULL,
    actual_duration INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    todo_id INTEGER,
    todo_content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);\n\n""")
                        
                        # 插入数据
                        f.write("-- 插入学习记录数据\n")
                        for session in sessions:
                            f.write(f"INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, ")
                            f.write(f"planned_duration, actual_duration, completed, notes, todo_id, todo_content) VALUES (")
                            f.write(f"{session['id']}, '{session['date']}', '{session['start_time']}', ")
                            f.write(f"'{session['end_time']}', '{session['timer_type']}', {session['planned_duration']}, ")
                            f.write(f"{session['actual_duration']}, {1 if session['completed'] else 0}, ")
                            notes = session['notes'].replace("'", "''") if session['notes'] else ""
                            todo_id = session.get('todo_id', 'NULL')
                            todo_content = session.get('todo_content', '')
                            if todo_content:
                                todo_content = todo_content.replace("'", "''")
                            f.write(f"'{notes}', {todo_id}, '{todo_content}');\n")
                    
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
                        
                        # 重命名列，包含数据库中所有字段
                        df = df.rename(columns={
                            'id': 'ID',
                            'date': '日期',
                            'start_time': '开始时间',
                            'end_time': '结束时间',
                            'timer_type': '计时器类型',
                            'planned_duration': '计划时长(秒)',
                            'actual_duration': '实际时长(秒)',
                            'completed': '已完成',
                            'notes': '备注',
                            'todo_id': '关联待办ID',
                            'todo_content': '待办内容',
                            'created_at': '创建时间'
                        })
                        
                        # 导出到Excel
                        df.to_excel(file_path, index=False)
                        
                        QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
                    except ImportError:
                        QMessageBox.warning(self, "缺少依赖", "导出Excel需要安装pandas和openpyxl库，请使用pip安装：\npip install pandas openpyxl")
        
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出数据失败: {str(e)}")
    
    def _import_json_data(self, file_path):
        """导入JSON数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if not isinstance(data, list):
                QMessageBox.warning(self, "格式错误", "JSON文件应包含学习记录数组")
                return
            
            imported_count = 0
            for record in data:
                # 验证必需字段
                required_fields = ['date', 'start_time', 'end_time']
                if not all(field in record for field in required_fields):
                    # 兼容旧格式
                    old_required_fields = ['日期', '开始时间', '结束时间']
                    if not all(field in record for field in old_required_fields):
                        continue
                    # 转换旧格式到新格式
                    record['date'] = record['日期']
                    record['start_time'] = record['开始时间']
                    record['end_time'] = record['结束时间']
        
                # 计算持续时间（分钟）
                duration_minutes = 0
                if 'actual_duration' in record:
                    # 使用actual_duration字段（秒）
                    duration_minutes = record['actual_duration'] / 60
                elif '实际时长(秒)' in record:
                    # 兼容旧格式（秒转换为分钟）
                    duration_minutes = record['实际时长(秒)'] / 60
                elif 'actual_duration' in record:
                    # 兼容旧格式（秒转换为分钟）
                    duration_minutes = record['actual_duration'] / 60 if record['actual_duration'] else 0
                elif '实际时长(分钟)' in record:
                    duration_minutes = record['实际时长(分钟)']
                elif '计划时长(分钟)' in record:
                    duration_minutes = record['计划时长(分钟)']
                elif '时长(分钟)' in record:
                    duration_minutes = record['时长(分钟)']
        
                # 插入数据库，包含所有字段
                try:
                    self.database.add_session_direct(
                        record['date'],
                        record['start_time'],
                        record['end_time'],
                        duration_minutes,
                        record.get('notes', record.get('备注', '')),
                        record.get('todo_id', record.get('关联待办ID')),
                        record.get('timer_type', record.get('计时器类型', 'study')),
                        record.get('planned_duration'),
                        record.get('actual_duration'),
                        record.get('completed', True),
                        record.get('todo_content', ''),
                        record.get('id')
                    )
                    imported_count += 1
                except Exception as e:
                    self.logger.warning(f"导入记录失败: {e}")
                    continue
        
            QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条学习记录")
        
        except json.JSONDecodeError:
            QMessageBox.warning(self, "格式错误", "无效的JSON文件格式")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入JSON数据失败: {str(e)}")
    

    
    def _import_excel_data(self, file_path):
        """导入Excel数据"""
        try:
            import pandas as pd
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必需列
            required_columns = ['日期', '开始时间', '结束时间']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # 检查是否是英文列名
                english_required_columns = ['date', 'start_time', 'end_time']
                missing_english_columns = [col for col in english_required_columns if col not in df.columns]
                
                if missing_english_columns:
                    QMessageBox.warning(self, "格式错误", f"Excel文件缺少必需列: {', '.join(missing_columns)} 或 {', '.join(missing_english_columns)}")
                    return
                else:
                    # 重命名英文列名为中文
                    df = df.rename(columns={
                        'date': '日期',
                        'start_time': '开始时间',
                        'end_time': '结束时间',
                        'notes': '备注',
                        'todo_id': '关联待办ID',
                        'todo_content': '待办内容',
                        'timer_type': '计时器类型',
                        'planned_duration': '计划时长(秒)',
                        'actual_duration': '实际时长(秒)',
                        'completed': '已完成',
                        'id': 'ID'
                    })
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    # 处理日期格式
                    date_value = row['日期']
                    if isinstance(date_value, str):
                        date_str = date_value
                    else:
                        date_str = date_value.strftime('%Y-%m-%d')
                    
                    # 计算持续时间（分钟）
                    duration_minutes = 0
                    if '实际时长(秒)' in row:
                        # 使用实际时长(秒)字段
                        duration_minutes = float(row['实际时长(秒)']) / 60
                    elif 'actual_duration' in row:
                        # 兼容旧格式（秒转换为分钟）
                        duration_minutes = float(row['actual_duration']) / 60 if row['actual_duration'] else 0
                    elif '实际时长(分钟)' in row:
                        duration_minutes = float(row['实际时长(分钟)'])
                    elif '计划时长(分钟)' in row:
                        duration_minutes = float(row['计划时长(分钟)'])
                    elif '时长(分钟)' in row:
                        duration_minutes = float(row['时长(分钟)'])
                    
                    # 插入数据库，包含所有字段
                    self.database.add_session_direct(
                        date_str,
                        str(row['开始时间']),
                        str(row['结束时间']),
                        duration_minutes,
                        str(row.get('备注', '')),
                        row.get('关联待办ID'),
                        str(row.get('计时器类型', 'study')),
                        int(row.get('计划时长(秒)', 0)) if '计划时长(秒)' in row else None,
                        int(row.get('实际时长(秒)', 0)) if '实际时长(秒)' in row else None,
                        bool(row.get('已完成', True)) if '已完成' in row else True,
                        str(row.get('待办内容', '')) if '待办内容' in row else '',
                        int(row.get('ID', 0)) if 'ID' in row else None
                    )
                    imported_count += 1
                except Exception as e:
                    self.logger.warning(f"导入记录失败: {e}")
                    continue
            
            QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条学习记录")
            
        except ImportError:
            QMessageBox.warning(self, "缺少依赖", "导入Excel需要安装pandas和openpyxl库，请使用pip安装：\npip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入Excel数据失败: {str(e)}")
    
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

    def _import_data(self, format_type):
        """导入数据"""
        try:
            if format_type == "json":
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择JSON文件", "", "JSON文件 (*.json)"
                )
                if file_path:
                    self._import_json_data(file_path)
            elif format_type == "excel":
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
                )
                if file_path:
                    self._import_excel_data(file_path)
        except Exception as e:
            self.logger.error(f"导入数据失败: {e}")
            QMessageBox.critical(self, "导入失败", f"导入数据失败: {str(e)}")
    
    def _import_sound_file(self):
        """导入音频文件"""
        # 选择音频文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 获取文件名
                filename = os.path.basename(file_path)
                
                # 确保resources/sounds目录存在
                sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "sounds")
                os.makedirs(sounds_dir, exist_ok=True)
                
                # 目标文件路径
                target_path = os.path.join(sounds_dir, filename)
                
                # 复制文件
                import shutil
                shutil.copy2(file_path, target_path)
                
                # 重新加载音频文件列表
                self._load_sound_files()
                
                QMessageBox.information(self, "导入成功", f"音频文件已导入: {filename}")
                
            except Exception as e:
                self.logger.error(f"导入音频文件失败: {e}")
                QMessageBox.critical(self, "导入失败", f"导入音频文件失败: {str(e)}")
    
    def _load_sound_files(self):
        """加载音频文件列表"""
        try:
            # 清空下拉列表
            self.sound_file_combo.clear()
            
            # 获取resources/sounds目录路径
            sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "sounds")
            
            # 如果目录不存在，创建它
            if not os.path.exists(sounds_dir):
                os.makedirs(sounds_dir, exist_ok=True)
                return
            
            # 获取所有音频文件
            sound_files = []
            for file in os.listdir(sounds_dir):
                if file.lower().endswith((".mp3", ".wav")):
                    sound_files.append(file)
            
            # 添加到下拉列表
            self.sound_file_combo.addItems(sound_files)
            
        except Exception as e:
            self.logger.error(f"加载音频文件列表失败: {e}")