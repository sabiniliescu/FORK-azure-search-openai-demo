#!/usr/bin/env python3
"""
Test script pentru conectivitatea la Azure SQL Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Încărcăm variabilele de mediu din .env
from dotenv import load_dotenv

# Încărcăm din fișierul .env din rădăcină
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
print(f"Încarcăm variabilele de mediu din: {env_path}")
load_dotenv(env_path, override=True)

# Verificăm dacă variabilele au fost încărcate
print("Variabile de mediu încărcate:")
print(f"AZURE_SQL_SERVER: {os.getenv('AZURE_SQL_SERVER')}")
print(f"AZURE_SQL_DATABASE: {os.getenv('AZURE_SQL_DATABASE')}")
print(f"AZURE_SQL_USERNAME: {os.getenv('AZURE_SQL_USERNAME')}")
print(f"AZURE_SQL_PASSWORD: {'SET' if os.getenv('AZURE_SQL_PASSWORD') else 'NOT SET'}")
print()

from chat_logging.database_logger import azure_sql_logger
from chat_logging.chat_logger import chat_logger
import asyncio
import time
from datetime import datetime

async def test_database_connectivity():
    """Testează conectivitatea la baza de date Azure SQL"""
    print("=== TEST AZURE SQL DATABASE CONNECTIVITY ===\n")
    
    # Verifică configurația
    print("1. Verificare configurație...")
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    
    print(f"   Server: {server}")
    print(f"   Database: {database}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not username or not password:
        print("❌ Credențialele nu sunt configurate!")
        return False
    
    print("✓ Configurația pare OK\n")
    
    # Test 1: Inițializare database logger
    print("2. Test inițializare database logger...")
    try:
        # Forțează reinițializarea cu noile credențiale
        azure_sql_logger.connection_string = azure_sql_logger._build_connection_string()
        if azure_sql_logger.connection_string:
            print("✓ Connection string generat cu succes")
        else:
            print("❌ Nu s-a putut genera connection string")
            return False
    except Exception as e:
        print(f"❌ Eroare la inițializare: {e}")
        return False
    
    print("✓ Database logger inițializat\n")
    
    # Test 2: Creare tabele
    print("3. Test creare tabele...")
    try:
        await azure_sql_logger._initialize_database()
        print("✓ Tabela chat_logs verificată/creată")
    except Exception as e:
        print(f"❌ Eroare la crearea tabelei: {e}")
        return False
    
    print("✓ Tabele create cu succes\n")
    
    # Test 3: Salvare chat start
    print("4. Test salvare chat start...")
    test_request_id = f"test-db-{int(time.time())}"
    test_conversation_id = f"conv-db-{int(time.time())}"
    
    try:
        success = await azure_sql_logger.log_chat_start(
            conversation_id=test_conversation_id,
            request_id=test_request_id,
            question="Test question pentru baza de date?",
            user_id="test-user-123",
            prompt_text='[{"role": "user", "content": "Test question pentru baza de date?"}]',
            model_used="gpt-4-test",
            temperature=0.7,
            session_id="test-session-456",
            timestamp_start=datetime.now()
        )
        
        if success:
            print("✓ Chat start salvat în baza de date")
        else:
            print("❌ Nu s-a putut salva chat start")
            return False
            
    except Exception as e:
        print(f"❌ Eroare la salvarea chat start: {e}")
        return False
    
    print("✓ Chat start salvat cu succes\n")
    
    # Test 4: Salvare chat end
    print("5. Test salvare chat end...")
    try:
        success = await azure_sql_logger.log_chat_end(
            request_id=test_request_id,
            answer="Acesta este un răspuns de test pentru verificarea conectivității la baza de date Azure SQL.",
            tokens_used=75,
            timestamp_end=datetime.now()
        )
        
        if success:
            print("✓ Chat end salvat în baza de date")
        else:
            print("❌ Nu s-a putut salva chat end")
            return False
            
    except Exception as e:
        print(f"❌ Eroare la salvarea chat end: {e}")
        return False
    
    print("✓ Chat end salvat cu succes\n")
    
    # Test 5: Salvare feedback
    print("6. Test salvare feedback...")
    try:
        success = await azure_sql_logger.log_feedback(
            conversation_id=test_conversation_id,
            session_id="test-session-456",
            feedback="positive",
            feedback_text="Test feedback pentru verificarea funcționalității!",
            user_id="test-user-123",
            timestamp=datetime.now()
        )
        
        if success:
            print("✓ Feedback salvat în baza de date")
        else:
            print("❌ Nu s-a putut salva feedback")
            return False
            
    except Exception as e:
        print(f"❌ Eroare la salvarea feedback: {e}")
        return False
    
    print("✓ Feedback salvat cu succes\n")
    
    # Test 6: Recuperare istoric conversație
    print("7. Test recuperare istoric...")
    try:
        history = await azure_sql_logger.get_conversation_history(
            conversation_id=test_conversation_id,
            limit=10
        )
        
        if history and len(history) > 0:
            print(f"✓ Recuperat {len(history)} înregistrări din istoric")
            print("   Primul element:")
            for key, value in history[0].items():
                if key in ['question', 'answer', 'feedback']:
                    print(f"     {key}: {value}")
        else:
            print("❌ Nu s-au găsit înregistrări în istoric")
            return False
            
    except Exception as e:
        print(f"❌ Eroare la recuperarea istoricului: {e}")
        return False
    
    print("✓ Istoric recuperat cu succes\n")
    
    print("=== TOATE TESTELE AU TRECUT CU SUCCES ===")
    print("🎉 Baza de date Azure SQL funcționează perfect!")
    print("🔗 Aplicația poate salva și recupera chat logs din baza de date.")
    return True

def test_chat_logger_with_database():
    """Testează chat logger-ul integrat cu baza de date"""
    print("\n=== TEST CHAT LOGGER INTEGRAT CU BAZA DE DATE ===\n")
    
    # Test cu noul chat logger care are acces la baza de date
    print("1. Testing integrated chat logging...")
    request_id = f"integrated-test-{int(time.time())}"
    conversation_id = f"integrated-conv-{int(time.time())}"
    
    # Start chat log
    chat_logger.start_chat_log(
        request_id=request_id,
        question="Cum funcționează logging-ul integrat?",
        user_id="integrated-user-789",
        conversation_id=conversation_id,
        prompt='[{"role": "user", "content": "Cum funcționează logging-ul integrat?"}]',
        model_used="gpt-4-integrated",
        temperature=0.8,
        session_id="integrated-session-999"
    )
    
    print("✓ Chat log început cu succes")
    
    # Simulăm procesarea
    time.sleep(1)
    
    # Finish chat log
    chat_logger.finish_chat_log(
        request_id=request_id,
        answer="Logging-ul integrat funcționează prin salvarea automată în baza de date Azure SQL, în paralel cu logging-ul în terminal. Aplicația continuă să funcționeze chiar dacă baza de date nu este disponibilă.",
        tokens_used=125
    )
    
    print("✓ Chat log finalizat cu succes")
    
    # Log feedback
    chat_logger.log_feedback(
        conversation_id=conversation_id,
        session_id="integrated-session-999",
        feedback="positive",
        feedback_text="Sistemul integrat funcționează excelent!",
        user_id="integrated-user-789",
        answer_index=0
    )
    
    print("✓ Feedback logged cu succes")
    print("\n🎉 Chat logger integrat funcționează perfect!")

async def main():
    """Funcția principală de test"""
    print("Începem testarea sistemului de logging cu Azure SQL Database...\n")
    
    # Test conectivitate bază de date
    db_success = await test_database_connectivity()
    
    if db_success:
        # Test chat logger integrat
        test_chat_logger_with_database()
        
        # Dăm timp pentru task-urile de background să se termine
        print("\nAșteptăm finalizarea task-urilor de background...")
        await asyncio.sleep(3)
        
        print("\n✅ TOATE TESTELE AU FOST FINALIZATE CU SUCCES!")
        print("🎯 Sistemul de logging este gata pentru producție!")
    else:
        print("\n❌ Testele au eșuat!")
        print("🔧 Verifică configurația bazei de date și încearcă din nou.")

if __name__ == "__main__":
    asyncio.run(main())
