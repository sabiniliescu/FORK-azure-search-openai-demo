#!/usr/bin/env python3
"""
Test debug pentru variabilele de mediu
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Încărcăm variabilele de mediu
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
print(f"Încarcăm .env din: {env_path}")
load_dotenv(env_path, override=True)

print("\n=== VARIABILE DE MEDIU ===")
print(f"AZURE_SQL_SERVER: '{os.getenv('AZURE_SQL_SERVER')}'")
print(f"AZURE_SQL_DATABASE: '{os.getenv('AZURE_SQL_DATABASE')}'")
print(f"AZURE_SQL_USERNAME: '{os.getenv('AZURE_SQL_USERNAME')}'")
print(f"AZURE_SQL_PASSWORD: '{os.getenv('AZURE_SQL_PASSWORD')}'")

# Test import database logger
print("\n=== TEST IMPORT DATABASE LOGGER ===")
try:
    from chat_logging.database_logger import azure_sql_logger
    print("✓ Database logger importat cu succes")
    print(f"Connection string: {azure_sql_logger.connection_string[:100]}...")
except Exception as e:
    print(f"❌ Eroare la import: {e}")
