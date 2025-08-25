import sqlite3
from datetime import datetime, date

def check_sessions():
    # 连接到数据库
    conn = sqlite3.connect('data/focus_timer.db')
    conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    cursor = conn.cursor()
    
    # 查询有todo_id的会话记录
    cursor.execute("SELECT id, todo_id, todo_content FROM study_sessions WHERE todo_id IS NOT NULL LIMIT 5;")
    results = cursor.fetchall()
    
    print("有TODO关联的会话记录:")
    for row in results:
        print(f"ID: {row['id']}, TODO ID: {row['todo_id']}, TODO内容: '{row['todo_content']}'")
    
    # 查询所有字段信息
    cursor.execute("PRAGMA table_info(study_sessions);")
    columns = cursor.fetchall()
    print("\nstudy_sessions表结构:")
    for col in columns:
        print(f"列名: {col[1]}, 类型: {col[2]}, 是否可为空: {col[3]}, 默认值: {col[4]}, 是否为主键: {col[5]}")
    
    conn.close()

if __name__ == "__main__":
    check_sessions()