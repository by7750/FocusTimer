#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO列表页面组件
负责显示和管理待办事项
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QLineEdit, QPushButton, QLabel, QCheckBox, QDateEdit, QMenu,
                             QAction, QMessageBox, QFrame, QSizePolicy, QToolButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QDate
from PyQt5.QtGui import QIcon, QFont, QColor

import logging
from datetime import datetime, date
from typing import List, Dict, Optional

# 项目模块导入
from config.settings import Settings
from config.database import Database


class TodoItem(QWidget):
    """TODO项目组件"""
    
    # 定义信号
    completed_changed = pyqtSignal(int, bool)  # ID, 是否完成
    deleted = pyqtSignal(int)  # ID
    edited = pyqtSignal(int, str)  # ID, 新内容
    
    def __init__(self, todo_data: Dict, parent=None):
        super().__init__(parent)
        self.todo_data = todo_data
        self.todo_id = todo_data['id']
        self.content = todo_data['content']
        self.completed = bool(todo_data['completed'])
        self.priority = todo_data.get('priority', 0)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 设置最小高度，确保内容完全显示
        self.setMinimumHeight(40)
        
        # 完成状态复选框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self.on_completed_changed)
        layout.addWidget(self.checkbox)
        
        # 内容标签
        self.content_label = QLabel(self.content)
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.content_label.setWordWrap(True)
        self.content_label.setMinimumHeight(40)
        self.content_label.setAlignment(Qt.AlignVCenter)  # 垂直居中对齐

        # 根据完成状态设置样式
        self.update_style()
        
        layout.addWidget(self.content_label)
        
        # 编辑按钮
        self.edit_btn = QToolButton()
        self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("编辑")
        self.edit_btn.setMinimumSize(30, 30)
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        layout.addWidget(self.edit_btn)
        
        # 删除按钮
        self.delete_btn = QToolButton()
        self.delete_btn.setText("🗑️")
        self.delete_btn.setToolTip("删除")
        self.delete_btn.setMinimumSize(30, 30)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)
        
    def update_style(self):
        """根据完成状态更新样式"""
        if self.completed:
            self.content_label.setStyleSheet(
                "text-decoration: line-through; color: #7f8c8d;"
            )
        else:
            # 根据优先级设置不同的颜色
            if self.priority >= 2:
                color = "#e74c3c"  # 高优先级，红色
            elif self.priority == 1:
                color = "#f39c12"  # 中优先级，橙色
            else:
                color = "#2c3e50"  # 普通优先级，深蓝色
                
            self.content_label.setStyleSheet(f"color: {color};")
    
    def on_completed_changed(self, state):
        """完成状态变化处理"""
        self.completed = (state == Qt.Checked)
        self.update_style()
        self.completed_changed.emit(self.todo_id, self.completed)
    
    def on_edit_clicked(self):
        """编辑按钮点击处理"""
        from PyQt5.QtWidgets import QInputDialog
        
        new_content, ok = QInputDialog.getText(
            self, "编辑待办事项", "内容:", text=self.content
        )
        
        if ok and new_content.strip():
            self.content = new_content
            self.content_label.setText(new_content)
            self.edited.emit(self.todo_id, new_content)
    
    def on_delete_clicked(self):
        """删除按钮点击处理"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个待办事项吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.deleted.emit(self.todo_id)


class TodoWidget(QWidget):
    """TODO列表页面组件"""
    
    def __init__(self, settings: Settings, database: Database, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # 当前选择的日期
        self.current_date = date.today()
        
        # 构建UI
        self.setup_ui()
        
        # 加载数据
        self.load_todo_items()
    
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 顶部日期选择和标题
        top_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("待办事项")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        # 日期选择
        date_label = QLabel("日期:")
        top_layout.addWidget(date_label)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.on_date_changed)
        top_layout.addWidget(self.date_edit)
        
        main_layout.addLayout(top_layout)
        
        # 待办事项列表
        self.todo_list = QListWidget()
        self.todo_list.setFrameStyle(QFrame.NoFrame)
        self.todo_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 5px;
                margin-bottom: 8px;
                padding: 8px;
                min-height: 40px;
            }
        """)
        main_layout.addWidget(self.todo_list)
        
        # 底部输入框和按钮
        bottom_layout = QHBoxLayout()
        
        self.new_todo_input = QLineEdit()
        self.new_todo_input.setPlaceholderText("添加新的待办事项...")
        self.new_todo_input.returnPressed.connect(self.add_todo_item)
        self.new_todo_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        bottom_layout.addWidget(self.new_todo_input)
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_todo_item)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219653;
            }
        """)
        bottom_layout.addWidget(self.add_btn)
        
        main_layout.addLayout(bottom_layout)
    
    def load_todo_items(self):
        """加载待办事项列表"""
        self.todo_list.clear()
        
        # 获取当前日期的待办事项
        date_str = self.current_date.isoformat()
        todo_items = self.database.get_todo_items(date_str, include_completed=True)
        
        if not todo_items:
            # 如果没有待办事项，显示提示
            empty_item = QListWidgetItem()
            empty_widget = QLabel("今天没有待办事项，添加一个吧！")
            empty_widget.setAlignment(Qt.AlignCenter)
            empty_widget.setStyleSheet("color: #7f8c8d; padding: 20px;")
            
            empty_item.setSizeHint(empty_widget.sizeHint())
            self.todo_list.addItem(empty_item)
            self.todo_list.setItemWidget(empty_item, empty_widget)
            return
        
        # 先添加未完成的项目
        incomplete_items = [item for item in todo_items if not item['completed']]
        for todo_item in incomplete_items:
            self._add_todo_item_to_list(todo_item)
        
        # 再添加已完成的项目
        complete_items = [item for item in todo_items if item['completed']]
        for todo_item in complete_items:
            self._add_todo_item_to_list(todo_item)
    
    def _add_todo_item_to_list(self, todo_data):
        """将待办事项添加到列表中"""
        list_item = QListWidgetItem()
        
        # 创建自定义组件
        item_widget = TodoItem(todo_data)
        
        # 连接信号
        item_widget.completed_changed.connect(self.on_item_completed_changed)
        item_widget.deleted.connect(self.on_item_deleted)
        item_widget.edited.connect(self.on_item_edited)
        
        # 设置列表项大小
        size_hint = item_widget.sizeHint()
        # 确保高度足够
        if size_hint.height() < 50:
            size_hint.setHeight(50)
        list_item.setSizeHint(size_hint)
        
        # 添加到列表
        self.todo_list.addItem(list_item)
        self.todo_list.setItemWidget(list_item, item_widget)
    
    def add_todo_item(self):
        """添加新的待办事项"""
        content = self.new_todo_input.text().strip()
        if not content:
            return
        
        # 添加到数据库
        date_str = self.current_date.isoformat()
        todo_id = self.database.add_todo_item(content, date_str)
        
        # 清空输入框
        self.new_todo_input.clear()
        
        # 重新加载列表
        self.load_todo_items()
    
    def on_date_changed(self, qdate):
        """日期变化处理"""
        self.current_date = date(qdate.year(), qdate.month(), qdate.day())
        self.load_todo_items()
    
    def on_item_completed_changed(self, todo_id, completed):
        """项目完成状态变化处理"""
        self.database.update_todo_item(todo_id, completed=completed)
        # 延迟重新加载，以便用户可以看到状态变化
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self.load_todo_items)
    
    def on_item_deleted(self, todo_id):
        """项目删除处理"""
        self.database.delete_todo_item(todo_id)
        self.load_todo_items()
    
    def on_item_edited(self, todo_id, new_content):
        """项目编辑处理"""
        self.database.update_todo_item(todo_id, content=new_content)