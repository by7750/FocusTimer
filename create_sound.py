#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认提示音脚本
"""

import os
import wave
import struct
import math

# 确保目录存在
sound_dir = "resources/sounds"
os.makedirs(sound_dir, exist_ok=True)

# 提示音路径
sound_path = os.path.join(sound_dir, "default_alarm.wav")

# 如果提示音不存在，创建一个
if not os.path.exists(sound_path):
    # 创建一个简单的提示音
    # 参数
    sample_rate = 44100  # 采样率
    duration = 1.0       # 持续时间（秒）
    frequency = 440.0    # 频率（赫兹）
    volume = 0.5         # 音量（0.0-1.0）
    
    # 创建WAV文件
    with wave.open(sound_path, 'w') as wav_file:
        # 设置参数
        wav_file.setparams((1, 2, sample_rate, int(sample_rate * duration), 'NONE', 'not compressed'))
        
        # 生成音频数据
        values = []
        for i in range(int(sample_rate * duration)):
            # 生成正弦波
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            # 打包为二进制数据
            packed_value = struct.pack('h', value)
            values.append(packed_value)
        
        # 写入WAV文件
        value_str = b''.join(values)
        wav_file.writeframes(value_str)
    
    print(f"创建默认提示音: {sound_path}")
else:
    print(f"提示音已存在: {sound_path}")

print("提示音创建完成！")