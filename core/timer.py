#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计时器核心模块
负责计时器的核心逻辑和状态管理
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from enum import Enum
from datetime import datetime
import logging
from typing import Optional


class TimerState(Enum):
    """计时器状态枚举"""
    IDLE = "idle"  # 空闲状态
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    FINISHED = "finished"  # 完成


class FocusTimer(QObject):
    """专注计时器类"""

    # 信号定义
    state_changed = pyqtSignal(TimerState)  # 状态变化信号
    time_updated = pyqtSignal(int, int)  # 时间更新信号 (剩余时间, 总时间)
    timer_finished = pyqtSignal(str, int, bool)  # 计时完成信号 (类型, 实际时长, 是否完成)
    progress_updated = pyqtSignal(float)  # 进度更新信号 (0.0-1.0)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)

        # 计时器状态
        self._state = TimerState.IDLE
        self._timer_type = ""
        self._total_duration = 0  # 总时长(秒)
        self._remaining_time = 0  # 剩余时间(秒)
        self._elapsed_time = 0  # 已用时间(秒)

        # 会话信息
        self._session_id = None
        self._start_time = None
        self._pause_time = None
        self._total_pause_duration = 0  # 总暂停时长

        # Qt定时器
        self._qt_timer = QTimer()
        self._qt_timer.timeout.connect(self._on_timer_tick)
        self._qt_timer.setInterval(1000)  # 1秒间隔

        self.logger.info("计时器核心初始化完成")

    @property
    def state(self) -> TimerState:
        """获取当前状态"""
        return self._state

    @property
    def timer_type(self) -> str:
        """获取计时器类型"""
        return self._timer_type

    @property
    def total_duration(self) -> int:
        """获取总时长"""
        return self._total_duration

    @property
    def remaining_time(self) -> int:
        """获取剩余时间"""
        return self._remaining_time

    @property
    def elapsed_time(self) -> int:
        """获取已用时间"""
        return self._elapsed_time

    @property
    def progress(self) -> float:
        """获取进度(0.0-1.0)"""
        if self._total_duration == 0:
            return 0.0
        return self._elapsed_time / self._total_duration

    @property
    def session_id(self) -> Optional[int]:
        """获取会话ID"""
        return self._session_id

    def is_running(self) -> bool:
        """是否正在运行"""
        return self._state == TimerState.RUNNING

    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._state == TimerState.PAUSED

    def is_idle(self) -> bool:
        """是否空闲"""
        return self._state == TimerState.IDLE

    def is_finished(self) -> bool:
        """是否完成"""
        return self._state == TimerState.FINISHED

    def start(self, timer_type: str, duration: int, session_id: Optional[int] = None):
        """
        开始计时

        Args:
            timer_type: 计时器类型
            duration: 持续时间(秒)
            session_id: 数据库会话ID
        """
        if self._state in [TimerState.RUNNING, TimerState.PAUSED]:
            self.logger.warning("计时器已在运行或暂停状态，无法重新开始")
            return False

        self._timer_type = timer_type
        self._total_duration = duration
        self._remaining_time = duration
        self._elapsed_time = 0
        self._session_id = session_id
        self._start_time = datetime.now()
        self._pause_time = None
        self._total_pause_duration = 0

        self._set_state(TimerState.RUNNING)
        self._qt_timer.start()

        # 发送初始信号
        self._emit_time_signals()

        self.logger.info(f"计时器开始: 类型={timer_type}, 时长={duration}秒, 会话ID={session_id}")
        return True

    def pause(self):
        """暂停计时"""
        if self._state != TimerState.RUNNING:
            self.logger.warning("计时器未在运行状态，无法暂停")
            return False

        self._qt_timer.stop()
        self._pause_time = datetime.now()
        self._set_state(TimerState.PAUSED)

        self.logger.info("计时器已暂停")
        return True

    def resume(self):
        """恢复计时"""
        if self._state != TimerState.PAUSED:
            self.logger.warning("计时器未在暂停状态，无法恢复")
            return False

        if self._pause_time:
            # 累加暂停时长
            pause_duration = (datetime.now() - self._pause_time).total_seconds()
            self._total_pause_duration += pause_duration
            self._pause_time = None

        self._qt_timer.start()
        self._set_state(TimerState.RUNNING)

        self.logger.info("计时器已恢复")
        return True

    def stop(self, completed: bool = False):
        """
        停止计时

        Args:
            completed: 是否完成（True表示正常完成，False表示提前停止）
        """
        if self._state == TimerState.IDLE:
            self.logger.warning("计时器未在运行状态，无法停止")
            return False

        self._qt_timer.stop()

        # 计算实际用时
        actual_duration = self._elapsed_time
        if self._state == TimerState.PAUSED and self._pause_time:
            # 如果在暂停状态停止，需要加上最后一次暂停的时长
            pause_duration = (datetime.now() - self._pause_time).total_seconds()
            self._total_pause_duration += pause_duration

        self._set_state(TimerState.FINISHED if completed else TimerState.IDLE)

        # 发送完成信号
        self.timer_finished.emit(self._timer_type, actual_duration, completed)

        self.logger.info(f"计时器停止: 类型={self._timer_type}, 实际时长={actual_duration}秒, "
                         f"完成={completed}, 暂停时长={self._total_pause_duration}秒")

        # 重置状态
        if not completed:
            self._reset_state()

        return True

    def reset(self):
        """重置计时器"""
        self._qt_timer.stop()
        self._reset_state()
        self._set_state(TimerState.IDLE)

        self.logger.info("计时器已重置")

    def add_time(self, seconds: int):
        """
        添加时间

        Args:
            seconds: 要添加的秒数（可以为负数）
        """
        if self._state not in [TimerState.RUNNING, TimerState.PAUSED]:
            return False

        new_remaining = max(0, self._remaining_time + seconds)
        time_diff = new_remaining - self._remaining_time

        self._remaining_time = new_remaining
        self._total_duration += time_diff
        self._elapsed_time = self._total_duration - self._remaining_time

        self._emit_time_signals()

        self.logger.info(f"调整时间: {'+' if seconds >= 0 else ''}{seconds}秒, "
                         f"剩余时间: {self._remaining_time}秒")
        return True

    def get_time_info(self) -> dict:
        """获取时间信息"""
        return {
            'state': self._state,
            'timer_type': self._timer_type,
            'total_duration': self._total_duration,
            'remaining_time': self._remaining_time,
            'elapsed_time': self._elapsed_time,
            'progress': self.progress,
            'session_id': self._session_id,
            'start_time': self._start_time,
            'total_pause_duration': self._total_pause_duration
        }

    def _on_timer_tick(self):
        """定时器滴答事件"""
        if self._state != TimerState.RUNNING:
            return

        self._remaining_time -= 1
        self._elapsed_time += 1

        # 发送更新信号
        self._emit_time_signals()

        # 检查是否完成
        if self._remaining_time <= 0:
            self.stop(completed=True)

    def _emit_time_signals(self):
        """发送时间相关信号"""
        self.time_updated.emit(self._remaining_time, self._total_duration)
        self.progress_updated.emit(self.progress)

    def _set_state(self, new_state: TimerState):
        """设置状态"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.state_changed.emit(new_state)
            self.logger.debug(f"状态变化: {old_state} -> {new_state}")

    def _reset_state(self):
        """重置状态"""
        self._timer_type = ""
        self._total_duration = 0
        self._remaining_time = 0
        self._elapsed_time = 0
        self._session_id = None
        self._start_time = None
        self._pause_time = None
        self._total_pause_duration = 0

    def format_time(self, seconds: int, show_seconds: bool = True) -> str:
        """
        格式化时间显示

        Args:
            seconds: 秒数
            show_seconds: 是否显示秒数

        Returns:
            格式化的时间字符串
        """
        if seconds < 0:
            seconds = 0

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            if show_seconds:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{hours:02d}:{minutes:02d}"
        else:
            if show_seconds:
                return f"{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}分钟"

    def get_formatted_remaining_time(self, show_seconds: bool = True) -> str:
        """获取格式化的剩余时间"""
        return self.format_time(self._remaining_time, show_seconds)

    def get_formatted_elapsed_time(self, show_seconds: bool = True) -> str:
        """获取格式化的已用时间"""
        return self.format_time(self._elapsed_time, show_seconds)


class TimerManager(QObject):
    """计时器管理器"""

    # 信号定义
    timer_started = pyqtSignal(str, int)  # 计时器开始 (类型, 时长)
    timer_paused = pyqtSignal()  # 计时器暂停
    timer_resumed = pyqtSignal()  # 计时器恢复
    timer_stopped = pyqtSignal(bool)  # 计时器停止 (是否完成)
    timer_finished = pyqtSignal(str, int)  # 计时器完成 (类型, 实际时长)

    def __init__(self, database=None, parent=None):
        super().__init__(parent)

        self.database = database
        self.logger = logging.getLogger(__name__)

        # 核心计时器
        self.timer = FocusTimer(self)

        # 连接信号
        self._connect_signals()

        self.logger.info("计时器管理器初始化完成")

    def _connect_signals(self):
        """连接信号"""
        self.timer.state_changed.connect(self._on_state_changed)
        self.timer.timer_finished.connect(self._on_timer_finished)

    def start_timer(self, timer_type: str, duration: int) -> bool:
        """
        开始计时器

        Args:
            timer_type: 计时器类型
            duration: 持续时间(秒)

        Returns:
            是否成功开始
        """
        session_id = None

        # 如果有数据库，创建会话记录
        if self.database:
            try:
                session_id = self.database.start_session(timer_type, duration)
            except Exception as e:
                self.logger.error(f"创建数据库会话失败: {e}")

        # 开始计时器
        if self.timer.start(timer_type, duration, session_id):
            self.timer_started.emit(timer_type, duration)
            return True

        return False

    def pause_timer(self) -> bool:
        """暂停计时器"""
        if self.timer.pause():
            self.timer_paused.emit()
            return True
        return False

    def resume_timer(self) -> bool:
        """恢复计时器"""
        if self.timer.resume():
            self.timer_resumed.emit()
            return True
        return False

    def stop_timer(self, completed: bool = False) -> bool:
        """停止计时器"""
        if self.timer.stop(completed):
            self.timer_stopped.emit(completed)
            return True
        return False

    def get_timer(self) -> FocusTimer:
        """获取计时器实例"""
        return self.timer

    def _on_state_changed(self, new_state: TimerState):
        """状态变化处理"""
        self.logger.debug(f"计时器状态变化: {new_state}")

    def _on_timer_finished(self, timer_type: str, actual_duration: int, completed: bool):
        """计时器完成处理"""
        # 更新数据库
        if self.database and self.timer.session_id:
            try:
                self.database.end_session(
                    self.timer.session_id,
                    completed=completed,
                    notes=""
                )
            except Exception as e:
                self.logger.error(f"更新数据库会话失败: {e}")

        # 发送完成信号
        if completed:
            self.timer_finished.emit(timer_type, actual_duration)