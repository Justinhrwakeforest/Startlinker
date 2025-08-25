#!/usr/bin/env python
"""
Script to manually create reports app database tables
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.db import connection

def create_reports_tables():
    """Create the reports app tables manually"""
    print("Creating reports app database tables...")
    
    with connection.cursor() as cursor:
        # Create UserReport table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports_userreport (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type VARCHAR(50) NOT NULL,
                reason TEXT NOT NULL,
                evidence_urls TEXT DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'pending',
                priority VARCHAR(20) DEFAULT 'medium',
                admin_notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                resolved_at DATETIME,
                reporter_id INTEGER NOT NULL REFERENCES users_user(id),
                reported_user_id INTEGER NOT NULL REFERENCES users_user(id),
                assigned_admin_id INTEGER REFERENCES users_user(id),
                UNIQUE(reporter_id, reported_user_id)
            )
        """)
        
        # Create ReportAction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports_reportaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at DATETIME NOT NULL,
                report_id INTEGER NOT NULL REFERENCES reports_userreport(id),
                admin_id INTEGER NOT NULL REFERENCES users_user(id)
            )
        """)
        
        # Create ReportStatistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports_reportstatistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type VARCHAR(50) NOT NULL,
                total_count INTEGER DEFAULT 0,
                pending_count INTEGER DEFAULT 0,
                resolved_count INTEGER DEFAULT 0,
                average_resolution_time REAL DEFAULT 0.0,
                date DATE NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(report_type, date)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_userreport_reporter ON reports_userreport(reporter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_userreport_reported_user ON reports_userreport(reported_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_userreport_status ON reports_userreport(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_userreport_priority ON reports_userreport(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_userreport_created_at ON reports_userreport(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_reportaction_report ON reports_reportaction(report_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_reportaction_admin ON reports_reportaction(admin_id)")
        
        print("[OK] Database tables created successfully")
        
    return True

if __name__ == "__main__":
    try:
        success = create_reports_tables()
        if success:
            print("ALL REPORTS DATABASE TABLES CREATED")
        else:
            print("FAILED TO CREATE SOME TABLES")
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()