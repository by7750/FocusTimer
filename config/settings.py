#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理模块
负责应用程序配置的加载、保存和管理
"""

import json
import os
from typing import Dict, Any, List
import logging


class Settings:
    """设置管理类"""

    def __init__(self, config_file: str = "data/settings.json"):
        """
        初始化设置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._settings = {}
        self._default_settings = self._get_default_settings()
        self.load()

    def _get_default_settings(self) -> Dict[str, Any]:
        """获取默认设置"""
        return {
            # 应用程序基本设置
            "app": {
                "language": "zh_CN",
                "theme": "light",
                "auto_start": False,
                "minimize_to_tray": True,
                "window_size": [800, 600],
                "window_position": None  # None表示居中显示
            },

            # 计时器设置
            "timer": {
                "types": [
                    {
                        "id": "study",
                        "name": "学习",
                        "duration": 45 * 60,  # 45分钟，以秒为单位
                        "color": "#4CAF50",
                        "icon": "study"
                    },
                    {
                        "id": "rest",
                        "name": "休息",
                        "duration": 15 * 60,  # 15分钟
                        "color": "#2196F3",
                        "icon": "rest"
                    }
                ],
                "current_type": "study",
                "auto_switch": False,  # 是否自动切换（学习->休息->学习）
                "auto_start_next": False  # 是否自动开始下一个计时
            },

            # 提醒设置
            "notification": {
                "sound_enabled": True,
                "sound_file": "resources/sounds/default_alarm.wav",
                "sound_volume": 0.8,
                "popup_enabled": True,
                "popup_duration": 10,  # 弹窗显示时长（秒）
                "desktop_notification": True
            },

            # 统计设置
            "statistics": {
                "data_retention_days": 365,  # 数据保留天数
                "backup_enabled": True,
                "backup_interval": 7,  # 备份间隔（天）
                "export_format": "json"
            },

            # 界面设置
            "ui": {
                "show_seconds": True,  # 是否显示秒数
                "progress_style": "circle",  # circle 或 linear
                "animation_enabled": True,
                "font_size": 12,
                "opacity": 1.0,
                "background_image": "",  # 背景图片路径
                "background_mode": "stretch"  # 背景图片显示模式: stretch, fit, tile
            }
        }

    def load(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)

                # 合并默认设置和加载的设置
                self._settings = self._merge_settings(self._default_settings, loaded_settings)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                # 使用默认设置
                self._settings = self._default_settings.copy()
                self.save()  # 创建默认配置文件
                self.logger.info("使用默认配置，已创建配置文件")

        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            self._settings = self._default_settings.copy()

    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)

            self.logger.info("配置文件保存成功")

        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")

    def _merge_settings(self, default: Dict, loaded: Dict) -> Dict:
        """
        合并默认设置和加载的设置

        Args:
            default: 默认设置
            loaded: 加载的设置

        Returns:
            合并后的设置
        """
        result = default.copy()

        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_settings(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def get(self, key: str, default=None):
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键（如 'app.language'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._settings

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        target = self._settings

        # 导航到最后一级的父字典
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # 设置值
        target[keys[-1]] = value

    def get_timer_types(self) -> List[Dict]:
        """获取计时器类型列表"""
        return self.get('timer.types', [])

    def get_timer_type_by_id(self, type_id: str) -> Dict:
        """根据ID获取计时器类型"""
        types = self.get_timer_types()
        for timer_type in types:
            if timer_type.get('id') == type_id:
                return timer_type
        return {}

    def add_timer_type(self, timer_type: Dict):
        """添加新的计时器类型"""
        types = self.get_timer_types()

        # 检查ID是否已存在
        existing_ids = [t.get('id') for t in types]
        if timer_type.get('id') in existing_ids:
            raise ValueError(f"计时器类型ID '{timer_type.get('id')}' 已存在")

        types.append(timer_type)
        self.set('timer.types', types)

    def update_timer_type(self, type_id: str, updates: Dict):
        """更新计时器类型"""
        types = self.get_timer_types()

        for i, timer_type in enumerate(types):
            if timer_type.get('id') == type_id:
                types[i].update(updates)
                self.set('timer.types', types)
                return True

        return False

    def remove_timer_type(self, type_id: str):
        """删除计时器类型"""
        types = self.get_timer_types()

        # 不能删除默认的学习和休息类型
        if type_id in ['study', 'rest']:
            raise ValueError("不能删除默认的计时器类型")

        types = [t for t in types if t.get('id') != type_id]
        self.set('timer.types', types)

        # 如果当前选中的类型被删除，切换到学习模式
        if self.get('timer.current_type') == type_id:
            self.set('timer.current_type', 'study')

    def get_current_timer_type(self) -> Dict:
        """获取当前选中的计时器类型"""
        current_id = self.get('timer.current_type', 'study')
        return self.get_timer_type_by_id(current_id)

    def set_current_timer_type(self, type_id: str):
        """设置当前计时器类型"""
        if self.get_timer_type_by_id(type_id):
            self.set('timer.current_type', type_id)
        else:
            raise ValueError(f"计时器类型 '{type_id}' 不存在")

    def reset_to_defaults(self):
        """重置为默认设置"""
        self._settings = self._default_settings.copy()
        self.save()
        self.logger.info("设置已重置为默认值")


# 全局设置实例（单例模式）
_settings_instance = None


def get_settings() -> Settings:
    """获取设置实例（单例模式）"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance