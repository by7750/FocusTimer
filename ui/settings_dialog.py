# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QSpinBox, QPushButton,
    QLineEdit, QFileDialog, QCheckBox, QMessageBox
)
from typing import Dict


class SettingsDialog(QDialog):
    """设置对话框：模式时间、提醒音乐与弹窗"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.settings = settings
        self.setMinimumWidth(420)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 模式与时间
        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(1, 24 * 60)
        form.addRow(QLabel('模式'), self.mode_combo)
        form.addRow(QLabel('时间 (分钟)'), self.minutes_spin)
        layout.addLayout(form)

        # 模式操作
        btn_row = QHBoxLayout()
        self.btn_add_update = QPushButton('添加/更新')
        self.btn_remove = QPushButton('删除当前')
        btn_row.addWidget(self.btn_add_update)
        btn_row.addWidget(self.btn_remove)
        layout.addLayout(btn_row)

        # 提醒设置
        form2 = QFormLayout()
        self.music_edit = QLineEdit()
        self.btn_browse = QPushButton('选择音乐')
        music_row = QHBoxLayout()
        music_row.addWidget(self.music_edit)
        music_row.addWidget(self.btn_browse)
        form2.addRow(QLabel('提醒音乐'), music_row)
        self.popup_check = QCheckBox('倒计时结束时弹出提醒窗口')
        form2.addRow(self.popup_check)
        layout.addLayout(form2)

        # 底部
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_ok = QPushButton('确定')
        self.btn_cancel = QPushButton('取消')
        bottom.addWidget(self.btn_ok)
        bottom.addWidget(self.btn_cancel)
        layout.addLayout(bottom)

        # 连接信号
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.btn_add_update.clicked.connect(self._on_add_update)
        self.btn_remove.clicked.connect(self._on_remove)
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _load(self):
        modes: Dict[str, int] = self.settings.get_modes()
        self.mode_combo.clear()
        self.mode_combo.addItems(modes.keys())
        self.mode_combo.setCurrentText(self.settings.get_selected_mode())
        self.minutes_spin.setValue(max(1, modes.get(self.mode_combo.currentText(), 60) // 60))
        self.music_edit.setText(self.settings.get_music_path())
        self.popup_check.setChecked(self.settings.get_show_popup())

    def _on_mode_changed(self, text: str):
        seconds = self.settings.get_modes().get(text, 60)
        self.minutes_spin.setValue(max(1, int(seconds) // 60))

    def _on_add_update(self):
        name = self.mode_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, '提示', '模式名称不能为空')
            return
        minutes = self.minutes_spin.value()
        self.settings.set_mode_seconds(name, minutes * 60)
        self._load()
        QMessageBox.information(self, '成功', f'模式 "{name}" 已设置为 {minutes} 分钟')

    def _on_remove(self):
        name = self.mode_combo.currentText().strip()
        if not name:
            return
        if len(self.settings.get_modes()) <= 1:
            QMessageBox.warning(self, '提示', '至少保留一个模式')
            return
        self.settings.remove_mode(name)
        self._load()

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择音乐文件', '', '音频文件 (*.mp3 *.wav *.ogg);;所有文件 (*.*)')
        if path:
            self.music_edit.setText(path)
            self.settings.set_music_path(path)

    def accept(self):
        # 保存其他设置
        self.settings.set_selected_mode(self.mode_combo.currentText())
        self.settings.set_show_popup(self.popup_check.isChecked())
        super().accept()