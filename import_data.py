#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入脚本
用于从导出的JSON文件中恢复数据
"""

import json
import sys
import os
from datetime import datetime
from config.database import Database


def import_data(import_file_path):
    """
    从JSON文件导入数据到数据库
    
    Args:
        import_file_path: 导入文件路径
    """
    if not os.path.exists(import_file_path):
        print(f"错误: 导入文件不存在: {import_file_path}")
        return False
    
    # 初始化数据库
    db = Database()
    
    try:
        # 读取导出的数据
        with open(import_file_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"正在从 {import_file_path} 导入数据...")
        print(f"导出时间: {export_data.get('export_timestamp', '未知')}")
        
        # 获取数据库连接
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # 清空现有数据（可选，根据需求决定是否需要）
            # 注意：这里我们不会清空数据，而是直接插入，让数据库处理重复ID的情况
            
            # 导入TODO项目数据
            todo_count = 0
            for todo_item in export_data.get("todo_items", []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO todo_items 
                        (id, content, date, completed, created_at, completed_at, priority)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        todo_item["id"],
                        todo_item["content"],
                        todo_item["date"],
                        todo_item["completed"],
                        todo_item["created_at"],
                        todo_item.get("completed_at"),
                        todo_item["priority"]
                    ))
                    todo_count += 1
                except Exception as e:
                    print(f"导入TODO项目失败 (ID: {todo_item['id']}): {e}")
            
            # 导入学习会话数据
            session_count = 0
            for session in export_data.get("study_sessions", []):
                try:
                    # 检查会话是否已存在
                    existing_session = cursor.execute(
                        'SELECT id FROM study_sessions WHERE id = ?', 
                        (session["id"],)
                    ).fetchone()
                    
                    if existing_session:
                        # 更新现有会话
                        cursor.execute('''
                            UPDATE study_sessions SET
                            date = ?,
                            start_time = ?,
                            end_time = ?,
                            timer_type = ?,
                            planned_duration = ?,
                            actual_duration = ?,
                            completed = ?,
                            notes = ?,
                            todo_id = ?,
                            todo_content = ?,
                            created_at = ?
                            WHERE id = ?
                        ''', (
                            session["date"],
                            session["start_time"],
                            session.get("end_time"),
                            session.get("timer_type", "study"),
                            session.get("planned_duration"),
                            session.get("actual_duration"),
                            bool(session.get("completed", True)),
                            session.get("notes", ""),
                            session.get("todo_id"),
                            session.get("todo_content", ""),
                            session.get("created_at"),
                            session["id"]
                        ))
                    else:
                        # 使用add_session_direct方法导入新会话数据
                        db.add_session_direct(
                            date_str=session["date"],
                            start_time=session["start_time"],
                            end_time=session.get("end_time"),
                            duration_minutes=session["actual_duration"]/60 if session["actual_duration"] else 0,
                            notes=session.get("notes", ""),
                            todo_id=session.get("todo_id"),
                            timer_type=session.get("timer_type", "study"),
                            planned_duration=session.get("planned_duration"),
                            actual_duration=session.get("actual_duration"),
                            completed=bool(session.get("completed", True)),
                            todo_content=session.get("todo_content", ""),
                            id=session["id"]
                        )
                    session_count += 1
                except Exception as e:
                    print(f"导入学习会话失败 (ID: {session['id']}): {e}")
            
            # 导入每日统计数据
            stats_count = 0
            for stat in export_data.get("daily_stats", []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_stats 
                        (id, date, total_study_time, total_rest_time, session_count, completion_rate, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        stat["id"],
                        stat["date"],
                        stat["total_study_time"],
                        stat["total_rest_time"],
                        stat["session_count"],
                        stat["completion_rate"],
                        stat["updated_at"]
                    ))
                    stats_count += 1
                except Exception as e:
                    print(f"导入每日统计数据失败 (ID: {stat['id']}): {e}")
            
            # 导入计时器类型统计数据
            timer_stats_count = 0
            for stat in export_data.get("timer_type_stats", []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO timer_type_stats 
                        (id, timer_type, date, usage_count, total_time)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        stat["id"],
                        stat["timer_type"],
                        stat["date"],
                        stat["usage_count"],
                        stat["total_time"]
                    ))
                    timer_stats_count += 1
                except Exception as e:
                    print(f"导入计时器类型统计数据失败 (ID: {stat['id']}): {e}")
            
            # 提交事务
            conn.commit()
            
            print(f"数据导入成功！共导入:")
            print(f"  - TODO项目: {todo_count} 条")
            print(f"  - 学习会话: {session_count} 条")
            print(f"  - 每日统计: {stats_count} 条")
            print(f"  - 计时器统计: {timer_stats_count} 条")
            
            return True
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            print(f"数据导入过程中发生错误，已回滚: {e}")
            return False
            
    except Exception as e:
        print(f"数据导入失败: {e}")
        return False
    finally:
        # 关闭数据库连接
        if db:
            db.close()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python import_data.py <导出的JSON文件路径>")
        sys.exit(1)
    
    import_file_path = sys.argv[1]
    success = import_data(import_file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()