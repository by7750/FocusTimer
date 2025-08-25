#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出脚本
用于导出数据库中的所有数据
"""

import json
import os
import sys
from datetime import datetime
from config.database import Database


def export_data(export_file_path=None):
    """
    导出数据库中的所有数据
    
    Args:
        export_file_path: 导出文件路径，默认为data_export_YYYYMMDD_HHMMSS.json
    """
    if export_file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file_path = f"data_export_{timestamp}.json"
    
    # 确保导出目录存在
    export_dir = os.path.dirname(export_file_path)
    if export_dir and not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    
    # 初始化数据库
    db = Database()
    
    try:
        # 导出数据
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "study_sessions": [],
            "todo_items": [],
            "daily_stats": [],
            "timer_type_stats": []
        }
        
        # 获取数据库连接
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # 导出学习会话数据
        cursor.execute('''
            SELECT id, date, start_time, end_time, timer_type, planned_duration, 
                   actual_duration, completed, notes, todo_id, todo_content, created_at
            FROM study_sessions
            ORDER BY date DESC, start_time DESC
        ''')
        study_sessions = cursor.fetchall()
        export_data["study_sessions"] = [dict(row) for row in study_sessions]
        
        # 导出TODO项目数据
        cursor.execute('''
            SELECT id, content, date, completed, created_at, completed_at, priority
            FROM todo_items
            ORDER BY date DESC, priority DESC, created_at DESC
        ''')
        todo_items = cursor.fetchall()
        export_data["todo_items"] = [dict(row) for row in todo_items]
        
        # 导出每日统计数据
        cursor.execute('''
            SELECT id, date, total_study_time, total_rest_time, session_count, 
                   completion_rate, updated_at
            FROM daily_stats
            ORDER BY date DESC
        ''')
        daily_stats = cursor.fetchall()
        export_data["daily_stats"] = [dict(row) for row in daily_stats]
        
        # 导出计时器类型统计数据
        cursor.execute('''
            SELECT id, timer_type, date, usage_count, total_time
            FROM timer_type_stats
            ORDER BY date DESC, timer_type
        ''')
        timer_type_stats = cursor.fetchall()
        export_data["timer_type_stats"] = [dict(row) for row in timer_type_stats]
        
        # 将数据写入文件
        with open(export_file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"数据导出成功！共导出:")
        print(f"  - 学习会话: {len(export_data['study_sessions'])} 条")
        print(f"  - TODO项目: {len(export_data['todo_items'])} 条")
        print(f"  - 每日统计: {len(export_data['daily_stats'])} 条")
        print(f"  - 计时器统计: {len(export_data['timer_type_stats'])} 条")
        print(f"导出文件: {export_file_path}")
        
        return True
        
    except Exception as e:
        print(f"数据导出失败: {e}")
        return False
    finally:
        # 关闭数据库连接
        if db:
            db.close()


def main():
    """主函数"""
    # 解析命令行参数
    export_file_path = None
    if len(sys.argv) > 1:
        export_file_path = sys.argv[1]
    
    success = export_data(export_file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()