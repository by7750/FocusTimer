#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
负责学习数据的存储和统计
"""

import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import logging


class Database:
    """数据库管理类"""

    def __init__(self, db_file: str = "data/focus_timer.db"):
        """
        初始化数据库

        Args:
            db_file: 数据库文件路径
        """
        self.db_file = db_file
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self._ensure_database_exists()
        self._initialize_database()

    def _ensure_database_exists(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.connection is None or self._is_connection_closed():
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问
        return self.connection

    def _is_connection_closed(self) -> bool:
        """检查连接是否已关闭"""
        try:
            self.connection.execute("SELECT 1")
            return False
        except:
            return True

    def _initialize_database(self):
        """初始化数据库表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 创建学习记录表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS study_sessions
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               date
                               DATE
                               NOT
                               NULL,
                               start_time
                               DATETIME
                               NOT
                               NULL,
                               end_time
                               DATETIME,
                               timer_type
                               TEXT
                               NOT
                               NULL,
                               planned_duration
                               INTEGER
                               NOT
                               NULL,
                               actual_duration
                               INTEGER,
                               completed
                               BOOLEAN
                               DEFAULT
                               FALSE,
                               notes
                               TEXT,
                               todo_id
                               INTEGER,
                               todo_content
                               TEXT,
                               created_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # 创建每日统计表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS daily_stats
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               date
                               DATE
                               UNIQUE
                               NOT
                               NULL,
                               total_study_time
                               INTEGER
                               DEFAULT
                               0,
                               total_rest_time
                               INTEGER
                               DEFAULT
                               0,
                               session_count
                               INTEGER
                               DEFAULT
                               0,
                               completion_rate
                               REAL
                               DEFAULT
                               0.0,
                               updated_at
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # 创建计时器类型使用统计表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS timer_type_stats
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               timer_type
                               TEXT
                               NOT
                               NULL,
                               date
                               DATE
                               NOT
                               NULL,
                               usage_count
                               INTEGER
                               DEFAULT
                               0,
                               total_time
                               INTEGER
                               DEFAULT
                               0,
                               UNIQUE
                           (
                               timer_type,
                               date
                           )
                               )
                           ''')

            # 创建TODO列表表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS todo_items
                           (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               content TEXT NOT NULL,
                               date DATE NOT NULL,
                               completed BOOLEAN DEFAULT FALSE,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               completed_at DATETIME,
                               priority INTEGER DEFAULT 0
                           )
                           ''')
            
            # 创建索引提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_sessions_date ON study_sessions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_sessions_timer_type ON study_sessions(timer_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timer_type_stats_date ON timer_type_stats(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_todo_items_date ON todo_items(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_todo_items_completed ON todo_items(completed)')

            conn.commit()
            self.logger.info("数据库初始化完成")

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
            
    def add_todo_item(self, content: str, date_str: str = None, priority: int = 0) -> int:
        """
        添加一个新的TODO项目
        
        Args:
            content: 项目内容
            date_str: 日期字符串，格式为YYYY-MM-DD，默认为今天
            priority: 优先级，数字越大优先级越高
            
        Returns:
            新添加的TODO项目ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 如果没有提供日期，则使用今天的日期
            if date_str is None:
                todo_date = date.today()
            else:
                todo_date = date.fromisoformat(date_str)
                
            cursor.execute('''
                INSERT INTO todo_items (content, date, priority, created_at)
                VALUES (?, ?, ?, ?)
            ''', (content, todo_date, priority, datetime.now()))
            
            todo_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"添加TODO项目: ID={todo_id}, 内容={content}, 日期={todo_date}")
            return todo_id
            
        except Exception as e:
            self.logger.error(f"添加TODO项目失败: {e}")
            raise
            
    def get_todo_items(self, date_str: str = None, include_completed: bool = False) -> List[Dict]:
        """
        获取指定日期的TODO项目列表
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD，默认为今天
            include_completed: 是否包含已完成的项目
            
        Returns:
            TODO项目列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 如果没有提供日期，则使用今天的日期
            if date_str is None:
                todo_date = date.today()
            else:
                todo_date = date.fromisoformat(date_str)
                
            # 构建查询条件
            conditions = ["date = ?"]
            params = [todo_date]
            
            if not include_completed:
                conditions.append("completed = 0")
                
            where_clause = " AND ".join(conditions)
            
            cursor.execute(f'''
                SELECT id, content, date, completed, created_at, completed_at, priority
                FROM todo_items
                WHERE {where_clause}
                ORDER BY priority DESC, created_at ASC
            ''', params)
            
            results = cursor.fetchall()
            todo_items = [dict(row) for row in results]
            return todo_items
            
        except Exception as e:
            self.logger.error(f"获取TODO项目失败: {e}")
            return []
            
    def update_todo_item(self, todo_id: int, content: str = None, completed: bool = None, 
                         priority: int = None) -> bool:
        """
        更新TODO项目
        
        Args:
            todo_id: TODO项目ID
            content: 新的内容，如果为None则不更新
            completed: 是否完成，如果为None则不更新
            priority: 新的优先级，如果为None则不更新
            
        Returns:
            更新是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            params = []
            
            if content is not None:
                update_fields.append("content = ?")
                params.append(content)
                
            if completed is not None:
                update_fields.append("completed = ?")
                params.append(1 if completed else 0)
                
                # 如果标记为完成，记录完成时间
                if completed:
                    update_fields.append("completed_at = ?")
                    params.append(datetime.now())
                else:
                    update_fields.append("completed_at = NULL")
                    
            if priority is not None:
                update_fields.append("priority = ?")
                params.append(priority)
                
            if not update_fields:
                return True  # 没有需要更新的字段
                
            # 构建SQL语句
            set_clause = ", ".join(update_fields)
            params.append(todo_id)
            
            cursor.execute(f'''
                UPDATE todo_items
                SET {set_clause}
                WHERE id = ?
            ''', params)
            
            conn.commit()
            self.logger.info(f"更新TODO项目: ID={todo_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新TODO项目失败: {e}")
            return False
            
    def delete_todo_item(self, todo_id: int) -> bool:
        """
        删除TODO项目
        
        Args:
            todo_id: TODO项目ID
            
        Returns:
            删除是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM todo_items WHERE id = ?', (todo_id,))
            conn.commit()
            
            self.logger.info(f"删除TODO项目: ID={todo_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除TODO项目失败: {e}")
            return False

    def start_session(self, timer_type: str, planned_duration: int, start_time: datetime = None, todo_id: int = None) -> int:
        """
        开始一个新的学习会话

        Args:
            timer_type: 计时器类型
            planned_duration: 计划持续时间（秒）
            start_time: 会话开始时间，如果不提供则使用当前时间
            todo_id: 关联的TODO项目ID

        Returns:
            会话ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 如果没有提供开始时间，则使用当前时间
            if start_time is None:
                start_time = datetime.now()
            
            today = start_time.date()

            # 检查表中是否存在todo_id字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 获取待办内容（如果有）
            todo_content = ""
            if todo_id:
                cursor.execute('SELECT content FROM todo_items WHERE id = ?', (todo_id,))
                result = cursor.fetchone()
                if result:
                    todo_content = result['content']
            
            # 检查是否存在todo_content字段
            has_todo_content = 'todo_content' in columns
            
            if 'todo_id' in columns and has_todo_content:
                cursor.execute('''
                               INSERT INTO study_sessions (date, start_time, timer_type, planned_duration, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ''', (today, start_time, timer_type, planned_duration, todo_id, todo_content))
            elif 'todo_id' in columns and not has_todo_content:
                # 添加todo_content字段
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_content TEXT')
                cursor.execute('''
                               INSERT INTO study_sessions (date, start_time, timer_type, planned_duration, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ''', (today, start_time, timer_type, planned_duration, todo_id, todo_content))
            elif not 'todo_id' in columns:
                # 添加todo_id和todo_content字段
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_id INTEGER')
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_content TEXT')
                cursor.execute('''
                               INSERT INTO study_sessions (date, start_time, timer_type, planned_duration, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ''', (today, start_time, timer_type, planned_duration, todo_id, todo_content))

            session_id = cursor.lastrowid
            conn.commit()

            self.logger.info(f"开始新会话: ID={session_id}, 类型={timer_type}, 时长={planned_duration}秒, 开始时间={start_time}, 关联TODO={todo_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            raise

    def end_session(self, session_id: int, completed: bool = True, notes: str = "", actual_duration: int = None, end_time: datetime = None):
        """
        结束学习会话

        Args:
            session_id: 会话ID
            completed: 是否完成
            notes: 备注
            actual_duration: 实际学习时长（秒），如果提供则使用此值，否则计算开始和结束时间的差值
            end_time: 结束时间，如果不提供则使用当前时间
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 获取会话开始时间
            cursor.execute('SELECT start_time FROM study_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()

            if not result:
                raise ValueError(f"会话ID {session_id} 不存在")

            start_time = datetime.fromisoformat(result['start_time'])
            
            # 如果没有提供结束时间，则使用当前时间
            if end_time is None:
                end_time = datetime.now()
            
            # 如果提供了实际学习时长，则使用此值，否则计算开始和结束时间的差值
            if actual_duration is None:
                actual_duration = int((end_time - start_time).total_seconds())

            # 更新会话记录
            cursor.execute('''
                           UPDATE study_sessions
                           SET end_time        = ?,
                               actual_duration = ?,
                               completed       = ?,
                               notes           = ?
                           WHERE id = ?
                           ''', (end_time, actual_duration, completed, notes, session_id))

            conn.commit()

            # 更新统计数据
            self._update_daily_stats(start_time.date())

            self.logger.info(f"结束会话: ID={session_id}, 实际时长={actual_duration}秒, 完成={completed}")

        except Exception as e:
            self.logger.error(f"结束会话失败: {e}")
            raise
            
    def update_session_notes(self, session_id: int, notes: str):
        """
        更新会话备注

        Args:
            session_id: 会话ID
            notes: 备注内容
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 更新会话备注
            cursor.execute('''
                           UPDATE study_sessions
                           SET notes = ?
                           WHERE id = ?
                           ''', (notes, session_id))

            conn.commit()
            self.logger.info(f"更新会话备注: ID={session_id}, 备注={notes}")
            return True

        except Exception as e:
            self.logger.error(f"更新会话备注失败: {e}")
            raise
            
    def update_session_todo(self, session_id: int, todo_id: int = None):
        """
        更新会话关联的TODO项目

        Args:
            session_id: 会话ID
            todo_id: 关联的TODO项目ID，如果为None则取消关联
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 获取待办内容（如果有）
            todo_content = ""
            if todo_id:
                cursor.execute('SELECT content FROM todo_items WHERE id = ?', (todo_id,))
                result = cursor.fetchone()
                if result:
                    todo_content = result['content']

            # 更新会话关联的TODO和TODO内容
            cursor.execute('''
                           UPDATE study_sessions
                           SET todo_id = ?, todo_content = ?
                           WHERE id = ?
                           ''', (todo_id, todo_content, session_id))

            conn.commit()
            self.logger.info(f"更新会话关联TODO: ID={session_id}, TODO ID={todo_id}, TODO内容={todo_content}")
            return True

        except Exception as e:
            self.logger.error(f"更新会话关联TODO失败: {e}")
            raise
            
    def delete_session(self, session_id: int):
        """
        删除学习会话记录

        Args:
            session_id: 会话ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取会话信息，用于更新统计数据
            cursor.execute('SELECT date FROM study_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"会话ID {session_id} 不存在")
                
            session_date = result['date']
            
            # 删除会话记录
            cursor.execute('DELETE FROM study_sessions WHERE id = ?', (session_id,))
            
            conn.commit()
            
            # 更新统计数据
            self._update_daily_stats(date.fromisoformat(session_date))
            
            self.logger.info(f"删除会话: ID={session_id}, 日期={session_date}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除会话失败: {e}")
            raise
    
    def add_session_direct(self, date_str: str, start_time: str, end_time: str, 
                          duration_minutes: float, notes: str = "", todo_id: int = None, 
                          timer_type: str = "study", planned_duration: int = None, 
                          actual_duration: int = None, completed: bool = True, 
                          todo_content: str = "", id: int = None) -> int:
        """
        直接添加学习会话记录（用于数据导入）
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)
            start_time: 开始时间字符串
            end_time: 结束时间字符串
            duration_minutes: 持续时间（分钟）
            notes: 备注
            todo_id: 关联的TODO项目ID
            timer_type: 计时器类型
            planned_duration: 计划时长（秒）
            actual_duration: 实际时长（秒）
            completed: 是否完成
            todo_content: 待办内容
            id: 会话ID
            
        Returns:
            会话ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 转换时间格式
            session_date = date.fromisoformat(date_str)
            
            # 解析开始和结束时间
            if len(start_time.split()) == 1:  # 只有时间部分
                start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M:%S")
            else:  # 完整的日期时间
                start_datetime = datetime.fromisoformat(start_time)
                
            if end_time:
                if len(end_time.split()) == 1:  # 只有时间部分
                    end_datetime = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M:%S")
                else:  # 完整的日期时间
                    end_datetime = datetime.fromisoformat(end_time)
            else:
                end_datetime = None
            
            # 转换持续时间为秒
            if actual_duration is None:
                actual_duration = int(duration_minutes * 60)
            if planned_duration is None:
                planned_duration = actual_duration  # 假设计划时长等于实际时长
            
            # 获取待办内容（如果有）
            if todo_id and not todo_content:
                cursor.execute('SELECT content FROM todo_items WHERE id = ?', (todo_id,))
                result = cursor.fetchone()
                if result:
                    todo_content = result['content']
            
            # 检查表中是否存在todo_id字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 检查是否存在todo_content字段
            has_todo_content = 'todo_content' in columns
            
            if 'todo_id' in columns and has_todo_content:
                cursor.execute('''
                               INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, 
                                                          planned_duration, actual_duration, completed, 
                                                          notes, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (id, session_date, start_datetime, end_datetime, timer_type,
                                   planned_duration, actual_duration, completed, notes, todo_id, todo_content))
            elif 'todo_id' in columns and not has_todo_content:
                # 添加todo_content字段
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_content TEXT')
                cursor.execute('''
                               INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, 
                                                          planned_duration, actual_duration, completed, 
                                                          notes, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (id, session_date, start_datetime, end_datetime, timer_type,
                                   planned_duration, actual_duration, completed, notes, todo_id, todo_content))
            elif not 'todo_id' in columns:
                # 添加todo_id和todo_content字段
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_id INTEGER')
                cursor.execute('ALTER TABLE study_sessions ADD COLUMN todo_content TEXT')
                cursor.execute('''
                               INSERT INTO study_sessions (id, date, start_time, end_time, timer_type, 
                                                          planned_duration, actual_duration, completed, 
                                                          notes, todo_id, todo_content)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (id, session_date, start_datetime, end_datetime, timer_type,
                                   planned_duration, actual_duration, completed, notes, todo_id, todo_content))
            
            session_id = cursor.lastrowid
            conn.commit()
            
            # 更新统计数据
            self._update_daily_stats(session_date)
            
            self.logger.info(f"直接添加会话记录: ID={session_id}, 日期={date_str}, 时长={duration_minutes}分钟")
            return session_id
            
        except Exception as e:
            self.logger.error(f"直接添加会话记录失败: {e}")
            raise
    
    def get_daily_sessions(self, target_date: date = None) -> List[Dict]:
        """
        获取指定日期的学习会话记录

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            会话记录列表
        """
        try:
            if target_date is None:
                target_date = date.today()
                
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查表中是否存在todo_id字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            self.logger.debug(f"study_sessions表字段: {columns}")
            
            if 'todo_id' in columns:
                # 检查表中是否存在todo_content字段
                has_todo_content = 'todo_content' in columns
                
                if has_todo_content:
                    # 直接使用表中的todo_content字段，不再通过连表查询
                    cursor.execute('''
                                   SELECT id, date, start_time, end_time, timer_type, 
                                          planned_duration, actual_duration, completed, notes, todo_id, todo_content
                                   FROM study_sessions
                                   WHERE date = ? AND timer_type = 'study'
                                   ORDER BY start_time DESC
                                   ''', (target_date,))
                else:
                    # 如果没有todo_content字段，则通过连表查询获取
                    cursor.execute('''
                                   SELECT s.id, s.date, s.start_time, s.end_time, s.timer_type, 
                                          s.planned_duration, s.actual_duration, s.completed, s.notes, s.todo_id,
                                          t.content as todo_content
                                   FROM study_sessions s
                                   LEFT JOIN todo_items t ON s.todo_id = t.id
                                   WHERE s.date = ? AND s.timer_type = 'study'
                                   ORDER BY s.start_time DESC
                                   ''', (target_date,))
            else:
                cursor.execute('''
                               SELECT id, date, start_time, end_time, timer_type, 
                                      planned_duration, actual_duration, completed, notes
                               FROM study_sessions
                               WHERE date = ? AND timer_type = 'study'
                               ORDER BY start_time DESC
                               ''', (target_date,))

            results = cursor.fetchall()
            self.logger.debug(f"查询到{len(results)}条会话记录")
            sessions = []

            for row in results:
                # 格式化时间
                start_time = datetime.fromisoformat(row['start_time']).strftime('%H:%M:%S')
                end_time = datetime.fromisoformat(row['end_time']).strftime('%H:%M:%S') if row['end_time'] else ''
                
                # 计算持续时间（分钟）
                duration_minutes = round(row['actual_duration'] / 60, 1) if row['actual_duration'] else 0
                
                session = {
                    'id': row['id'],
                    'date': row['date'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                    'completed': bool(row['completed']),
                    'notes': row['notes'] or ''
                }
                
                # 添加TODO相关信息（无论是否存在）
                if 'todo_id' in columns:
                    # 将Row对象转换为字典以便正确访问字段
                    row_dict = dict(row)
                    session['todo_id'] = row_dict.get('todo_id')
                    session['todo_content'] = row_dict.get('todo_content', '')
                
                sessions.append(session)

            self.logger.debug(f"返回{len(sessions)}条会话记录")
            return sessions

        except Exception as e:
            self.logger.error(f"获取日期会话记录失败: {e}")
            return []
            
    def _update_daily_stats(self, target_date: date):
        """更新每日统计数据"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 计算当日统计数据
            cursor.execute('''
                           SELECT timer_type,
                                  COUNT(*)                                                 as session_count,
                                  SUM(CASE WHEN completed THEN actual_duration ELSE 0 END) as completed_time,
                                  SUM(actual_duration)                                     as total_time,
                                  AVG(CASE WHEN completed THEN 1.0 ELSE 0.0 END)           as completion_rate
                           FROM study_sessions
                           WHERE date = ? AND actual_duration IS NOT NULL
                           GROUP BY timer_type
                           ''', (target_date,))

            type_stats = cursor.fetchall()

            total_study_time = 0
            total_rest_time = 0
            total_sessions = 0
            total_completion_rate = 0

            for stat in type_stats:
                timer_type = stat['timer_type']
                completed_time = stat['completed_time'] or 0
                session_count = stat['session_count']
                completion_rate = stat['completion_rate'] or 0

                if timer_type == 'study':
                    total_study_time += completed_time
                elif timer_type == 'rest':
                    total_rest_time += completed_time

                total_sessions += session_count
                total_completion_rate += completion_rate

                # 更新计时器类型统计
                cursor.execute('''
                    INSERT OR REPLACE INTO timer_type_stats 
                    (timer_type, date, usage_count, total_time)
                    VALUES (?, ?, ?, ?)
                ''', (timer_type, target_date, session_count, completed_time))

            # 计算平均完成率
            avg_completion_rate = total_completion_rate / len(type_stats) if type_stats else 0

            # 更新或插入每日统计
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats 
                (date, total_study_time, total_rest_time, session_count, completion_rate, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (target_date, total_study_time, total_rest_time, total_sessions,
                  avg_completion_rate, datetime.now()))

            conn.commit()

        except Exception as e:
            self.logger.error(f"更新每日统计失败: {e}")

    def get_daily_stats(self, start_date: date, end_date: date) -> List[Dict]:
        """
        获取指定日期范围的每日统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            统计数据列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT *
                           FROM daily_stats
                           WHERE date BETWEEN ? AND ?
                           ORDER BY date
                           ''', (start_date, end_date))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取每日统计失败: {e}")
            return []

    def get_recent_stats(self, days: int = 7) -> List[Dict]:
        """
        获取最近N天的统计数据

        Args:
            days: 天数

        Returns:
            统计数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.get_daily_stats(start_date, end_date)

    def get_all_sessions(self) -> List[Dict]:
        """
        获取所有学习会话记录

        Returns:
            所有会话记录列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查表中是否存在todo_id和todo_content字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            has_todo_id = 'todo_id' in columns
            has_todo_content = 'todo_content' in columns

            # 构建查询语句，确保包含所有字段
            if has_todo_id and has_todo_content:
                cursor.execute('''
                    SELECT * FROM study_sessions 
                    ORDER BY start_time DESC
                ''')
            elif has_todo_id and not has_todo_content:
                # 如果有todo_id但没有todo_content，通过连表查询获取
                cursor.execute('''
                    SELECT s.*, t.content as todo_content FROM study_sessions s
                    LEFT JOIN todo_items t ON s.todo_id = t.id
                    ORDER BY s.start_time DESC
                ''')
            else:
                # 如果没有todo_id字段，直接查询所有字段
                cursor.execute('''
                    SELECT * FROM study_sessions 
                    ORDER BY start_time DESC
                ''')

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取所有会话记录失败: {e}")
            return []
    
    def get_session_history(self, start_date: date = None, end_date: date = None,
                            timer_type: str = None, limit: int = 100) -> List[Dict]:
        """
        获取会话历史记录

        Args:
            start_date: 开始日期
            end_date: 结束日期
            timer_type: 计时器类型过滤
            limit: 最大记录数

        Returns:
            会话记录列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查表中是否存在todo_id字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            has_todo_id = 'todo_id' in columns

            conditions = []
            params = []

            if start_date:
                conditions.append('s.date >= ?')
                params.append(start_date)

            if end_date:
                conditions.append('s.date <= ?')
                params.append(end_date)

            if timer_type:
                conditions.append('s.timer_type = ?')
                params.append(timer_type)

            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            params.append(limit)

            # 检查表中是否存在todo_content字段
            has_todo_content = 'todo_content' in columns
            
            if has_todo_id:
                if has_todo_content:
                    # 直接使用表中的todo_content字段，不再通过连表查询
                    cursor.execute(f'''
                        SELECT * FROM study_sessions
                        WHERE {where_clause.replace('s.', '')}
                        ORDER BY start_time DESC
                        LIMIT ?
                    ''', params)
                else:
                    # 如果没有todo_content字段，则通过连表查询获取
                    cursor.execute(f'''
                        SELECT s.*, t.content as todo_content FROM study_sessions s
                        LEFT JOIN todo_items t ON s.todo_id = t.id
                        WHERE {where_clause}
                        ORDER BY s.start_time DESC
                        LIMIT ?
                    ''', params)
            else:
                cursor.execute(f'''
                    SELECT * FROM study_sessions 
                    WHERE {where_clause}
                    ORDER BY start_time DESC
                    LIMIT ?
                ''', params)

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取会话历史失败: {e}")
            return []

    def get_timer_type_stats(self, days: int = 30) -> Dict[str, Dict]:
        """
        获取计时器类型使用统计

        Args:
            days: 统计天数

        Returns:
            计时器类型统计字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)

            cursor.execute('''
                           SELECT timer_type,
                                  SUM(usage_count) as total_usage,
                                  SUM(total_time)  as total_time,
                                  AVG(usage_count) as avg_daily_usage
                           FROM timer_type_stats
                           WHERE date BETWEEN ? AND ?
                           GROUP BY timer_type
                           ''', (start_date, end_date))

            results = cursor.fetchall()
            stats = {}

            for row in results:
                stats[row['timer_type']] = {
                    'total_usage': row['total_usage'] or 0,
                    'total_time': row['total_time'] or 0,
                    'avg_daily_usage': row['avg_daily_usage'] or 0
                }

            return stats

        except Exception as e:
            self.logger.error(f"获取计时器类型统计失败: {e}")
            return {}

    def get_completion_rate_trend(self, days: int = 30) -> List[Tuple[date, float]]:
        """
        获取完成率趋势

        Args:
            days: 天数

        Returns:
            (日期, 完成率) 元组列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)

            cursor.execute('''
                           SELECT date, completion_rate
                           FROM daily_stats
                           WHERE date BETWEEN ? AND ?
                           ORDER BY date
                           ''', (start_date, end_date))

            results = cursor.fetchall()
            return [(date.fromisoformat(row['date']), row['completion_rate'])
                    for row in results]

        except Exception as e:
            self.logger.error(f"获取完成率趋势失败: {e}")
            return []

    def get_total_study_time(self, start_date: date = None, end_date: date = None) -> int:
        """
        获取总学习时间

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            总学习时间（秒）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            conditions = ["timer_type = 'study'", "completed = 1"]
            params = []

            if start_date:
                conditions.append('date >= ?')
                params.append(start_date)

            if end_date:
                conditions.append('date <= ?')
                params.append(end_date)

            where_clause = ' AND '.join(conditions)

            cursor.execute(f'''
                SELECT SUM(actual_duration) as total_time
                FROM study_sessions 
                WHERE {where_clause}
            ''', params)

            result = cursor.fetchone()
            return result['total_time'] or 0

        except Exception as e:
            self.logger.error(f"获取总学习时间失败: {e}")
            return 0

    def get_todo_study_stats(self, target_date: date = None) -> List[Dict]:
        """
        获取指定日期各个TODO的学习时长统计
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            TODO学习统计列表，包含todo_content和total_duration
        """
        try:
            if target_date is None:
                target_date = date.today()
                
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查表中是否存在todo_content字段
            cursor.execute("PRAGMA table_info(study_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            has_todo_content = 'todo_content' in columns
            has_todo_id = 'todo_id' in columns
            
            if has_todo_content:
                # 直接使用todo_content字段统计
                cursor.execute('''
                    SELECT 
                        COALESCE(todo_content, '未分类') as todo_name,
                        SUM(CASE WHEN completed THEN actual_duration ELSE 0 END) as total_duration
                    FROM study_sessions
                    WHERE date = ? AND timer_type = 'study' AND actual_duration IS NOT NULL
                    GROUP BY COALESCE(todo_content, '未分类')
                    HAVING total_duration > 0
                    ORDER BY total_duration DESC
                ''', (target_date,))
            elif has_todo_id:
                # 通过连表查询获取TODO内容
                cursor.execute('''
                    SELECT 
                        COALESCE(t.content, '未分类') as todo_name,
                        SUM(CASE WHEN s.completed THEN s.actual_duration ELSE 0 END) as total_duration
                    FROM study_sessions s
                    LEFT JOIN todo_items t ON s.todo_id = t.id
                    WHERE s.date = ? AND s.timer_type = 'study' AND s.actual_duration IS NOT NULL
                    GROUP BY COALESCE(t.content, '未分类')
                    HAVING total_duration > 0
                    ORDER BY total_duration DESC
                ''', (target_date,))
            else:
                # 没有TODO关联，返回总体统计
                cursor.execute('''
                    SELECT 
                        '学习时间' as todo_name,
                        SUM(CASE WHEN completed THEN actual_duration ELSE 0 END) as total_duration
                    FROM study_sessions
                    WHERE date = ? AND timer_type = 'study' AND actual_duration IS NOT NULL
                    HAVING total_duration > 0
                ''', (target_date,))
            
            results = cursor.fetchall()
            stats = []
            
            for row in results:
                stats.append({
                    'todo_name': row['todo_name'],
                    'total_duration': row['total_duration'],  # 秒
                    'duration_minutes': round(row['total_duration'] / 60, 1),  # 分钟
                    'duration_hours': round(row['total_duration'] / 3600, 2)  # 小时
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取TODO学习统计失败: {e}")
            return []

    def backup_data(self, backup_file: str = None) -> str:
        """
        备份数据

        Args:
            backup_file: 备份文件路径

        Returns:
            备份文件路径
        """
        try:
            if backup_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"data/backups/backup_{timestamp}.db"

            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)

            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_file, backup_file)

            self.logger.info(f"数据备份完成: {backup_file}")
            return backup_file

        except Exception as e:
            self.logger.error(f"数据备份失败: {e}")
            raise

    def restore_data(self, backup_file: str):
        """
        从备份恢复数据

        Args:
            backup_file: 备份文件路径
        """
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")

            # 关闭当前连接
            if self.connection:
                self.connection.close()
                self.connection = None

            # 恢复备份文件
            import shutil
            shutil.copy2(backup_file, self.db_file)

            # 重新初始化数据库连接
            self._initialize_database()

            self.logger.info(f"数据恢复完成: {backup_file}")

        except Exception as e:
            self.logger.error(f"数据恢复失败: {e}")
            raise

    def export_data(self, export_file: str, format_type: str = "json"):
        """
        导出数据

        Args:
            export_file: 导出文件路径
            format_type: 导出格式 (json, csv)
        """
        try:
            conn = self._get_connection()

            if format_type.lower() == "json":
                self._export_to_json(conn, export_file)
            elif format_type.lower() == "csv":
                self._export_to_csv(conn, export_file)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")

            self.logger.info(f"数据导出完成: {export_file}")

        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            raise

    def _export_to_json(self, conn: sqlite3.Connection, export_file: str):
        """导出为JSON格式"""
        cursor = conn.cursor()

        data = {
            'export_time': datetime.now().isoformat(),
            'study_sessions': [],
            'daily_stats': [],
            'timer_type_stats': []
        }

        # 导出学习会话
        cursor.execute('SELECT * FROM study_sessions ORDER BY start_time')
        data['study_sessions'] = [dict(row) for row in cursor.fetchall()]

        # 导出每日统计
        cursor.execute('SELECT * FROM daily_stats ORDER BY date')
        data['daily_stats'] = [dict(row) for row in cursor.fetchall()]

        # 导出计时器类型统计
        cursor.execute('SELECT * FROM timer_type_stats ORDER BY date, timer_type')
        data['timer_type_stats'] = [dict(row) for row in cursor.fetchall()]

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _export_to_csv(self, conn: sqlite3.Connection, export_file: str):
        """导出为CSV格式"""
        import csv

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM study_sessions ORDER BY start_time')

        with open(export_file, 'w', newline='', encoding='utf-8-sig') as f:
            if cursor.fetchone():
                cursor.execute('SELECT * FROM study_sessions ORDER BY start_time')
                writer = csv.writer(f)

                # 写入表头
                headers = [description[0] for description in cursor.description]
                writer.writerow(headers)

                # 写入数据
                writer.writerows(cursor.fetchall())

    def clean_old_data(self, retention_days: int = 365):
        """
        清理旧数据

        Args:
            retention_days: 数据保留天数
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_date = date.today() - timedelta(days=retention_days)

            # 删除旧的学习会话记录
            cursor.execute('DELETE FROM study_sessions WHERE date < ?', (cutoff_date,))
            sessions_deleted = cursor.rowcount

            # 删除旧的每日统计
            cursor.execute('DELETE FROM daily_stats WHERE date < ?', (cutoff_date,))
            daily_deleted = cursor.rowcount

            # 删除旧的计时器类型统计
            cursor.execute('DELETE FROM timer_type_stats WHERE date < ?', (cutoff_date,))
            type_deleted = cursor.rowcount

            conn.commit()

            # 优化数据库
            cursor.execute('VACUUM')

            self.logger.info(f"数据清理完成: 删除 {sessions_deleted} 个会话, "
                             f"{daily_deleted} 个每日统计, {type_deleted} 个类型统计")

        except Exception as e:
            self.logger.error(f"数据清理失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        
    def get_last_n_days(self, days: int = 7, mode: str = None) -> Dict[str, int]:
        """
        获取最近N天的学习或休息时间
        
        Args:
            days: 天数
            mode: 模式（'学习'或'休息'）
            
        Returns:
            日期和时间（秒）的字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            # 确定查询的时间字段
            time_field = 'total_study_time' if mode == '学习' else 'total_rest_time'
            
            cursor.execute(f'''
                SELECT date, {time_field} as duration
                FROM daily_stats
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (start_date, end_date))
            
            results = cursor.fetchall()
            
            # 创建结果字典
            data = {}
            for row in results:
                data[row['date']] = row['duration']
                
            # 确保所有日期都有数据
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                if date_str not in data:
                    data[date_str] = 0
                current_date += timedelta(days=1)
                
            return data
            
        except Exception as e:
            self.logger.error(f"获取最近{days}天数据失败: {e}")
            return {}