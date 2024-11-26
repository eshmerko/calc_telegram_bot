import sqlite3

def init_db():
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()

    # Создаем таблицу для настроек админа, если её нет
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reception FLOAT DEFAULT 500,
        sorting FLOAT DEFAULT 5,
        storage FLOAT DEFAULT 65,
        labeling FLOAT DEFAULT 5,
        picking FLOAT DEFAULT 5,
        logistics FLOAT DEFAULT 1000
    )
    """)

    # Создаем таблицу для пользовательских настроек (если её нет)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        quantity INTEGER DEFAULT 1,
        storage_days INTEGER DEFAULT 15,
        volume FLOAT DEFAULT 0
    )
    """)

    # Проверка на наличие столбца 'volume', если его нет - добавляем
    try:
        cursor.execute("SELECT volume FROM user_settings LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN volume FLOAT DEFAULT 0")
    
    conn.commit()
    conn.close()

# Инициализация базы данных
init_db()
