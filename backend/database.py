"""
Database models and connection setup for Plan My Trip
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'tripxplorer.db')

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    email TEXT,
                    name TEXT,
                    google_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'freemium',
                    status TEXT NOT NULL DEFAULT 'active',
                    payment_id TEXT,
                    amount_paid REAL,
                    currency TEXT DEFAULT 'INR',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create usage_tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    month_year TEXT NOT NULL,
                    trips_used INTEGER DEFAULT 0,
                    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, month_year)
                )
            ''')
            
            # Create trip_history table for analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trip_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    city TEXT,
                    interests TEXT,
                    days INTEGER,
                    places_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def create_user(self, user_id: str, email: str = None, name: str = None, google_id: str = None) -> bool:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, email, name, google_id)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, email, name, google_id))
                
                # Create default freemium subscription
                cursor.execute('''
                    INSERT OR IGNORE INTO subscriptions (user_id, plan, status)
                    VALUES (?, 'freemium', 'active')
                ''', (user_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.*, s.plan, s.status, s.payment_id, s.amount_paid, s.currency, s.started_at, s.expires_at
                    FROM users u
                    LEFT JOIN subscriptions s ON u.user_id = s.user_id
                    WHERE u.user_id = ? AND s.status = 'active'
                    ORDER BY s.created_at DESC
                    LIMIT 1
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_subscription(self, user_id: str, plan: str, payment_id: str = None, 
                          amount_paid: float = None, currency: str = 'INR') -> bool:
        """Update user subscription"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate expiration date for premium (1 month from now)
                expires_at = None
                if plan == 'premium':
                    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
                
                cursor.execute('''
                    UPDATE subscriptions 
                    SET plan = ?, payment_id = ?, amount_paid = ?, currency = ?, 
                        expires_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND status = 'active'
                ''', (plan, payment_id, amount_paid, currency, expires_at, user_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False
    
    def get_usage(self, user_id: str, month_year: str = None) -> Dict[str, Any]:
        """Get user usage for a specific month"""
        if not month_year:
            month_year = datetime.now().strftime("%Y-%m")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get or create usage record
                cursor.execute('''
                    INSERT OR IGNORE INTO usage_tracking (user_id, month_year)
                    VALUES (?, ?)
                ''', (user_id, month_year))
                
                cursor.execute('''
                    SELECT trips_used, last_reset FROM usage_tracking
                    WHERE user_id = ? AND month_year = ?
                ''', (user_id, month_year))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'trips_used': row['trips_used'],
                        'last_reset': row['last_reset']
                    }
                return {'trips_used': 0, 'last_reset': datetime.now().isoformat()}
        except Exception as e:
            print(f"Error getting usage: {e}")
            return {'trips_used': 0, 'last_reset': datetime.now().isoformat()}
    
    def increment_usage(self, user_id: str, month_year: str = None) -> bool:
        """Increment user usage for the month"""
        if not month_year:
            month_year = datetime.now().strftime("%Y-%m")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or update usage
                cursor.execute('''
                    INSERT INTO usage_tracking (user_id, month_year, trips_used, last_reset)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, month_year) DO UPDATE SET
                        trips_used = trips_used + 1,
                        updated_at = CURRENT_TIMESTAMP
                ''', (user_id, month_year))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error incrementing usage: {e}")
            return False
    
    def record_trip(self, user_id: str, city: str, interests: str, days: int, places_count: int) -> bool:
        """Record a trip in history for analytics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trip_history (user_id, city, interests, days, places_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, city, interests, days, places_count))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording trip: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total trips
                cursor.execute('''
                    SELECT COUNT(*) as total_trips FROM trip_history WHERE user_id = ?
                ''', (user_id,))
                total_trips = cursor.fetchone()['total_trips']
                
                # Get trips this month
                current_month = datetime.now().strftime("%Y-%m")
                cursor.execute('''
                    SELECT COUNT(*) as monthly_trips FROM trip_history 
                    WHERE user_id = ? AND strftime('%Y-%m', created_at) = ?
                ''', (user_id, current_month))
                monthly_trips = cursor.fetchone()['monthly_trips']
                
                # Get most visited cities
                cursor.execute('''
                    SELECT city, COUNT(*) as visits FROM trip_history 
                    WHERE user_id = ? GROUP BY city ORDER BY visits DESC LIMIT 5
                ''', (user_id,))
                top_cities = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'total_trips': total_trips,
                    'monthly_trips': monthly_trips,
                    'top_cities': top_cities
                }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {'total_trips': 0, 'monthly_trips': 0, 'top_cities': []}

# Global database manager instance
db_manager = DatabaseManager()
