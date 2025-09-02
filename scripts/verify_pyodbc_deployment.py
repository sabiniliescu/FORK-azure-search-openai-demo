#!/usr/bin/env python3
"""
Script pentru verificarea automată a instalării pyodbc în Azure după deploy
"""

import requests
import time
import sys
import json
from datetime import datetime

def check_pyodbc_deployment():
    """Verifică dacă pyodbc a fost instalat cu succes în Azure"""
    
    backend_url = "https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io"
    
    print("🔍 Verificarea instalării pyodbc în Azure...")
    print(f"📡 Backend URL: {backend_url}")
    print()
    
    # Test 1: Verifică dacă aplicația răspunde
    print("1️⃣ Test conectivitate aplicație...")
    try:
        response = requests.get(f"{backend_url}/config", timeout=30)
        if response.status_code == 200:
            print("   ✅ Aplicația răspunde!")
        else:
            print(f"   ⚠️ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Eroare conectivitate: {e}")
        print("   ⏳ Aplicația poate să nu fie încă gata. Încearcă din nou în 1-2 minute.")
        return False
    
    # Test 2: Fă un chat test pentru a declanșa logging-ul
    print("\n2️⃣ Test chat pentru a declanșa logging-ul...")
    try:
        chat_payload = {
            "messages": [
                {
                    "role": "user", 
                    "content": "Test pyodbc deployment - spune doar 'OK'"
                }
            ],
            "context": {
                "overrides": {
                    "temperature": 0.1
                }
            }
        }
        
        response = requests.post(
            f"{backend_url}/chat", 
            json=chat_payload, 
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("   ✅ Chat test trimis cu succes!")
            print("   📝 Acest chat ar trebui să declanșeze logging-ul database")
            
            # Așteaptă puțin pentru logging
            print("   ⏳ Așteaptă 5 secunde pentru procesarea logging-ului...")
            time.sleep(5)
            
        else:
            print(f"   ⚠️ Chat test status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Eroare chat test: {e}")
    
    # Instrucțiuni pentru verificare manuală
    print("\n3️⃣ Verificare manuală în Azure Portal:")
    print("   🔗 Deschide: https://portal.azure.com")
    print("   📂 Navighează la: Container Apps > capps-backend-xxx")
    print("   📋 Mergi la: Monitoring > Log stream")
    print()
    print("   🔍 Caută aceste mesaje în log-uri:")
    print()
    print("   ✅ SUCCES (pyodbc instalat):")
    print("      🎉 [DATABASE SUCCESS] pyodbc v5.2.0 INSTALAT CU SUCCES!")
    print("      ✅ [DATABASE] Azure SQL Database connectivity: ENABLED")
    print("      🎉 [DATABASE SUCCESS] Chat start logged pentru request_id: xxx")
    print()
    print("   ❌ EȘEC (pyodbc nu este instalat):")
    print("      ❌ [DATABASE ERROR] pyodbc NU ESTE INSTALAT!")
    print("      ❌ [DATABASE INIT] pyodbc nu este instalat. Database logging DEZACTIVAT!")
    print()
    
    # Test 3: Ghid pentru verificare completă
    print("4️⃣ Test complet recomandat:")
    print(f"   1. Deschide aplicația: {backend_url}")
    print("   2. Fă un chat în interfața web")
    print("   3. Verifică log-urile Azure în timp real")
    print("   4. Căută mesajele de SUCCESS în log-uri")
    print()
    
    print("✅ Verificarea s-a completat!")
    print("💡 Dacă vezi mesajele de SUCCESS în log-urile Azure, pyodbc funcționează!")
    
    return True

if __name__ == "__main__":
    print("🚀 Începe verificarea pyodbc deployment...")
    print("=" * 70)
    
    try:
        success = check_pyodbc_deployment()
        if success:
            print("\n🎯 Script completat! Verifică manual log-urile Azure pentru confirmare.")
        else:
            print("\n💥 Au fost probleme. Încearcă din nou în câteva minute.")
    except KeyboardInterrupt:
        print("\n🛑 Verificare întreruptă.")
    except Exception as e:
        print(f"\n💥 Eroare neașteptată: {e}")
