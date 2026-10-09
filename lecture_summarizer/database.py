import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            video_path TEXT,
            pdf_path TEXT,
            transcript TEXT,
            summary TEXT,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add progress column if missing (existing databases)
    try:
        cursor.execute('ALTER TABLE lectures ADD COLUMN progress INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slide_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            page_number INTEGER,
            FOREIGN KEY (lecture_id) REFERENCES lectures (id)
        )
    ''')

    conn.commit()
    conn.close()


def create_lecture(title, video_path=None, pdf_path=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO lectures (title, video_path, pdf_path, status)
        VALUES (?, ?, ?, 'pending')
    ''', (title, video_path, pdf_path))

    lecture_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return lecture_id


def update_lecture_status(lecture_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE lectures SET status = ? WHERE id = ?
    ''', (status, lecture_id))

    conn.commit()
    conn.close()


def update_lecture_progress(lecture_id, progress):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE lectures SET progress = ? WHERE id = ?', (progress, lecture_id))
    conn.commit()
    conn.close()


def update_lecture_transcript(lecture_id, transcript):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE lectures SET transcript = ? WHERE id = ?
    ''', (transcript, lecture_id))

    conn.commit()
    conn.close()


def update_lecture_summary(lecture_id, summary):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE lectures SET summary = ?, status = 'complete' WHERE id = ?
    ''', (summary, lecture_id))

    conn.commit()
    conn.close()


def add_slide_image(lecture_id, image_path, page_number):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO slide_images (lecture_id, image_path, page_number)
        VALUES (?, ?, ?)
    ''', (lecture_id, image_path, page_number))

    conn.commit()
    conn.close()


def get_lecture(lecture_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM lectures WHERE id = ?', (lecture_id,))
    lecture = cursor.fetchone()

    if lecture:
        cursor.execute('''
            SELECT image_path, page_number FROM slide_images
            WHERE lecture_id = ? ORDER BY page_number
        ''', (lecture_id,))
        images = cursor.fetchall()

        result = dict(lecture)
        result['images'] = [{'path': img['image_path'], 'page': img['page_number']} for img in images]
    else:
        result = None

    conn.close()
    return result


def get_all_lectures():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, title, status, created_at FROM lectures ORDER BY created_at DESC')
    lectures = cursor.fetchall()

    result = [dict(lecture) for lecture in lectures]

    conn.close()
    return result


def delete_lecture(lecture_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM slide_images WHERE lecture_id = ?', (lecture_id,))
    cursor.execute('DELETE FROM lectures WHERE id = ?', (lecture_id,))

    conn.commit()
    conn.close()
