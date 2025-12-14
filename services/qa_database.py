"""
问答历史存档数据库模块
使用 SQLite 存储问答历史记录
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import threading

# 数据库文件路径
DB_PATH = Path(__file__).parent.parent / "qa_history.db"

# 线程本地存储，确保每个线程使用独立的连接
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """获取线程安全的数据库连接"""
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
    return _local.connection


def init_database():
    """初始化数据库表结构"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 创建问答历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'default',
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            agent_name TEXT,
            agent_role TEXT,
            intent_type TEXT DEFAULT 'qa',
            confidence REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    # 创建会话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id TEXT DEFAULT 'default',
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_session ON qa_history(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_user ON qa_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_created ON qa_history(created_at)")
    
    conn.commit()
    print(f"✅ 问答数据库初始化完成: {DB_PATH}")


def create_session(user_id: str = "default", title: str = None) -> str:
    """创建新会话"""
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO qa_sessions (session_id, user_id, title)
        VALUES (?, ?, ?)
    """, (session_id, user_id, title or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    
    conn.commit()
    return session_id


def save_qa_record(
    session_id: str,
    question: str,
    answer: str,
    agent_name: str = None,
    agent_role: str = None,
    intent_type: str = "qa",
    confidence: float = 0.0,
    user_id: str = "default",
    metadata: Dict = None
) -> int:
    """保存问答记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 插入问答记录
    cursor.execute("""
        INSERT INTO qa_history (
            session_id, user_id, question, answer, 
            agent_name, agent_role, intent_type, confidence, metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, user_id, question, answer,
        agent_name, agent_role, intent_type, confidence,
        json.dumps(metadata, ensure_ascii=False) if metadata else None
    ))
    
    record_id = cursor.lastrowid
    
    # 更新会话信息
    cursor.execute("""
        UPDATE qa_sessions 
        SET updated_at = CURRENT_TIMESTAMP,
            message_count = message_count + 1
        WHERE session_id = ?
    """, (session_id,))
    
    # 如果会话不存在，创建一个
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO qa_sessions (session_id, user_id, title, message_count)
            VALUES (?, ?, ?, 1)
        """, (session_id, user_id, question[:50] if len(question) > 50 else question))
    
    conn.commit()
    return record_id


def get_session_history(session_id: str, limit: int = 50) -> List[Dict]:
    """获取会话历史"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, question, answer, agent_name, agent_role, 
               intent_type, confidence, created_at, metadata
        FROM qa_history
        WHERE session_id = ?
        ORDER BY created_at ASC
        LIMIT ?
    """, (session_id, limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_recent_sessions(user_id: str = "default", limit: int = 10) -> List[Dict]:
    """获取最近的会话列表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, title, message_count, created_at, updated_at
        FROM qa_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_recent_qa_history(user_id: str = "default", limit: int = 20) -> List[Dict]:
    """获取最近的问答历史（跨会话）"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT h.id, h.session_id, h.question, h.answer, h.agent_name, 
               h.agent_role, h.intent_type, h.created_at,
               s.title as session_title
        FROM qa_history h
        LEFT JOIN qa_sessions s ON h.session_id = s.session_id
        WHERE h.user_id = ?
        ORDER BY h.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def search_qa_history(
    keyword: str,
    user_id: str = "default",
    limit: int = 20
) -> List[Dict]:
    """搜索问答历史"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT h.id, h.session_id, h.question, h.answer, h.agent_name,
               h.created_at, s.title as session_title
        FROM qa_history h
        LEFT JOIN qa_sessions s ON h.session_id = s.session_id
        WHERE h.user_id = ?
          AND (h.question LIKE ? OR h.answer LIKE ?)
        ORDER BY h.created_at DESC
        LIMIT ?
    """, (user_id, f"%{keyword}%", f"%{keyword}%", limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def delete_session(session_id: str) -> bool:
    """删除会话及其所有记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM qa_history WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM qa_sessions WHERE session_id = ?", (session_id,))
    
    conn.commit()
    return cursor.rowcount > 0


def get_statistics(user_id: str = "default") -> Dict:
    """获取统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 总问答数
    cursor.execute("""
        SELECT COUNT(*) as total FROM qa_history WHERE user_id = ?
    """, (user_id,))
    total = cursor.fetchone()['total']
    
    # 今日问答数
    cursor.execute("""
        SELECT COUNT(*) as today FROM qa_history 
        WHERE user_id = ? AND DATE(created_at) = DATE('now')
    """, (user_id,))
    today = cursor.fetchone()['today']
    
    # 会话数
    cursor.execute("""
        SELECT COUNT(*) as sessions FROM qa_sessions WHERE user_id = ?
    """, (user_id,))
    sessions = cursor.fetchone()['sessions']
    
    # 最常使用的智能体
    cursor.execute("""
        SELECT agent_name, COUNT(*) as count 
        FROM qa_history 
        WHERE user_id = ? AND agent_name IS NOT NULL
        GROUP BY agent_name
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,))
    top_agents = [dict(row) for row in cursor.fetchall()]
    
    return {
        "total_qa": total,
        "today_qa": today,
        "total_sessions": sessions,
        "top_agents": top_agents
    }


# 初始化数据库
init_database()

