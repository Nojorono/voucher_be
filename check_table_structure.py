#!/usr/bin/env python
"""
Check database table structure for wholesale
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from wholesales.models import Wholesale

def check_table_structure():
    print("🔍 Checking Wholesale Table Structure")
    print("=" * 60)
    
    # Check if table exists and its structure
    with connection.cursor() as cursor:
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'wholesales_wholesale'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("Table: wholesales_wholesale")
        print("-" * 60)
        print(f"{'Column Name':<20} {'Data Type':<15} {'Nullable':<10} {'Default':<15}")
        print("-" * 60)
        
        parent_column_exists = False
        for column in columns:
            column_name, data_type, is_nullable, column_default = column
            if column_name == 'parent_id':
                parent_column_exists = True
            print(f"{column_name:<20} {data_type:<15} {is_nullable:<10} {str(column_default):<15}")
        
        print("-" * 60)
        
        if parent_column_exists:
            print("✅ parent_id column exists in the table")
        else:
            print("❌ parent_id column NOT found in the table")
            print("   This means the migration hasn't been run yet")
        
        # Check if there's any data
        cursor.execute("SELECT COUNT(*) FROM wholesales_wholesale")
        count = cursor.fetchone()[0]
        print(f"📊 Total records in table: {count}")
        
        if count > 0:
            # Show some sample data
            cursor.execute("SELECT id, name, parent_id FROM wholesales_wholesale LIMIT 5")
            rows = cursor.fetchall()
            
            print("\n📋 Sample data:")
            print(f"{'ID':<5} {'Name':<25} {'Parent ID':<10}")
            print("-" * 40)
            for row in rows:
                id_val, name, parent_id = row
                print(f"{id_val:<5} {name:<25} {str(parent_id):<10}")

if __name__ == "__main__":
    try:
        check_table_structure()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   This might be due to database connection issues")
        print("   Make sure PostgreSQL is running and accessible")
