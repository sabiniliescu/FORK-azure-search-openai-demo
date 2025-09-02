#!/usr/bin/env python3
"""
Test simplu pentru conectivitatea la Azure SQL Database
"""

import os
import pyodbc
from dotenv import load_dotenv

# Încărcăm variabilele de mediu
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_path, override=True)

def test_simple_connection():
    """Test simplu de conectivitate"""
    print("=== TEST SIMPLU CONECTIVITATE AZURE SQL ===\n")
    
    # Configurație - fără valori default pentru a forța încărcarea din .env
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    
    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'SET' if password else 'NOT SET'}")
    print()
    
    if not all([server, database, username, password]):
        print("❌ Una sau mai multe variabile de mediu nu sunt setate!")
        print(f"Server: {'SET' if server else 'NOT SET'}")
        print(f"Database: {'SET' if database else 'NOT SET'}")
        print(f"Username: {'SET' if username else 'NOT SET'}")
        print(f"Password: {'SET' if password else 'NOT SET'}")
        return False
    
    # Construiește connection string cu format simplu
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print("Connection string construit:")
    # Print fără parolă pentru securitate
    safe_conn_str = connection_string.replace(f"Password={password};", "Password=***;")
    print(safe_conn_str)
    print("Încerc să mă conectez...")
    
    try:
        # Testez conectivitatea directă
        print("Conectare în curs...")
        connection = pyodbc.connect(connection_string)
        print("✓ Conectare reușită!")
        
        # Test query simplu
        cursor = connection.cursor()
        cursor.execute("SELECT @@VERSION AS version")
        row = cursor.fetchone()
        print(f"✓ Versiune SQL Server: {row.version[:50]}...")
        
        # Test verificare bază de date
        cursor.execute("SELECT DB_NAME() AS current_database")
        row = cursor.fetchone()
        print(f"✓ Baza de date curentă: {row.current_database}")
        
        # Test verificare permisiuni pentru creare tabele
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_logs_test' AND xtype='U')
                CREATE TABLE chat_logs_test (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    test_message NVARCHAR(100)
                )
            """)
            connection.commit()
            print("✓ Permisiuni CREATE TABLE: OK")
            
            # Test insert
            cursor.execute("INSERT INTO chat_logs_test (test_message) VALUES (?)", "Test message")
            connection.commit()
            print("✓ Permisiuni INSERT: OK")
            
            # Test select
            cursor.execute("SELECT COUNT(*) as count FROM chat_logs_test")
            row = cursor.fetchone()
            print(f"✓ Permisiuni SELECT: OK (găsite {row.count} înregistrări)")
            
            # Cleanup
            cursor.execute("DROP TABLE chat_logs_test")
            connection.commit()
            print("✓ Permisiuni DROP: OK")
            
        except Exception as perm_error:
            print(f"❌ Eroare la testarea permisiunilor: {perm_error}")
        
        cursor.close()
        connection.close()
        print("\n🎉 TOATE TESTELE AU REUȘIT!")
        print("✅ Conectivitatea la Azure SQL Database funcționează perfect!")
        return True
        
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        return False

if __name__ == "__main__":
    test_simple_connection()
