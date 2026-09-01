import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'tracker.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            platform TEXT NOT NULL,
            target_price REAL NOT NULL,
            current_price REAL,
            initial_price REAL,
            image_url TEXT,
            last_checked DATETIME,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Price history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Default settings
    default_settings = {
        'check_interval_hours': '4',
        'telegram_bot_token': '',
        'telegram_chat_id': '',
        'email_alerts_enabled': 'false',
        'smtp_email': '',
        'smtp_password': '',
        'recipient_email': ''
    }
    
    for key, val in default_settings.items():
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, val))
        
    conn.commit()
    conn.close()

def get_all_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, 
               (SELECT price FROM price_history WHERE product_id = p.id ORDER BY timestamp DESC LIMIT 1) as latest_price
        FROM products p
        ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_product(title, url, platform, target_price, current_price, image_url):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (title, url, platform, target_price, current_price, initial_price, image_url, last_checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (title, url, platform, target_price, current_price, current_price, image_url))
    product_id = cursor.lastrowid
    
    if current_price is not None:
        cursor.execute('''
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
        ''', (product_id, current_price))
        
    conn.commit()
    conn.close()
    return product_id

def update_product_price(product_id, current_price, title=None, image_url=None):
    conn = get_db()
    cursor = conn.cursor()
    
    if title and image_url:
        cursor.execute('''
            UPDATE products
            SET current_price = ?, title = ?, image_url = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (current_price, title, image_url, product_id))
    elif title:
        cursor.execute('''
            UPDATE products
            SET current_price = ?, title = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (current_price, title, product_id))
    elif image_url:
        cursor.execute('''
            UPDATE products
            SET current_price = ?, image_url = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (current_price, image_url, product_id))
    else:
        cursor.execute('''
            UPDATE products
            SET current_price = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (current_price, product_id))
    
    if current_price is not None:
        cursor.execute('''
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
        ''', (product_id, current_price))
    
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    cursor.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
    conn.commit()
    conn.close()

def get_product_history(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT price, timestamp FROM price_history
        WHERE product_id = ?
        ORDER BY timestamp ASC
    ''', (product_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings')
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def update_settings(settings_dict):
    conn = get_db()
    cursor = conn.cursor()
    for key, val in settings_dict.items():
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, str(val)))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
