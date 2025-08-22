# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt


def seconds_to_minutes_text(seconds: int) -> str:
    m = round(max(0, int(seconds)) / 60.0, 1)
    return f"{m}"


class StatsWindow(QWidget):
    """统计窗口（简版）：展示最近 7 天学习时间（分钟）"""

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.setWindowTitle('统计')
        self.database = database
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel('最近 7 天学习时间（分钟）')
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['日期', '学习时长(分钟)'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.label)
        layout.addWidget(self.table)

    def _load(self):
        data = self.database.get_last_n_days(7, mode='学习')
        self.table.setRowCount(len(data))
        total = 0
        for i, (date, seconds) in enumerate(data.items()):
            total += int(seconds)
            self.table.setItem(i, 0, QTableWidgetItem(date))
            self.table.setItem(i, 1, QTableWidgetItem(seconds_to_minutes_text(seconds)))
        self.label.setText(f'最近 7 天学习时间（分钟） - 总计 {seconds_to_minutes_text(total)} 分钟')