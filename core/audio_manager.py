#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频管理模块
负责音频播放功能
"""

import os
import logging
import threading
from typing import Optional

# 尝试导入不同的音频库，根据可用性选择
try:
    import pygame
    AUDIO_BACKEND = "pygame"
except ImportError:
    try:
        import winsound
        AUDIO_BACKEND = "winsound"
    except ImportError:
        AUDIO_BACKEND = "none"


class AudioManager:
    """音频管理类"""

    def __init__(self):
        """初始化音频管理器"""
        self.logger = logging.getLogger(__name__)
        self.is_playing = False
        self.stop_event = threading.Event()
        
        # 尝试初始化pygame音频（即使当前后端不是pygame）
        try:
            import pygame
            pygame.mixer.init()
            self.pygame_available = True
            self.logger.info("pygame音频初始化成功")
        except (ImportError, Exception) as e:
            self.pygame_available = False
            self.logger.warning(f"pygame音频初始化失败: {e}")
            
        self.logger.info(f"使用音频后端: {AUDIO_BACKEND}")
    
    def play_sound(self, sound_file: str, loop: bool = False) -> bool:
        """播放音频文件
        
        Args:
            sound_file: 音频文件路径
            loop: 是否循环播放
            
        Returns:
            是否成功开始播放
        """
        if not sound_file or not os.path.exists(sound_file):
            self.logger.warning(f"音频文件不存在: {sound_file}")
            return False
            
        # 停止当前播放的音频
        self.stop_sound()
        
        try:
            if AUDIO_BACKEND == "pygame":
                return self._play_with_pygame(sound_file, loop)
            elif AUDIO_BACKEND == "winsound":
                return self._play_with_winsound(sound_file, loop)
            else:
                self.logger.warning("没有可用的音频后端")
                return False
        except Exception as e:
            self.logger.error(f"播放音频失败: {e}")
            return False
    
    def _play_with_pygame(self, sound_file: str, loop: bool) -> bool:
        """使用pygame播放音频"""
        try:
            pygame.mixer.music.load(sound_file)
            loop_count = -1 if loop else 0  # -1表示无限循环
            pygame.mixer.music.play(loop_count)
            self.is_playing = True
            return True
        except Exception as e:
            self.logger.error(f"pygame播放失败: {e}")
            return False
    
    def _play_with_winsound(self, sound_file: str, loop: bool) -> bool:
        """使用winsound播放音频"""
        try:
            # winsound不支持后台播放，创建线程播放
            self.stop_event.clear()
            self.is_playing = True
            
            def play_thread():
                try:
                    # winsound只支持wav格式
                    if sound_file.lower().endswith('.wav'):
                        while not self.stop_event.is_set():
                            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                            if not loop or self.stop_event.is_set():
                                break
                    else:
                        # 非wav格式，尝试使用pygame播放
                        if self.pygame_available:
                            try:
                                import pygame
                                pygame.mixer.music.load(sound_file)
                                loop_count = -1 if loop else 0  # -1表示无限循环
                                pygame.mixer.music.play(loop_count)
                                self.logger.info(f"使用pygame播放非wav文件: {sound_file}")
                                
                                # 等待停止信号或播放结束
                                while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                                    import time
                                    time.sleep(0.5)  # 每0.5秒检查一次
                                    
                                # 如果收到停止信号，停止pygame播放
                                if self.stop_event.is_set() and pygame.mixer.music.get_busy():
                                    pygame.mixer.music.stop()
                                    
                                return  # 播放完成或被停止，退出线程
                            except Exception as e:
                                self.logger.error(f"使用pygame播放非wav文件失败: {e}")
                                # 如果pygame播放失败，尝试使用系统提示音
                                winsound.MessageBeep()
                        else:
                            # pygame不可用，使用系统提示音
                            self.logger.warning(f"无法播放非wav文件: {sound_file}，pygame不可用")
                            winsound.MessageBeep()
                except Exception as e:
                    self.logger.error(f"winsound播放线程错误: {e}")
                finally:
                    self.is_playing = False
            
            threading.Thread(target=play_thread, daemon=True).start()
            return True
        except Exception as e:
            self.logger.error(f"winsound播放失败: {e}")
            self.is_playing = False
            return False
    
    def stop_sound(self):
        """停止当前播放的音频"""
        if not self.is_playing:
            return
            
        try:
            # 停止pygame音乐播放（如果可用）
            if self.pygame_available:
                try:
                    import pygame
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                        self.logger.info("pygame音频播放已停止")
                except (ImportError, AttributeError) as e:
                    self.logger.error(f"停止pygame音频失败: {e}")
            
            # 停止winsound播放
            if AUDIO_BACKEND == "winsound":
                self.stop_event.set()
                self.logger.info("winsound音频播放已停止")
                
            self.is_playing = False
            self.logger.info("音频播放已停止")
        except Exception as e:
            self.logger.error(f"停止音频失败: {e}")
    
    def is_sound_playing(self) -> bool:
        """检查是否正在播放音频"""
        # 如果pygame可用，优先检查pygame播放状态
        if self.pygame_available:
            try:
                import pygame
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    return True
            except (ImportError, AttributeError):
                pass
                
        # 否则返回内部状态
        return self.is_playing
    
    def pause_sound(self):
        """暂停当前播放的音频"""
        if not self.is_playing:
            return
            
        try:
            # 暂停pygame音乐播放（如果可用）
            if self.pygame_available:
                try:
                    import pygame
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                        self.logger.info("pygame音频播放已暂停")
                        return  # 成功暂停，直接返回
                except (ImportError, AttributeError) as e:
                    self.logger.error(f"暂停pygame音频失败: {e}")
            
            # 对于winsound或其他后端，使用停止功能
            self.stop_sound()
            self.logger.info("音频播放已暂停")
        except Exception as e:
            self.logger.error(f"暂停音频失败: {e}")
    
    def unpause_sound(self):
        """恢复暂停的音频播放"""
        if not self.is_playing:
            return
            
        try:
            # 恢复pygame音乐播放（如果可用）
            if self.pygame_available:
                try:
                    import pygame
                    if pygame.mixer.get_init():
                        pygame.mixer.music.unpause()
                        self.logger.info("pygame音频播放已恢复")
                        return  # 成功恢复，直接返回
                except (ImportError, AttributeError) as e:
                    self.logger.error(f"恢复pygame音频失败: {e}")
            
            # 对于winsound或其他后端，可能需要重新开始播放
            # 这里我们简单地记录日志，因为winsound不支持真正的暂停/恢复
            self.logger.info("音频播放已恢复")
        except Exception as e:
            self.logger.error(f"恢复音频失败: {e}")