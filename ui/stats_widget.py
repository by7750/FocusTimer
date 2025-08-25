#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计页面模块
负责展示学习时间统计数据
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTabWidget, QCalendarWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                             QScrollArea, QSizePolicy, QComboBox, QPushButton,
                             QBoxLayout)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QMargins
from PyQt5.QtGui import QColor, QPalette, QPainter, QFont
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis, QBarSeries, QBarSet, QBarCategoryAxis

from datetime import datetime, date, timedelta
import logging


def seconds_to_minutes_text(seconds: int) -> str:
    """将秒转换为分钟文本"""
    m = round(max(0, int(seconds)) / 60.0, 1)
    return f"{m}"


def seconds_to_hours_text(seconds: int) -> str:
    """将秒转换为小时文本"""
    h = round(max(0, int(seconds)) / 3600.0, 2)
    return f"{h}"


class StatsWidget(QWidget):
    """统计页面组件"""
    
    def __init__(self, settings, database, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.current_selected_date = None  # 初始化当前选中的日期
        
        self._build_ui()
        self._setup_styles()
        self._load_data()
        
    def refresh_data(self):
        """刷新统计数据"""
        self._load_data()
        
        # 如果有选中的日期，重新加载该日期的会话记录
        if hasattr(self, 'current_selected_date') and self.current_selected_date is not None:
            try:
                qt_date = QDate(self.current_selected_date.year, 
                               self.current_selected_date.month, 
                               self.current_selected_date.day)
                self._on_date_clicked(qt_date)
            except Exception as e:
                self.logger.error(f"刷新选中日期数据失败: {e}")
                # 重置当前选中日期
                self.current_selected_date = None

    def _build_ui(self):
        """构建界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("学习统计")
        title_label.setObjectName("pageTitle")
        main_layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建图表选项卡
        chart_tab = QWidget()
        chart_layout = QVBoxLayout(chart_tab)
        
        # 创建分割器，用于响应式布局
        chart_splitter = QSplitter(Qt.Vertical)
        
        # 创建折线图
        self.chart_view = self._create_chart()
        self.chart_view.setMinimumHeight(250)  # 设置最小高度
        chart_splitter.addWidget(self.chart_view)
        
        # 创建表格
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['日期', '学习时长(分钟)'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(150)  # 减小最小高度
        self.table.setSizePolicy(self.table.sizePolicy().horizontalPolicy(), self.table.sizePolicy().Expanding)
        chart_splitter.addWidget(self.table)
        
        # 设置分割器比例 (图表:表格 = 2:1)
        chart_splitter.setSizes([400, 200])
        chart_layout.addWidget(chart_splitter)
        
        # 添加图表选项卡
        self.tab_widget.addTab(chart_tab, "趋势图")
        
        # 创建日历选项卡
        calendar_tab = QWidget()
        calendar_main_layout = QVBoxLayout(calendar_tab)
        calendar_main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建滚动内容容器
        scroll_content = QWidget()
        calendar_layout = QVBoxLayout(scroll_content)
        calendar_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建上部分割器，用于日历和详情
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 创建日历
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        self.calendar.clicked.connect(self._on_date_clicked)
        self.calendar.setMinimumSize(300, 250)  # 设置最小尺寸
        top_splitter.addWidget(self.calendar)
        
        # 日期详情
        self.date_details = QLabel("选择日期查看详情")
        self.date_details.setAlignment(Qt.AlignCenter)
        self.date_details.setMinimumHeight(100)
        self.date_details.setMinimumWidth(200)
        self.date_details.setWordWrap(True)  # 允许文本换行
        self.date_details.setStyleSheet("QLabel { padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9; }")
        top_splitter.addWidget(self.date_details)
        
        # 设置上部分割器比例
        top_splitter.setSizes([400, 300])
        calendar_layout.addWidget(top_splitter)
        
        # 添加记录按钮
        from PyQt5.QtWidgets import QPushButton
        add_record_layout = QHBoxLayout()
        add_record_layout.setAlignment(Qt.AlignRight)
        self.add_record_button = QPushButton("添加学习记录")
        self.add_record_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_record_button.clicked.connect(self._add_study_record)
        add_record_layout.addWidget(self.add_record_button)
        calendar_layout.addLayout(add_record_layout)
        
        # 创建学习记录表格
        self.sessions_table = QTableWidget(0, 7)  # 增加一列用于TODO关联
        self.sessions_table.setHorizontalHeaderLabels(['ID', '开始时间', '结束时间', '时长(分钟)', '备注', '关联待办', '操作'])
        
        # 设置列宽自适应
        header = self.sessions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID列
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 开始时间列
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 结束时间列
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 时长列
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 备注列自适应宽度
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # 关联待办列自适应宽度
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 操作列
        
        self.sessions_table.setMinimumHeight(150)  # 减小最小高度
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 默认不可编辑
        self.sessions_table.cellDoubleClicked.connect(self._on_session_cell_double_clicked)  # 双击事件
        
        # 设置表格的水平滚动策略
        self.sessions_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sessions_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        calendar_layout.addWidget(self.sessions_table)
        
        # 创建TODO统计卡片容器
        self._create_todo_stats_cards(calendar_layout)
        
        # 将滚动内容设置到滚动区域
        scroll_area.setWidget(scroll_content)
        calendar_main_layout.addWidget(scroll_area)
        
        # 添加日历选项卡
        self.tab_widget.addTab(calendar_tab, "日历视图")
        
        # 设置样式
        self._setup_styles()

    def _create_todo_stats_cards(self, parent_layout):
        """创建TODO统计卡片"""
        # 创建卡片容器 - 使用QWidget作为容器以支持响应式布局
        self.cards_container_widget = QWidget()
        self.cards_container = QHBoxLayout(self.cards_container_widget)
        self.cards_container.setSpacing(15)
        self.cards_container.setContentsMargins(0, 10, 0, 0)
        
        # 左侧卡片 - 柱状图
        self.chart_card = self._create_chart_card()
        self.cards_container.addWidget(self.chart_card)
        
        # 右侧卡片 - 文字信息表格
        self.info_card = self._create_info_card()
        self.cards_container.addWidget(self.info_card)
        
        # 设置卡片比例 (图表:表格 = 3:2)
        self.cards_container.setStretchFactor(self.chart_card, 3)
        self.cards_container.setStretchFactor(self.info_card, 2)
        
        # 添加到父布局
        parent_layout.addWidget(self.cards_container_widget)
        
        # 安装事件过滤器以监听窗口大小变化
        self.installEventFilter(self)
    
    def _create_chart_card(self):
        """创建柱状图卡片"""
        # 创建卡片框架
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setMinimumHeight(400)  # 增加最小高度为原来的2倍
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许卡片在两个方向上扩展
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        # 卡片布局
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("TODO学习时长统计")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        # 创建柱状图
        self.todo_chart_view = self._create_todo_chart()
        card_layout.addWidget(self.todo_chart_view)
        
        return card
    
    def _create_info_card(self):
        """创建信息表格卡片"""
        # 创建卡片框架
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setMinimumHeight(400)  # 增加最小高度为原来的2倍
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许卡片在两个方向上扩展
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        # 卡片布局
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("详细时长信息")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        # 创建信息表格
        self.todo_info_table = QTableWidget(0, 2)
        self.todo_info_table.setHorizontalHeaderLabels(['事件', '时长(分钟)'])
        self.todo_info_table.horizontalHeader().setStretchLastSection(True)
        self.todo_info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.todo_info_table.setMinimumHeight(240)  # 增加表格最小高度
        self.todo_info_table.setAlternatingRowColors(True)
        self.todo_info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.todo_info_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.todo_info_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        card_layout.addWidget(self.todo_info_table)
        
        return card
    
    def _create_todo_chart(self):
        """创建TODO柱状图"""
        # 创建柱状图系列
        self.todo_bar_series = QBarSeries()
        self.todo_bar_set = QBarSet("学习时长(分钟)")
        self.todo_bar_series.append(self.todo_bar_set)
        
        # 创建图表
        chart = QChart()
        chart.addSeries(self.todo_bar_series)
        chart.setTitle("")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 创建X轴（TODO名称）
        self.todo_axis_x = QBarCategoryAxis()
        chart.addAxis(self.todo_axis_x, Qt.AlignBottom)
        self.todo_bar_series.attachAxis(self.todo_axis_x)
        
        # 创建Y轴（时长）
        self.todo_axis_y = QValueAxis()
        self.todo_axis_y.setLabelFormat("%.0f")
        self.todo_axis_y.setTitleText("时长(分钟)")
        self.todo_axis_y.setMin(0)
        chart.addAxis(self.todo_axis_y, Qt.AlignLeft)
        self.todo_bar_series.attachAxis(self.todo_axis_y)
        
        # 创建图表视图
        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(240)  # 增加图表最小高度
        chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许图表在两个方向上扩展
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        # 设置图表的边距
        chart.setMargins(QMargins(5, 5, 5, 5))
        
        return chart_view
    
    def _update_todo_stats_cards(self, target_date):
        """更新TODO统计卡片数据"""
        try:
            # 获取TODO学习统计数据
            todo_stats = self.database.get_todo_study_stats(target_date)
            
            if not todo_stats:
                self._clear_todo_stats_cards()
                return
            
            # 更新柱状图
            self.todo_bar_set.remove(0, self.todo_bar_set.count())  # 清空现有数据
            
            # 准备图表数据
            categories = []
            values = []
            max_value = 0
            
            for stat in todo_stats:
                todo_name = stat['todo_name']
                duration_minutes = stat['duration_minutes']
                
                # 限制TODO名称长度，避免X轴标签过长
                if len(todo_name) > 8:
                    display_name = todo_name[:8] + "..."
                else:
                    display_name = todo_name
                
                categories.append(display_name)
                values.append(duration_minutes)
                max_value = max(max_value, duration_minutes)
            
            # 设置X轴类别
            self.todo_axis_x.clear()
            self.todo_axis_x.append(categories)
            
            # 添加数据到柱状图
            for value in values:
                self.todo_bar_set.append(value)
            
            # 设置Y轴范围
            self.todo_axis_y.setMax(max(max_value * 1.1, 10))  # 最小显示10分钟
            
            # 更新信息表格
            self.todo_info_table.setRowCount(len(todo_stats))
            for i, stat in enumerate(todo_stats):
                self.todo_info_table.setItem(i, 0, QTableWidgetItem(stat['todo_name']))
                self.todo_info_table.setItem(i, 1, QTableWidgetItem(f"{stat['duration_minutes']:.1f}"))
            
            # 调整表格行高
            self.todo_info_table.resizeRowsToContents()
            
        except Exception as e:
            self.logger.error(f"更新TODO统计卡片失败: {e}")
            self._clear_todo_stats_cards()
    
    def _clear_todo_stats_cards(self):
        """清空TODO统计卡片数据"""
        try:
            # 清空柱状图
            if hasattr(self, 'todo_bar_set'):
                self.todo_bar_set.remove(0, self.todo_bar_set.count())
                self.todo_axis_x.clear()
                self.todo_axis_y.setMax(10)
            
            # 清空信息表格
            if hasattr(self, 'todo_info_table'):
                self.todo_info_table.setRowCount(0)
                
        except Exception as e:
            self.logger.error(f"清空TODO统计卡片失败: {e}")

    def _setup_styles(self):
        """设置样式"""
        # 设置图表样式
        self.chart_view.setRenderHint(QPainter.HighQualityAntialiasing)
        
        # 设置表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置日历样式
        self.calendar.setStyleSheet("""
            QCalendarWidget QToolButton {
                height: 30px;
                width: 100px;
                color: #333;
                font-size: 14px;
                icon-size: 24px, 24px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QCalendarWidget QMenu {
                width: 150px;
                left: 20px;
                color: #333;
                font-size: 14px;
                background-color: #fff;
                border: 1px solid #ccc;
            }
            QCalendarWidget QSpinBox {
                width: 100px;
                font-size: 14px;
                color: #333;
                background-color: #fff;
                selection-background-color: #4a86e8;
                selection-color: #fff;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 14px;
                color: #333;
                background-color: #fff;
                selection-background-color: #4a86e8;
                selection-color: #fff;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
        """)

    def _create_chart(self) -> QChartView:
        """创建折线图"""
        # 创建折线系列
        self.series = QLineSeries()
        self.series.setName("学习时间(小时)")
        
        # 创建图表
        chart = QChart()
        chart.addSeries(self.series)
        chart.setTitle("近7天学习时间趋势")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 创建X轴（日期）
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("MM-dd")
        self.axis_x.setTitleText("日期")
        chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)
        
        # 创建Y轴（小时）
        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("%.1f")
        self.axis_y.setTitleText("学习时间(小时)")
        self.axis_y.setMin(0)
        chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)
        
        # 创建图表视图
        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(200)  # 减小最小高度以适应小窗口
        chart_view.setMinimumWidth(300)   # 设置最小宽度
        
        # 设置图表的边距，在小窗口下减少边距
        chart.setMargins(QMargins(10, 10, 10, 10))
        
        return chart_view

    def _load_data(self):
        """加载数据"""
        try:
            # 获取最近7天数据
            end_date = date.today()
            start_date = end_date - timedelta(days=6)  # 7天包括今天
            
            # 获取每日统计数据
            stats = self.database.get_recent_stats(7)
            
            # 如果没有数据，创建空数据
            if not stats:
                self.logger.warning("没有找到统计数据")
                return
            
            # 准备图表数据
            self.series.clear()
            
            # 准备表格数据
            self.table.setRowCount(len(stats))
            
            # 设置X轴范围
            self.axis_x.setRange(
                QDate(start_date.year, start_date.month, start_date.day).startOfDay(),
                QDate(end_date.year, end_date.month, end_date.day).endOfDay()
            )
            
            # 最大学习时间（小时）
            max_hours = 0
            
            # 填充数据
            for i, stat in enumerate(stats):
                # 日期
                stat_date = datetime.strptime(stat['date'], '%Y-%m-%d').date()
                qt_date = QDate(stat_date.year, stat_date.month, stat_date.day)
                
                # 学习时间（秒）
                study_time = stat['total_study_time']
                
                # 添加到图表
                timestamp = qt_date.startOfDay().toMSecsSinceEpoch()
                hours = study_time / 3600.0
                self.series.append(timestamp, hours)
                
                # 更新最大值
                if hours > max_hours:
                    max_hours = hours
                
                # 添加到表格
                self.table.setItem(i, 0, QTableWidgetItem(stat_date.strftime('%Y-%m-%d')))
                self.table.setItem(i, 1, QTableWidgetItem(seconds_to_minutes_text(study_time)))
            
            # 设置Y轴范围（最大值上取整 + 0.5）
            self.axis_y.setMax(max(1, int(max_hours) + 1))
            
            # 更新日历数据
            self._update_calendar_data(stats)
            
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}")

    def _update_calendar_data(self, stats):
        """更新日历数据"""
        # 清除所有日期格式
        self.calendar.setDateTextFormat(QDate(), self.calendar.dateTextFormat(QDate()))
        
        # 设置日期格式
        for stat in stats:
            # 解析日期
            stat_date = datetime.strptime(stat['date'], '%Y-%m-%d').date()
            qt_date = QDate(stat_date.year, stat_date.month, stat_date.day)
            
            # 学习时间（秒）
            study_time = stat['total_study_time']
            
            # 根据学习时间设置颜色深浅
            if study_time > 0:
                # 计算颜色深浅（最大3小时）
                intensity = min(1.0, study_time / (3 * 3600))
                
                # 创建日期格式
                fmt = self.calendar.dateTextFormat(qt_date)
                color = QColor(100, 149, 237)  # 蓝色
                color.setAlphaF(0.2 + intensity * 0.8)  # 透明度从0.2到1.0
                
                # 设置背景色
                fmt.setBackground(color)
                
                # 应用格式
                self.calendar.setDateTextFormat(qt_date, fmt)

    def _on_date_clicked(self, date):
        """日期点击事件"""
        try:
            # 转换为Python日期
            py_date = date.toPyDate()
            self.current_selected_date = py_date  # 保存当前选中的日期
            
            # 获取该日期的统计数据
            stats = self.database.get_daily_stats(py_date, py_date)
            
            # 获取该日期的学习会话记录
            sessions = self.database.get_daily_sessions(py_date)
            
            # 更新会话记录表格
            self.sessions_table.setRowCount(len(sessions))
            for i, session in enumerate(sessions):
                # 设置表格内容
                self.sessions_table.setItem(i, 0, QTableWidgetItem(str(session['id'])))
                self.sessions_table.setItem(i, 1, QTableWidgetItem(session['start_time']))
                self.sessions_table.setItem(i, 2, QTableWidgetItem(session['end_time']))
                self.sessions_table.setItem(i, 3, QTableWidgetItem(str(session['duration_minutes'])))
                self.sessions_table.setItem(i, 4, QTableWidgetItem(session['notes'] or ""))
                
                # 添加关联的TODO内容
                todo_content = session.get('todo_content', "")
                if todo_content is None:
                    todo_content = ""
                self.sessions_table.setItem(i, 5, QTableWidgetItem(str(todo_content)))
                
                # 添加删除按钮
                from PyQt5.QtWidgets import QPushButton
                delete_btn = QPushButton("删除")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                # 使用闭包保存当前会话ID
                session_id = session['id']
                delete_btn.clicked.connect(lambda checked, sid=session_id: self._delete_session(sid))
                self.sessions_table.setCellWidget(i, 6, delete_btn)
            
            if stats and len(stats) > 0:
                stat = stats[0]
                study_time = stat['total_study_time']
                rest_time = stat['total_rest_time']
                session_count = stat['session_count']
                completion_rate = stat['completion_rate'] * 100  # 转为百分比
                
                # 更新详情标签
                details = f"日期: {py_date.strftime('%Y-%m-%d')}\n"
                details += f"学习时间: {seconds_to_hours_text(study_time)} 小时\n"
                details += f"休息时间: {seconds_to_minutes_text(rest_time)} 分钟\n"
                details += f"专注次数: {session_count} 次\n"
                details += f"完成率: {completion_rate:.1f}%"
                
                self.date_details.setText(details)
            else:
                self.date_details.setText(f"日期: {py_date.strftime('%Y-%m-%d')}\n没有学习记录")
            
            # 更新TODO统计卡片
            self._update_todo_stats_cards(py_date)
                
        except Exception as e:
            self.logger.error(f"获取日期详情失败: {e}")
            self.date_details.setText("获取数据失败")
            # 清空TODO统计卡片
            self._clear_todo_stats_cards()

    def update_settings(self):
        """更新设置"""
        self._load_data()
        
    def _add_study_record(self):
        """手动添加学习记录"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDateTimeEdit, QSpinBox, QLineEdit, QDialogButtonBox, QMessageBox
        from PyQt5.QtCore import QDateTime
        
        try:
            # 创建对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("添加学习记录")
            dialog.setMinimumWidth(400)
            
            # 创建表单布局
            layout = QFormLayout(dialog)
            
            # 开始时间
            start_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
            start_time_edit.setCalendarPopup(True)
            start_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            layout.addRow("开始时间:", start_time_edit)
            
            # 结束时间
            end_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
            end_time_edit.setCalendarPopup(True)
            end_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            layout.addRow("结束时间:", end_time_edit)
            
            # 计划时长（分钟）
            duration_spin = QSpinBox()
            duration_spin.setRange(1, 180)  # 1-180分钟
            duration_spin.setValue(25)  # 默认25分钟
            duration_spin.setSuffix(" 分钟")
            layout.addRow("计划时长:", duration_spin)
            
            # 备注
            notes_edit = QLineEdit()
            layout.addRow("备注:", notes_edit)
            
            # 获取当前日期的TODO列表
            session_date = self.current_selected_date or date.today()
            todo_items = self.database.get_todo_items(session_date.isoformat(), include_completed=True)
            
            # 添加TODO关联下拉框
            todo_combo = QComboBox()
            todo_combo.setStyleSheet("padding: 8px;")
            todo_combo.addItem("无关联", None)
            
            # 添加TODO项目到下拉框
            for todo in todo_items:
                todo_combo.addItem(todo['content'], todo['id'])
            
            layout.addRow("关联待办事项:", todo_combo)
            
            # 按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addRow(button_box)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取输入值
                start_time = start_time_edit.dateTime().toPyDateTime()
                end_time = end_time_edit.dateTime().toPyDateTime()
                planned_duration = duration_spin.value() * 60  # 转换为秒
                notes = notes_edit.text()
                
                # 验证时间
                if end_time <= start_time:
                    QMessageBox.warning(self, "时间错误", "结束时间必须晚于开始时间")
                    return
                
                # 计算实际时长
                actual_duration = int((end_time - start_time).total_seconds())
                
                # 获取选中的TODO ID
                todo_id = todo_combo.currentData()
                
                # 创建会话记录
                session_id = self.database.start_session("study", planned_duration, start_time, todo_id)
                
                # 结束会话 - 使用用户填写的结束时间
                self.database.end_session(session_id, True, notes, actual_duration, end_time)
                
                # 刷新数据
                if hasattr(self, 'current_selected_date') and self.current_selected_date is not None:
                    qt_date = QDate(self.current_selected_date.year, 
                                   self.current_selected_date.month, 
                                   self.current_selected_date.day)
                    self._on_date_clicked(qt_date)
                self._load_data()
                
                QMessageBox.information(self, "添加成功", "学习记录已成功添加")
        
        except Exception as e:
            self.logger.error(f"添加学习记录失败: {e}")
            QMessageBox.critical(self, "添加失败", f"添加学习记录失败: {str(e)}")
    
    def _delete_session(self, session_id):
        """删除学习会话"""
        from PyQt5.QtWidgets import QMessageBox
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            f'确定要删除会话 #{session_id} 吗？\n此操作不可恢复。',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 调用数据库删除方法
                self.database.delete_session(session_id)
                self.logger.info(f"已删除会话: ID={session_id}")
                
                # 刷新当前日期的数据
                if hasattr(self, 'current_selected_date') and self.current_selected_date is not None:
                    # 重新加载当前选中日期的数据
                    qt_date = QDate(self.current_selected_date.year, 
                                   self.current_selected_date.month, 
                                   self.current_selected_date.day)
                    self._on_date_clicked(qt_date)
                    
                # 刷新统计数据
                self._load_data()
                
                # 显示成功消息
                QMessageBox.information(self, "成功", "会话已成功删除")
                
            except Exception as e:
                self.logger.error(f"删除会话失败: {e}")
                QMessageBox.critical(self, "错误", f"删除会话失败: {str(e)}")
        
        
    def _on_session_cell_double_clicked(self, row, column):
        """双击单元格事件"""
        # 允许编辑备注列（第5列，索引为4）和关联待办列（第6列，索引为5）
        if column == 4:
            self._edit_session_note(row, column)
        elif column == 5:
            self._edit_session_todo(row, column)
    
    def _edit_session_note(self, row, column):
        """编辑会话备注"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox
        
        # 获取会话ID
        session_id_item = self.sessions_table.item(row, 0)
        if not session_id_item:
            return
            
        session_id = int(session_id_item.text())
        current_note = self.sessions_table.item(row, column).text()
        
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑备注")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明标签
        msg_label = QLabel(f"编辑会话 #{session_id} 的备注:")
        msg_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(msg_label)
        
        # 添加备注输入框
        note_input = QLineEdit(current_note)
        note_input.setPlaceholderText("记录这段时间做了什么...")
        note_input.setStyleSheet("padding: 8px;")
        layout.addWidget(note_input)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
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
        """)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取新备注内容
            new_note = note_input.text().strip()
            
            try:
                # 更新数据库
                self.database.update_session_notes(session_id, new_note)
                
                # 更新表格显示
                self.sessions_table.item(row, column).setText(new_note)
                
                self.logger.info(f"已更新会话备注: ID={session_id}, 备注={new_note}")
            except Exception as e:
                self.logger.error(f"更新会话备注失败: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"更新备注失败: {str(e)}")
                
    def _edit_session_todo(self, row, column):
        """编辑会话关联的TODO"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox
        
        # 获取会话ID
        session_id_item = self.sessions_table.item(row, 0)
        if not session_id_item:
            return
            
        session_id = int(session_id_item.text())
        
        # 获取会话日期（从开始时间列）
        start_time_text = self.sessions_table.item(row, 1).text()
        try:
            # 尝试解析完整的日期时间格式
            session_date = datetime.strptime(start_time_text, "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            try:
                # 如果只有时间，则使用当前选中的日期
                session_date = self.current_selected_date
            except AttributeError:
                # 如果没有当前选中的日期，则使用今天的日期
                session_date = date.today()
        
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑关联待办")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明标签
        msg_label = QLabel(f"为会话 #{session_id} 关联待办事项:")
        msg_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(msg_label)
        
        # 获取当前日期的TODO列表
        todo_items = self.database.get_todo_items(session_date.isoformat(), include_completed=True)
        
        # 添加TODO关联下拉框
        todo_combo = QComboBox()
        todo_combo.setStyleSheet("padding: 8px;")
        todo_combo.addItem("无关联", None)
        
        # 获取当前关联的TODO内容
        current_todo = self.sessions_table.item(row, column).text()
        
        # 添加TODO项目到下拉框
        selected_index = 0
        for i, todo in enumerate(todo_items):
            todo_combo.addItem(todo['content'], todo['id'])
            # 如果内容匹配，记录索引
            if todo['content'] == current_todo:
                selected_index = i + 1  # +1 因为第一项是"无关联"
        
        # 设置当前选中项
        todo_combo.setCurrentIndex(selected_index)
        
        layout.addWidget(todo_combo)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
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
        """)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取选中的TODO ID
            todo_id = todo_combo.currentData()
            
            try:
                # 使用数据库方法更新关联的TODO
                self.database.update_session_todo(session_id, todo_id)
                
                # 更新表格显示
                new_todo_content = todo_combo.currentText() if todo_id is not None else ""
                if new_todo_content == "无关联":
                    new_todo_content = ""
                self.sessions_table.item(row, column).setText(new_todo_content)
                
                self.logger.info(f"已更新会话关联TODO: ID={session_id}, TODO ID={todo_id}")
            except Exception as e:
                self.logger.error(f"更新会话关联TODO失败: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"更新关联待办失败: {str(e)}")
                
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理窗口大小变化"""
        if obj == self and event.type() == event.Resize:
            # 窗口大小变化时调整布局
            self._adjust_layout_based_on_width()
            return False  # 继续处理事件
        return super().eventFilter(obj, event)
    
    def _adjust_layout_based_on_width(self):
        """根据窗口宽度调整布局"""
        if not hasattr(self, 'cards_container') or not hasattr(self, 'chart_card') or not hasattr(self, 'info_card'):
            return
            
        # 获取当前窗口宽度
        current_width = self.width()
        
        # 根据宽度调整布局
        if current_width < 800:  # 窗口较窄时改为垂直布局
            if self.cards_container.direction() != QBoxLayout.TopToBottom:
                # 移除现有的组件
                self.cards_container.removeWidget(self.chart_card)
                self.cards_container.removeWidget(self.info_card)
                
                # 改变布局方向
                self.cards_container.setDirection(QBoxLayout.TopToBottom)
                
                # 重新添加组件
                self.cards_container.addWidget(self.chart_card)
                self.cards_container.addWidget(self.info_card)
                
                # 设置拉伸因子
                self.cards_container.setStretchFactor(self.chart_card, 1)
                self.cards_container.setStretchFactor(self.info_card, 1)
        else:  # 窗口较宽时改为水平布局
            if self.cards_container.direction() != QBoxLayout.LeftToRight:
                # 移除现有的组件
                self.cards_container.removeWidget(self.chart_card)
                self.cards_container.removeWidget(self.info_card)
                
                # 改变布局方向
                self.cards_container.setDirection(QBoxLayout.LeftToRight)
                
                # 重新添加组件
                self.cards_container.addWidget(self.chart_card)
                self.cards_container.addWidget(self.info_card)
                
                # 设置拉伸因子
                self.cards_container.setStretchFactor(self.chart_card, 3)
                self.cards_container.setStretchFactor(self.info_card, 2)