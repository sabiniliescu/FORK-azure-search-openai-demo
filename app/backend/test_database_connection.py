#!/usr/bin/env python3
"""
Test script pentru verificarea conectivității la baza de date Azure SQL
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Adăugăm calea către modulele noastre
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_logging.database_logger import azure_sql_logger, PYODBC_AVAILABLE
from chat_logging.chat_logger import chat_logger

async def test_database_connection():
    """Test complet pentru conectivitatea la baza de date"""
    
    print("=" * 80)
    print("🧪 ÎNCEPE TESTAREA CONECTIVITĂȚII LA BAZA DE DATE")
    print("=" * 80)
    
    # Test 1: Verifică disponibilitatea pyodbc
    print("\n1️⃣ Test disponibilitate pyodbc:")
    print(f"   PYODBC_AVAILABLE: {PYODBC_AVAILABLE}")
    
    if not PYODBC_AVAILABLE:
        print("   ❌ PYODBC nu este disponibil!")
        print("   💡 Rulați: pip install pyodbc")
        return False
    else:
        print("   ✅ PYODBC este disponibil!")
    
    # Test 2: Verifică parametrii de conexiune
    print("\n2️⃣ Test parametri de conexiune:")
    
    from dotenv import load_dotenv
    # Încărcăm .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    load_dotenv(env_path)
    
    server = os.getenv("AZURE_SQL_SERVER", "mihaiweb.database.windows.net")
    database = os.getenv("AZURE_SQL_DATABASE", "MihAI_Web_logs")
    username = os.getenv("AZURE_SQL_USERNAME", "mihaiuser")
    password = os.getenv("AZURE_SQL_PASSWORD", "Parola_Complexa_123!")
    
    print(f"   Server: {server}")
    print(f"   Database: {database}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password) if password else 'None'}")
    print(f"   Enable DB Logging: {azure_sql_logger.enable_db_logging}")
    print(f"   Connection String Exists: {'Yes' if azure_sql_logger.connection_string else 'No'}")
    
    # Test 3: Test conexiune directă
    print("\n3️⃣ Test conexiune directă la baza de date:")
    try:
        if PYODBC_AVAILABLE and azure_sql_logger.connection_string:
            import pyodbc
            conn = pyodbc.connect(azure_sql_logger.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f"   ✅ SQL Server Version: {version[:50]}...")
            
            # Test simplu SELECT 1
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()[0]
            print(f"   ✅ Test query result: {result}")
            
            conn.close()
        else:
            print("   ❌ Nu se poate testa conexiunea - lipsesc parametrii!")
            return False
        
    except Exception as e:
        print(f"   ❌ Eroare la testarea conexiunii: {e}")
        return False
    
    # Test 4: Test schema tabelei
    print("\n4️⃣ Test verificare schema tabelei:")
    try:
        if PYODBC_AVAILABLE and azure_sql_logger.connection_string:
            import pyodbc
            conn = pyodbc.connect(azure_sql_logger.connection_string)
            cursor = conn.cursor()
            
            # Verificăm dacă tabela există
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'chat_logs'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print("   ✅ Tabela chat_logs există!")
                
                # Verificăm structura tabelului
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'chat_logs'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = cursor.fetchall()
                print(f"   📊 Structura tabelului ({len(columns)} coloane):")
                for col in columns:
                    print(f"      - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("   ❌ Tabela chat_logs nu există!")
                # Încearcă să creeze tabela
                print("   🔧 Încerc să creez tabela...")
                await azure_sql_logger._initialize_database()
                print("   ✅ Inițializare completă!")
            
            conn.close()
            
    except Exception as e:
        print(f"   ❌ Eroare la verificarea schemei: {e}")
    
    # Test 5: Test operațiuni ChatLogger
    print("\n5️⃣ Test operațiuni ChatLogger:")
    try:
        test_conversation_id = f"test_conv_{int(time.time())}"
        test_request_id = f"test_req_{int(time.time())}"
        
        print(f"   📝 Test conversation_id: {test_conversation_id}")
        print(f"   📝 Test request_id: {test_request_id}")
        
        # Test chat start
        print("   🚀 Test start_chat_log...")
        chat_logger.start_chat_log(
            request_id=test_request_id,
            question="Test question pentru verificarea logging-ului?",
            user_id="test_user",
            conversation_id=test_conversation_id,
            prompt='{"messages": [{"role": "user", "content": "test message"}]}',
            model_used="test_model",
            temperature=0.7,
            session_id=test_conversation_id
        )
        
        # Așteptăm puțin pentru operațiunile async
        await asyncio.sleep(2)
        
        # Test chat end
        print("   🏁 Test finish_chat_log...")
        chat_logger.finish_chat_log(
            request_id=test_request_id,
            answer="Test answer pentru verificarea logging-ului.",
            tokens_used=100
        )
        
        # Așteptăm puțin pentru operațiunile async
        await asyncio.sleep(2)
        
        # Test feedback
        print("   👍 Test log_feedback...")
        chat_logger.log_feedback(
            conversation_id=test_conversation_id,
            session_id=test_conversation_id,
            feedback="positive",
            feedback_text="Great answer!",
            user_id="test_user",
            answer_index=0,
            request_id=test_request_id
        )
        
        # Așteptăm puțin pentru operațiunile async
        await asyncio.sleep(2)
        
        print("   ✅ Toate operațiunile ChatLogger au fost executate!")
        
    except Exception as e:
        print(f"   ❌ Eroare operațiuni ChatLogger: {e}")
        import traceback
        print(f"   📍 Traceback: {traceback.format_exc()}")
    
    # Test 6: Verifică datele în baza de date
    print("\n6️⃣ Test verificare date în baza de date:")
    try:
        if PYODBC_AVAILABLE and azure_sql_logger.connection_string:
            import pyodbc
            conn = pyodbc.connect(azure_sql_logger.connection_string)
            cursor = conn.cursor()
            
            # Verificăm dacă înregistrarea a fost salvată
            cursor.execute("""
                SELECT COUNT(*) as count_records 
                FROM chat_logs 
                WHERE conversation_id = ? AND request_id = ?
            """, (test_conversation_id, test_request_id))
            
            count_records = cursor.fetchone()[0]
            print(f"   📊 Înregistrări găsite pentru test: {count_records}")
            
            if count_records > 0:
                print("   ✅ Datele au fost salvate în baza de date!")
                
                # Afișăm detaliile înregistrării
                cursor.execute("""
                    SELECT question, answer, feedback, feedback_text, timestamp_start, timestamp_end
                    FROM chat_logs 
                    WHERE conversation_id = ? AND request_id = ?
                """, (test_conversation_id, test_request_id))
                
                row = cursor.fetchone()
                if row:
                    print(f"   📋 Detalii înregistrare:")
                    print(f"      Question: {row[0]}")
                    print(f"      Answer: {row[1]}")
                    print(f"      Feedback: {row[2]}")
                    print(f"      Feedback Text: {row[3]}")
                    print(f"      Start: {row[4]}")
                    print(f"      End: {row[5]}")
            else:
                print("   ⚠️ Nu s-au găsit înregistrări în baza de date!")
                print("   💡 Verificați dacă operațiunile async s-au executat complet.")
            
            conn.close()
            
    except Exception as e:
        print(f"   ❌ Eroare la verificarea datelor: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 TESTAREA S-A FINALIZAT!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("🚀 Începe testarea sistemului de logging...")
    
    try:
        # Rulăm testele
        success = asyncio.run(test_database_connection())
        
        if success:
            print("\n🎯 REZULTAT: Testele s-au finalizat!")
            sys.exit(0)
        else:
            print("\n💥 REZULTAT: Unele teste au eșuat!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test întrerupt de utilizator.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Eroare neașteptată: {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        sys.exit(1)
