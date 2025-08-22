#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认图标脚本
"""

import os
from PIL import Image, ImageDraw

# 确保目录存在
icon_dir = "resources/icons"
os.makedirs(icon_dir, exist_ok=True)

# 图标路径
icon_path = os.path.join(icon_dir, "icon.png")

# 如果图标不存在，创建一个
if not os.path.exists(icon_path):
    # 创建一个256x256的图像，绿色背景
    img = Image.new('RGBA', (256, 256), color=(39, 174, 96, 255))
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的时钟图案
    # 外圆
    draw.ellipse((20, 20, 236, 236), outline=(255, 255, 255, 255), width=10)
    
    # 时钟中心点
    center = (128, 128)
    
    # 时针
    draw.line((center[0], center[1], center[0], center[1]-68), fill=(255, 255, 255, 255), width=8)
    
    # 分针
    draw.line((center[0], center[1], center[0]+52, center[1]), fill=(255, 255, 255, 255), width=8)
    
    # 保存图标
    img.save(icon_path)
    print(f"创建默认图标: {icon_path}")
else:
    print(f"图标已存在: {icon_path}")

# 创建ICO格式图标
ico_path = os.path.join(icon_dir, "app_icon.ico")
if not os.path.exists(ico_path):
    try:
        # 打开PNG图标
        img = Image.open(icon_path)
        
        # 保存为ICO格式
        img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"创建ICO图标: {ico_path}")
    except Exception as e:
        print(f"创建ICO图标失败: {e}")
else:
    print(f"ICO图标已存在: {ico_path}")

print("图标创建完成！")