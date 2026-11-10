import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textbooks.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 教材表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS textbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            edition TEXT,
            course TEXT,
            price REAL NOT NULL,
            condition TEXT NOT NULL,
            contact TEXT NOT NULL,
            student_id TEXT,
            campus TEXT,
            description TEXT,
            seller_note TEXT,
            cover_path TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 求购表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title TEXT NOT NULL,
            course TEXT,
            author_required TEXT,
            max_price REAL,
            condition_required TEXT,
            contact TEXT NOT NULL,
            student_id TEXT,
            campus TEXT,
            note TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 评价表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reviewer_contact TEXT NOT NULL,
            reviewer_name TEXT,
            reviewee_contact TEXT NOT NULL,
            reviewee_name TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            related_book TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 兼容旧数据库：如果表已存在但缺少新列，尝试添加
    # （新安装的用户不需要这步，但保留以防万一）
    try:
        cursor.execute("ALTER TABLE textbooks ADD COLUMN cover_path TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE textbooks ADD COLUMN student_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE wants ADD COLUMN student_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE textbooks ADD COLUMN campus TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE wants ADD COLUMN campus TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

    # 空库时自动写入示例数据（云端重启后磁盘会重置，靠这里恢复演示数据）
    try:
        seed_sample_data()
    except Exception:
        pass


# ========== 示例数据自动初始化（供云端等空库环境使用） ==========

SAMPLE_TEXTBOOKS = [
    ("高等数学（第七版上册）", "高等数学A", 15.0, "八成新", "wechat_tom2024", "麦庐园", "上册，有少量笔记"),
    ("线性代数（第六版）", "线性代数", 8.0, "九成新", "wechat_lily888", "蛟桥园", "基本没怎么写"),
    ("概率论与数理统计（第四版）", "概率论与数理统计", 12.0, "有笔记/划线", "wechat_tom2024", "麦庐园", "重点章节都有笔记"),
    ("大学物理（第七版）上册", "大学物理", 18.0, "八成新", "wechat_wang2025", "枫林园", "上下册一起出"),
    ("Python编程：从入门到实践", "Python程序设计", 25.0, "九成新", "wechat_coder001", "麦庐园", "几乎全新"),
    ("英语四级真题卷", "大学英语", 5.0, "有笔记/划线", "wechat_lily888", "蛟桥园", "做了几套"),
    ("宏观经济学（第七版）", "宏观经济学", 20.0, "八成新", "wechat_econ2025", "枫林园", "曼昆版"),
    ("微观经济学（第九版）", "微观经济学", 18.0, "九成新", "wechat_econ2025", "枫林园", "平狄克版"),
    ("会计学原理", "会计学基础", 12.0, "八成新", "wechat_acc001", "麦庐园", "含课后习题答案"),
    ("管理学（第十一版）", "管理学原理", 15.0, "七成新", "wechat_mgmt001", "蛟桥园", "罗宾斯版"),
    ("C程序设计（第五版）", "C语言程序设计", 10.0, "有笔记/划线", "wechat_coder001", "麦庐园", "谭浩强版，笔记完整"),
    ("数据结构（C语言版）", "数据结构", 22.0, "八成新", "wechat_cs001", "蛟桥园", "严蔚敏版"),
    ("操作系统（第四版）", "操作系统", 25.0, "九成新", "wechat_cs001", "蛟桥园", "汤小丹版"),
    ("计算机网络（第八版）", "计算机网络", 20.0, "八成新", "wechat_cs001", "蛟桥园", "谢希仁版"),
    ("马克思主义基本原理", "马克思主义基本原理", 6.0, "九成新", "wechat_politics", "麦庐园", "2023版"),
    ("毛泽东思想和中国特色社会主义理论体系概论", "毛概", 8.0, "有笔记/划线", "wechat_politics", "麦庐园", "重点都划了"),
    ("大学物理实验", "大学物理实验", 10.0, "八成新", "wechat_wang2025", "枫林园", "实验报告写了一半"),
    ("微积分（上下册）", "微积分", 16.0, "九成新", "wechat_math2025", "蛟桥园", "华东师大版"),
    ("复变函数与积分变换", "复变函数", 10.0, "八成新", "wechat_math2025", "蛟桥园", "课后习题有答案"),
    ("大学英语综合教程3", "大学英语", 12.0, "九成新", "wechat_lily888", "蛟桥园", "全新没怎么用"),
]

SAMPLE_WANTS = [
    ("高等数学（第七版下册）", "高等数学A", 15.0, "有笔记也可以", "wechat_zhang2025", "麦庐园", "上学期买了上册，急需下册"),
    ("复变函数与积分变换", "复变函数", 10.0, "八成新以上", "wechat_lily888", "蛟桥园", "下学期要学"),
    ("机器学习（周志华）", "人工智能导论", 40.0, "九成新", "wechat_coder001", "麦庐园", "西瓜书，考研用"),
    ("货币金融学", "货币银行学", 20.0, "八成新", "wechat_finance", "枫林园", "米什金版"),
    ("财务管理学", "财务管理", 15.0, "九成新", "wechat_acc002", "麦庐园", "荆新版"),
]


def seed_sample_data(force=False):
    """当数据库为空时自动写入示例数据，保证部署后首页就有内容可看"""
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    except Exception:
        conn.close()
        return 0
    conn.close()

    if count > 0 and not force:
        return 0

    for t in SAMPLE_TEXTBOOKS:
        title, course, price, condition, contact, campus, note = t
        add_textbook(
            title=title, author="", publisher="", edition="",
            course=course, price=price, condition=condition,
            contact=contact, description=note, campus=campus
        )

    for w in SAMPLE_WANTS:
        book_title, course, max_price, condition, contact, campus, note = w
        add_want(
            book_title=book_title, course=course, author_required="",
            max_price=max_price, condition_required=condition,
            contact=contact, note=note, campus=campus
        )

    return len(SAMPLE_TEXTBOOKS) + len(SAMPLE_WANTS)


# ========== 教材相关 ==========

def add_textbook(title, author, publisher, edition, course, price, condition, contact,
                 description, seller_note="", student_id="", cover_path="", campus=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO textbooks (title, author, publisher, edition, course, price, condition,
                               contact, student_id, campus, description, seller_note, cover_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, author, publisher, edition, course, price, condition,
          contact, student_id, campus, description, seller_note, cover_path))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_textbooks(status=None):
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM textbooks WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM textbooks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_textbooks(keyword=None, course=None, min_price=None, max_price=None, condition=None, campus=None):
    conn = get_connection()
    query = "SELECT * FROM textbooks WHERE status = 'available'"
    params = []

    if keyword:
        query += " AND (title LIKE ? OR author LIKE ? OR description LIKE ? OR course LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw, kw])
    if course:
        query += " AND course = ?"
        params.append(course)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if condition:
        query += " AND condition = ?"
        params.append(condition)
    if campus:
        query += " AND campus = ?"
        params.append(campus)

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_textbooks_by_contact(contact):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM textbooks WHERE contact = ? ORDER BY created_at DESC", (contact,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_status(tid, status):
    conn = get_connection()
    conn.execute("UPDATE textbooks SET status = ? WHERE id = ?", (status, tid))
    conn.commit()
    conn.close()


def delete_textbook(tid):
    conn = get_connection()
    conn.execute("DELETE FROM textbooks WHERE id = ?", (tid,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    available = conn.execute("SELECT COUNT(*) FROM textbooks WHERE status = 'available'").fetchone()[0]
    sold = conn.execute("SELECT COUNT(*) FROM textbooks WHERE status = 'sold'").fetchone()[0]
    avg_price = conn.execute("SELECT AVG(price) FROM textbooks WHERE status = 'available'").fetchone()[0]
    total_wants = conn.execute("SELECT COUNT(*) FROM wants WHERE status = 'open'").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "available": available,
        "sold": sold,
        "avg_price": round(avg_price, 1) if avg_price else 0,
        "open_wants": total_wants
    }


def get_all_courses():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT course FROM textbooks WHERE course != '' ORDER BY course").fetchall()
    conn.close()
    return [r[0] for r in rows]


# ========== 求购相关 ==========

def add_want(book_title, course, author_required, max_price, condition_required,
             contact, note="", student_id="", campus=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wants (book_title, course, author_required, max_price, condition_required,
                           contact, student_id, campus, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (book_title, course, author_required, max_price, condition_required,
          contact, student_id, campus, note))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_wants(status=None):
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM wants WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM wants ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_wants(keyword=None):
    conn = get_connection()
    query = "SELECT * FROM wants WHERE status = 'open'"
    params = []
    if keyword:
        query += " AND (book_title LIKE ? OR course LIKE ? OR note LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_want_status(wid, status):
    conn = get_connection()
    conn.execute("UPDATE wants SET status = ? WHERE id = ?", (status, wid))
    conn.commit()
    conn.close()


def delete_want(wid):
    conn = get_connection()
    conn.execute("DELETE FROM wants WHERE id = ?", (wid,))
    conn.commit()
    conn.close()


# ========== 评价相关 ==========

def add_review(reviewer_contact, reviewer_name, reviewee_contact, reviewee_name,
               rating, comment, related_book=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reviews (reviewer_contact, reviewer_name, reviewee_contact, reviewee_name,
                             rating, comment, related_book)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (reviewer_contact, reviewer_name, reviewee_contact, reviewee_name,
          rating, comment, related_book))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_reviews_for_user(contact):
    """获取某用户收到的所有评价"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM reviews WHERE reviewee_contact = ? ORDER BY created_at DESC
    """, (contact,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_rating(contact):
    """获取某用户的平均评分和评价数"""
    conn = get_connection()
    row = conn.execute("""
        SELECT AVG(rating) as avg_rating, COUNT(*) as count
        FROM reviews WHERE reviewee_contact = ?
    """, (contact,)).fetchone()
    conn.close()
    if row and row["count"] > 0:
        return {"avg": round(row["avg_rating"], 1), "count": row["count"]}
    return {"avg": 0, "count": 0}
