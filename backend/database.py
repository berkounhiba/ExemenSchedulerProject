"""
Database connection and utility functions
Handles all PostgreSQL interactions
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from config import get_connection_string
import sys


def get_connection():
    """
    Create and return a PostgreSQL connection
    Returns: connection object or None on error
    """
    try:
        conn = psycopg2.connect(get_connection_string())
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def test_connection():
    """
    Test database connection and display info
    Returns: True if successful, False otherwise
    """
    print("🔄 Testing PostgreSQL connection...")
    conn = get_connection()
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version[0][:50]}...")
            
            # Check tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            if tables:
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cur.fetchone()[0]
                        print(f"   - {table[0]}: {count:,} rows")
                    except:
                        print(f"   - {table[0]}")
            else:
                print("\n⚠️  No tables found. Run create_tables.sql first!")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            if conn:
                conn.close()
            return False
    else:
        print("❌ Cannot connect to database")
        print("\n💡 Checklist:")
        print("   1. PostgreSQL is running")
        print("   2. Database 'gestion_examens' exists")
        print("   3. Password in config.py is correct")
        print("   4. User has proper permissions")
        return False


def execute_query(query, params=None, fetch=False, fetch_one=False):
    """
    Execute a SQL query
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
        fetch: Return all results
        fetch_one: Return one result
    
    Returns: Query results or True/None
    """
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        
        if fetch_one:
            result = cur.fetchone()
        elif fetch:
            result = cur.fetchall()
        else:
            result = True
            
        conn.commit()
        cur.close()
        conn.close()
        return result
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        print(f"Query: {query[:100]}...")
        if conn:
            conn.rollback()
            conn.close()
        return None


def execute_query_dict(query, params=None):
    """
    Execute query and return results as list of dictionaries
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
    
    Returns: List of dictionaries
    """
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return [dict(row) for row in result]
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None


def execute_sql_file(filepath):
    """
    Execute a complete SQL file
    
    Args:
        filepath: Path to SQL file
    
    Returns: True if successful, False otherwise
    """
    conn = get_connection()
    if not conn:
        return False
        
    try:
        cur = conn.cursor()
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cur.execute(sql_script)
        conn.commit()
        print(f"✅ File {filepath} executed successfully")
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error executing file: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_table_stats():
    """
    Get row counts for all tables
    Returns: Dictionary with table names and counts
    """
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    
    tables = execute_query(query, fetch=True)
    if not tables:
        return {}
    
    stats = {}
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        for table in tables:
            table_name = table[0]
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                stats[table_name] = count
            except:
                stats[table_name] = 0
        cur.close()
        conn.close()
    
    return stats


def clear_all_data():
    """
    Clear all data from all tables
    WARNING: This deletes everything!
    """
    print("⚠️  WARNING: This will delete ALL data from the database!")
    response = input("Type 'DELETE' to confirm: ")
    
    if response != 'DELETE':
        print("❌ Operation cancelled")
        return False
    
    tables = [
        'surveillances', 'conflits', 'examens', 'inscriptions',
        'modules', 'professeurs', 'etudiants', 'lieu_examen',
        'groups', 'formations', 'specializations', 'departements'
    ]
    
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            for table in tables:
                cur.execute(f"DELETE FROM {table}")
                print(f"   🗑️  Cleared {table}")
            conn.commit()
            cur.close()
            conn.close()
            print("✅ All data cleared successfully")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    return False


# Test when run directly
if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    test_connection()
    
    print("\n" + "=" * 70)
    print("TABLE STATISTICS")
    print("=" * 70)
    stats = get_table_stats()
    if stats:
        total = sum(stats.values())
        print(f"\n📊 Total rows in database: {total:,}\n")
        for table, count in sorted(stats.items()):
            print(f"   {table:<20} {count:>10,}")
    else:
        print("No statistics available")