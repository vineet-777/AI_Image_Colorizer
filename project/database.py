# -*- coding: utf-8 -*-
"""
SQLite Database Module
Handles all database operations for the image colorization app
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def init_database():
    """Initialize database with required tables and indexes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            last_login TEXT DEFAULT NULL,
            created_at TEXT DEFAULT NULL
        )
    ''')
    
    # User images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_images (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            original_filename TEXT,
            original_image_path TEXT,
            colorized_image_path TEXT,
            file_size INTEGER,
            created_at TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Performance indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_images_user_id ON user_images(user_id)')
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_email(email):
    """Retrieve user by email address"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_user_by_id(user_id):
    """Retrieve user by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def create_user(user_id, full_name, email, password_hash):
    """Create new user account"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO users (id, full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)',
            (user_id, full_name, email, password_hash, created_at)
        )
        return user_id

def update_user_last_login(user_id):
    """Update user's last login timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        last_login = datetime.now().isoformat()
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (last_login, user_id)
        )

def get_user_images(user_id):
    """Get all images for a user (newest first)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM user_images WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def create_user_image(image_id, user_id, original_filename, original_image_path, colorized_image_path, file_size):
    """Save image metadata to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute(
            '''INSERT INTO user_images 
               (id, user_id, original_filename, original_image_path, colorized_image_path, file_size, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (image_id, user_id, original_filename, original_image_path, colorized_image_path, file_size, created_at)
        )
        return image_id

def get_user_image(image_id, user_id):
    """Retrieve specific image by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM user_images WHERE id = ? AND user_id = ?',
            (image_id, user_id)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def delete_user_image(image_id):
    """Delete image record from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_images WHERE id = ?', (image_id,))
