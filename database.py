import sqlite3
from sqlite3 import Error
from config import DB_NAME
import logging

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Ma'lumotlar bazasini ishga tushiradi va jadvallarni yaratadi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                is_driver BOOLEAN DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Drivers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                vehicle_type TEXT,  -- car_model o'rniga vehicle_type
                license_number TEXT,
                license_photo TEXT,
                status TEXT DEFAULT 'pending',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_name TEXT,
                from_viloyat TEXT,
                from_tuman TEXT,
                to_viloyat TEXT,
                to_tuman TEXT,
                weight REAL,
                vehicle_type TEXT,  -- Yangi maydon
                photo_id TEXT,
                pickup_address TEXT,
                phone TEXT,
                latitude REAL,
                longitude REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        
        conn.commit()
        logger.info("Database tables initialized successfully.")
    except Error as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def register_user(telegram_id, username, full_name, phone, is_driver=False):
    """Foydalanuvchini ro'yxatdan o'tkazadi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, full_name, phone, is_driver)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, username, full_name, phone, is_driver))
        conn.commit()
        logger.info(f"User {telegram_id} registered successfully.")
    except Error as e:
        logger.error(f"Error registering user {telegram_id}: {e}")
    finally:
        if conn:
            conn.close()

def register_driver(user_id, vehicle_type, license_number, license_photo, status="pending"):
    """Haydovchini ro'yxatdan o'tkazadi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO drivers (user_id, vehicle_type, license_number, license_photo, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, vehicle_type, license_number, license_photo, status))
        conn.commit()
        logger.info(f"Driver {user_id} registered with vehicle_type: {vehicle_type}, status: {status}.")
    except Error as e:
        logger.error(f"Error registering driver {user_id}: {e}")
    finally:
        if conn:
            conn.close()

def is_user_registered(telegram_id):
    """Foydalanuvchi ro'yxatdan o'tganligini tekshiradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        return user is not None
    except Error as e:
        logger.error(f"Error checking user registration for {telegram_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def is_driver(telegram_id):
    """Foydalanuvchi haydovchi ekanligini tekshiradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT is_driver FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result else False
    except Error as e:
        logger.error(f"Error checking driver status for {telegram_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_phone(telegram_id):
    """Foydalanuvchi telefon raqamini qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT phone FROM users WHERE telegram_id = ?', (telegram_id,))
        phone = cursor.fetchone()
        return phone[0] if phone else None
    except Error as e:
        logger.error(f"Error getting phone for user {telegram_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_driver_by_id(user_id):
    """Haydovchi ma'lumotlarini user_id bo'yicha qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, vehicle_type, license_number, license_photo, status FROM drivers WHERE user_id = ?', (user_id,))
        driver = cursor.fetchone()
        return driver
    except Error as e:
        logger.error(f"Error getting driver by id {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_driver_status(user_id, status):
    """Haydovchi statusini yangilaydi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE drivers SET status = ? WHERE user_id = ?', (status, user_id))
        conn.commit()
        logger.info(f"Driver {user_id} status updated to {status}.")
    except Error as e:
        logger.error(f"Error updating driver status for {user_id}: {e}")
    finally:
        if conn:
            conn.close()

def save_order(user_id, order_name, from_viloyat, from_tuman, to_viloyat, to_tuman, weight, vehicle_type, photo_id, pickup_address, phone, latitude, longitude):
    """Buyurtmani ma'lumotlar bazasiga saqlaydi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, order_name, from_viloyat, from_tuman, to_viloyat, to_tuman, weight, vehicle_type, photo_id, pickup_address, phone, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, order_name, from_viloyat, from_tuman, to_viloyat, to_tuman, weight, vehicle_type, photo_id, pickup_address, phone, latitude, longitude))
        conn.commit()
        logger.info(f"Order saved for user {user_id} with vehicle_type: {vehicle_type}.")
    except Error as e:
        logger.error(f"Error saving order for user {user_id}: {e}")
    finally:
        if conn:
            conn.close()

def get_statistics():
    """Statistik ma'lumotlarni qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_driver = 1')
        total_drivers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders')
        total_orders = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
        pending_orders = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'total_drivers': total_drivers,
            'total_orders': total_orders,
            'pending_orders': pending_orders
        }
    except Error as e:
        logger.error(f"Error getting statistics: {e}")
        return {'total_users': 0, 'total_drivers': 0, 'total_orders': 0, 'pending_orders': 0}
    finally:
        if conn:
            conn.close()

def get_all_users():
    """Barcha foydalanuvchilarni qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id, username, full_name, phone, is_driver FROM users')
        users = cursor.fetchall()
        return users
    except Error as e:
        logger.error(f"Error getting all users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_drivers():
    """Barcha haydovchilarni qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.telegram_id, u.username, u.full_name, u.phone, d.vehicle_type, d.license_number, d.license_photo, d.status
            FROM users u
            JOIN drivers d ON u.telegram_id = d.user_id
            WHERE u.is_driver = 1
        ''')
        drivers = cursor.fetchall()
        return drivers
    except Error as e:
        logger.error(f"Error getting all drivers: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_orders():
    """Barcha buyurtmalarni qaytaradi."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        orders = cursor.fetchall()
        return orders
    except Error as e:
        logger.error(f"Error getting all orders: {e}")
        return []
    finally:
        if conn:
            conn.close()