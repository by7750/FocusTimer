#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL数据导出脚本
用于导出数据库中的所有数据为SQL格式
"""

import os
import sys
from datetime import datetime
from config.database import Database


def export_sql(export_file_path=None):
    """
    导出数据库中的所有数据为SQL格式
    
    Args:
        export_file_path: 导出文件路径，默认为data_export_YYYYMMDD_HHMMSS.sql
    """
    if export_file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file_path = f"data_export_{timestamp}.sql"
    
    # 确保导出目录存在
    export_dir = os.path.dirname(export_file_path)
    if export_dir and not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    
    # 初始化数据库
    db = Database()
    
    try:
        # 打开文件准备写入
        with open(export_file_path, 'w', encoding='utf-8') as f:
            # 写入SQL文件头部信息
            f.write("-- 数据导出SQL脚本\n")
            f.write(f"-- 导出时间: {datetime.now().isoformat()}\n")
            f.write("-- 该脚本可用于恢复数据\n\n")
            
            # 获取数据库连接
            conn = db._get_connection()
            cursor = conn.cursor()
            
            # 导出表结构
            f.write("-- 表结构定义\n")
            f.write("DROP TABLE IF EXISTS study_sessions;\n")
            f.write("""CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    timer_type TEXT NOT NULL,
    planned_duration INTEGER NOT NULL,
    actual_duration INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    todo_id INTEGER,
    todo_content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);\n""")
            f.write("\n")
            
            f.write("DROP TABLE IF EXISTS daily_stats;\n")
            f.write("""CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    total_study_time INTEGER DEFAULT 0,
    total_rest_time INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);\n""")
            f.write("\n")
            
            f.write("DROP TABLE IF EXISTS timer_type_stats;\n")
            f.write("""CREATE TABLE timer_type_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timer_type TEXT NOT NULL,
    date DATE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    total_time INTEGER DEFAULT 0,
    UNIQUE(timer_type, date)
);\n""")
            f.write("\n")
            
            f.write("DROP TABLE IF EXISTS todo_items;\n")
            f.write("""CREATE TABLE todo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    priority INTEGER DEFAULT 0
);\n""")
            f.write("\n")
            
            # 导出学习会话数据
            f.write("-- 学习会话数据\n")
            f.write("DELETE FROM study_sessions;\n")
            cursor.execute('''
                SELECT id, date, start_time, end_time, timer_type, planned_duration, 
                       actual_duration, completed, notes, todo_id, todo_content, created_at
                FROM study_sessions
                ORDER BY date DESC, start_time DESC
            ''')
            study_sessions = cursor.fetchall()
            for session in study_sessions:
                # 处理None值
                values = []
                for value in session:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                f.write(f"INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, planned_duration, actual_duration, completed, notes, todo_id, todo_content, created_at) VALUES ({', '.join(values)});\n")
            f.write(f"-- 共导出 {len(study_sessions)} 条学习会话记录\n\n")
            
            # 导出TODO项目数据
            f.write("-- TODO项目数据\n")
            f.write("DELETE FROM todo_items;\n")
            cursor.execute('''
                SELECT id, content, date, completed, created_at, completed_at, priority
                FROM todo_items
                ORDER BY date DESC, priority DESC, created_at DESC
            ''')
            todo_items = cursor.fetchall()
            for todo in todo_items:
                # 处理None值
                values = []
                for value in todo:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                f.write(f"INSERT INTO todo_items (id, content, date, completed, created_at, completed_at, priority) VALUES ({', '.join(values)});\n")
            f.write(f"-- 共导出 {len(todo_items)} 条TODO项目记录\n\n")
            
            # 导出每日统计数据
            f.write("-- 每日统计数据\n")
            f.write("DELETE FROM daily_stats;\n")
            cursor.execute('''
                SELECT id, date, total_study_time, total_rest_time, session_count, 
                       completion_rate, updated_at
                FROM daily_stats
                ORDER BY date DESC
            ''')
            daily_stats = cursor.fetchall()
            for stat in daily_stats:
                # 处理None值
                values = []
                for value in stat:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                f.write(f"INSERT INTO daily_stats (id, date, total_study_time, total_rest_time, session_count, completion_rate, updated_at) VALUES ({', '.join(values)});\n")
            f.write(f"-- 共导出 {len(daily_stats)} 条每日统计记录\n\n")
            
            # 导出计时器类型统计数据
            f.write("-- 计时器类型统计数据\n")
            f.write("DELETE FROM timer_type_stats;\n")
            cursor.execute('''
                SELECT id, timer_type, date, usage_count, total_time
                FROM timer_type_stats
                ORDER BY date DESC, timer_type
            ''')
            timer_type_stats = cursor.fetchall()
            for stat in timer_type_stats:
                # 处理None值
                values = []
                for value in stat:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                f.write(f"INSERT INTO timer_type_stats (id, timer_type, date, usage_count, total_time) VALUES ({', '.join(values)});\n")
            f.write(f"-- 共导出 {len(timer_type_stats)} 条计时器类型统计记录\n\n")
        
        print(f"SQL数据导出成功！")
        print(f"导出文件: {export_file_path}")
        print(f"导出记录:")
        print(f"  - 学习会话: {len(study_sessions)} 条")
        print(f"  - TODO项目: {len(todo_items)} 条")
        print(f"  - 每日统计: {len(daily_stats)} 条")
        print(f"  - 计时器统计: {len(timer_type_stats)} 条")
        
        return True
        
    except Exception as e:
        print(f"SQL数据导出失败: {e}")
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
    
    success = export_sql(export_file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()