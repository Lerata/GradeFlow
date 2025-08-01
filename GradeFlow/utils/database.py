import streamlit as st
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from utils.crypto import hash_password

# Database file path
DB_PATH = "grading_system.db"

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Papers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            exam_id TEXT,
            subject TEXT,
            raw_text TEXT,
            ocr_confidence REAL,
            image_path TEXT,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''')
    
    # Grades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER NOT NULL,
            question_number INTEGER,
            ai_score REAL,
            ai_confidence REAL,
            human_score REAL,
            final_score REAL,
            subject TEXT,
            grading_details TEXT,
            graded_by INTEGER,
            reviewed_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (paper_id) REFERENCES papers (id),
            FOREIGN KEY (graded_by) REFERENCES users (id),
            FOREIGN KEY (reviewed_by) REFERENCES users (id)
        )
    ''')
    
    # Exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            total_questions INTEGER,
            max_score REAL,
            rubric TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            original_score REAL,
            reviewed_score REAL,
            comments TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grade_id) REFERENCES grades (id),
            FOREIGN KEY (reviewer_id) REFERENCES users (id)
        )
    ''')
    
    # Create default users if they don't exist
    create_default_users(cursor)
    
    conn.commit()
    conn.close()

def create_default_users(cursor):
    """Create default demo users"""
    default_users = [
        ('admin', 'admin123', 'System Administrator', 'admin@grading.system', 'admin'),
        ('teacher', 'teacher123', 'Demo Teacher', 'teacher@grading.system', 'teacher'),
        ('student', 'student123', 'Demo Student', 'student@grading.system', 'student')
    ]
    
    for username, password, name, email, role in default_users:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password_hash, name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hash_password(password), name, email, role))
        except sqlite3.IntegrityError:
            pass  # User already exists

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_user(username: str, password: str, name: str, email: str, role: str) -> bool:
    """Create new user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, email, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, hash_password(password), name, email, role))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_all_users() -> List[Dict]:
    """Get all users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, name, email, role, created_at FROM users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def save_paper(student_id: str, student_name: str, exam_id: str, subject: str, 
               raw_text: str, ocr_confidence: float, image_path: str, uploaded_by: int) -> int:
    """Save processed paper to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO papers (student_id, student_name, exam_id, subject, raw_text, 
                           ocr_confidence, image_path, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, student_name, exam_id, subject, raw_text, ocr_confidence, image_path, uploaded_by))
    
    paper_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return paper_id

def save_grade(paper_id: int, question_number: int, ai_score: float, ai_confidence: float,
               subject: str, grading_details: str, graded_by: int) -> int:
    """Save grade to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO grades (paper_id, question_number, ai_score, ai_confidence, subject,
                           grading_details, graded_by, final_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (paper_id, question_number, ai_score, ai_confidence, subject, grading_details, graded_by, ai_score))
    
    grade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return grade_id

def get_papers_for_review(limit: int = 50) -> List[Dict]:
    """Get papers pending review"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, u.name as uploaded_by_name
        FROM papers p
        LEFT JOIN users u ON p.uploaded_by = u.id
        WHERE p.status = 'pending'
        ORDER BY p.uploaded_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_grades_by_paper(paper_id: int) -> List[Dict]:
    """Get all grades for a paper"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT g.*, u1.name as graded_by_name, u2.name as reviewed_by_name
        FROM grades g
        LEFT JOIN users u1 ON g.graded_by = u1.id
        LEFT JOIN users u2 ON g.reviewed_by = u2.id
        WHERE g.paper_id = ?
        ORDER BY g.question_number
    ''', (paper_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_grade_score(grade_id: int, new_score: float, reviewed_by: int, comments: str = "") -> bool:
    """Update grade with human review"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE grades 
            SET human_score = ?, final_score = ?, reviewed_by = ?, 
                updated_at = CURRENT_TIMESTAMP, status = 'reviewed'
            WHERE id = ?
        ''', (new_score, new_score, reviewed_by, grade_id))
        
        # Add review record
        cursor.execute('''
            INSERT INTO reviews (grade_id, reviewer_id, reviewed_score, comments, status)
            VALUES (?, ?, ?, ?, 'completed')
        ''', (grade_id, reviewed_by, new_score, comments))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_student_grades(student_id: str) -> List[Dict]:
    """Get all grades for a student"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.student_name, p.exam_id, p.subject, p.uploaded_at,
               g.question_number, g.final_score, g.ai_confidence, g.status,
               g.grading_details
        FROM papers p
        JOIN grades g ON p.id = g.paper_id
        WHERE p.student_id = ?
        ORDER BY p.uploaded_at DESC, g.question_number
    ''', (student_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_system_stats() -> Dict:
    """Get system statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total papers
    cursor.execute('SELECT COUNT(*) as count FROM papers')
    total_papers = cursor.fetchone()['count']
    
    # Graded papers
    cursor.execute('SELECT COUNT(*) as count FROM papers WHERE status != "pending"')
    graded_papers = cursor.fetchone()['count']
    
    # Pending reviews
    cursor.execute('SELECT COUNT(*) as count FROM grades WHERE status = "pending"')
    pending_reviews = cursor.fetchone()['count']
    
    # Active users
    cursor.execute('SELECT COUNT(*) as count FROM users')
    active_users = cursor.fetchone()['count']
    
    # Grade distribution
    cursor.execute('''
        SELECT 
            CASE 
                WHEN final_score >= 90 THEN 'A'
                WHEN final_score >= 80 THEN 'B'
                WHEN final_score >= 70 THEN 'C'
                WHEN final_score >= 60 THEN 'D'
                ELSE 'F'
            END as grade,
            COUNT(*) as count
        FROM grades 
        WHERE final_score IS NOT NULL
        GROUP BY grade
    ''')
    
    grade_dist_rows = cursor.fetchall()
    grade_distribution = {row['grade']: row['count'] for row in grade_dist_rows}
    
    conn.close()
    
    return {
        'total_papers': total_papers,
        'graded_papers': graded_papers,
        'pending_reviews': pending_reviews,
        'active_users': active_users,
        'grade_distribution': grade_distribution
    }

def update_paper_status(paper_id: int, status: str) -> bool:
    """Update paper status"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE papers SET status = ? WHERE id = ?', (status, paper_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
