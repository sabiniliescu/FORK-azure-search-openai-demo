import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import asdict
import json
import time
import sys
from dotenv import load_dotenv

# Import opțional pentru pyodbc
try:
    import pyodbc
    PYODBC_AVAILABLE = True
    print("🎉 [DATABASE SUCCESS] pyodbc v{} INSTALAT CU SUCCES! Database logging ACTIVAT! 🎉".format(pyodbc.version), file=sys.stdout)
    print("✅ [DATABASE] Azure SQL Database connectivity: ENABLED", file=sys.stdout)
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False
    print("❌ [DATABASE ERROR] pyodbc NU ESTE INSTALAT! Database logging DEZACTIVAT!", file=sys.stderr)
    print("💡 [DATABASE FIX] Pentru a activa database logging, adăugați 'pyodbc==5.2.0' în requirements.txt și redeploy", file=sys.stderr)

# Încarcă variabilele de mediu la nivel de modul
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
load_dotenv(env_path, override=True)

# Configurarea logger-ului pentru database operations
db_logger = logging.getLogger("database_logger")
db_logger.setLevel(logging.INFO)


class AzureSQLLogger:
    """
    Logger pentru salvarea chat logs în Azure SQL Database.
    Funcționează independent de starea bazei de date - aplicația continuă
    să ruleze chiar dacă baza de date nu este disponibilă.
    """
    
    def __init__(self, enable_db_logging: bool = True):
        # Verifică dacă pyodbc este disponibil
        if not PYODBC_AVAILABLE:
            self.enable_db_logging = False
            self.connection_string = None
            self._log_safely("❌ [DATABASE INIT] pyodbc nu este instalat. Database logging DEZACTIVAT!")
            self._log_safely("💡 [DATABASE FIX] Pentru a activa logging: pip install pyodbc==5.2.0")
            return
            
        self.enable_db_logging = enable_db_logging
        self.connection_string = self._build_connection_string()
        self.connection_retry_count = 3
        self.connection_retry_delay = 5  # secunde - măresc pentru Azure SQL
        self.max_connection_timeout = 30  # secunde - măresc pentru Azure SQL
        
        # Mesaj de confirmare că pyodbc funcționează
        if self.enable_db_logging and self.connection_string:
            self._log_safely("🎉 [DATABASE INIT] pyodbc disponibil! Database logging ACTIVAT!")
            self._log_safely(f"🔗 [DATABASE INIT] Connection string configurat pentru: {os.getenv('AZURE_SQL_SERVER', 'N/A')}")
        
        # Flag pentru a evita spam-ul de erori în log dacă baza de date nu e disponibilă
        self.last_connection_error_time = 0
        self.connection_error_cooldown = 300  # 5 minute
        
        # Inițializarea bazei de date (creare tabelă dacă nu există)
        if self.enable_db_logging and self.connection_string:
            self._schedule_safe_task(self._initialize_database())
    
    def _detect_odbc_driver(self) -> Optional[str]:
        """Detectează cel mai recent driver ODBC SQL Server disponibil"""
        try:
            available_drivers = pyodbc.drivers()
            
            # Lista de driver-i în ordinea preferinței (cel mai nou primul)
            preferred_drivers = [
                "ODBC Driver 18 for SQL Server",
                "ODBC Driver 17 for SQL Server", 
                "ODBC Driver 13 for SQL Server",
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server"
            ]
            
            # Găsește primul driver disponibil din lista preferată
            for driver in preferred_drivers:
                if driver in available_drivers:
                    self._log_safely(f"[DATABASE] Driver ODBC detectat: {driver}")
                    return driver
            
            self._log_safely("[DATABASE] Nu s-a găsit niciun driver ODBC SQL Server compatibil!")
            return None
            
        except Exception as e:
            self._log_safely(f"[DATABASE] Eroare la detectarea driver-ului ODBC: {e}")
            return None

    def _build_connection_string(self) -> Optional[str]:
        """Construiește connection string-ul pentru Azure SQL Database"""
        try:
            # Detectează driver-ul ODBC disponibil
            odbc_driver = self._detect_odbc_driver()
            if not odbc_driver:
                self._log_safely("[DATABASE] Nu s-a găsit niciun driver ODBC compatibil. Database logging dezactivat.")
                return None
            
            server = os.getenv("AZURE_SQL_SERVER", "mihaiweb.database.windows.net")
            database = os.getenv("AZURE_SQL_DATABASE", "MihAI_Web_logs")
            username = os.getenv("AZURE_SQL_USERNAME", "")
            password = os.getenv("AZURE_SQL_PASSWORD", "")
            
            if not username or not password:
                self._log_safely("[DATABASE] AZURE_SQL_USERNAME sau AZURE_SQL_PASSWORD nu sunt configurate. Database logging dezactivat.")
                return None
            
            # Asigură-te că avem timeout setat înainte de a-l folosi
            if not hasattr(self, 'max_connection_timeout'):
                self.max_connection_timeout = 30  # Măresc timeout-ul pentru Azure SQL
            
            connection_string = (
                f"DRIVER={{{odbc_driver}}};"
                f"SERVER=tcp:{server},1433;"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout={self.max_connection_timeout};"
            )
            
            self._log_safely(f"[DATABASE] Connection string construit cu driver: {odbc_driver}")
            return connection_string
            
        except Exception as e:
            self._log_safely(f"[DATABASE] Eroare la construirea connection string: {e}")
            return None
    
    def _log_safely(self, message: str):
        """Log message both to logger and stdout"""
        print(message, file=sys.stdout)
        try:
            db_logger.info(message)
        except:
            pass  # Ignore logging errors
    
    def _schedule_safe_task(self, coro):
        """Programează o task asincronă în mod sigur"""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(coro)
        except RuntimeError:
            # Nu există event loop activ, rulează în thread separat
            try:
                import threading
                
                def run_in_thread():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(coro)
                    except Exception as e:
                        self._log_safely(f"[DATABASE] Task background eșuat: {e}")
                    finally:
                        loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                
            except Exception as e:
                self._log_safely(f"[DATABASE] Nu s-a putut programa task-ul: {e}")
    
    async def _initialize_database(self):
        """Inițializează baza de date și creează tabelele necesare"""
        try:
            await asyncio.to_thread(self._create_tables_if_not_exist)
        except Exception as e:
            self._log_safely(f"[DATABASE] Eroare la inițializarea bazei de date: {e}")
    
    def _create_tables_if_not_exist(self):
        """Creează tabelele necesare dacă nu există"""
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_logs' AND xtype='U')
        CREATE TABLE chat_logs (
            id BIGINT IDENTITY(1,1) PRIMARY KEY,
            conversation_id NVARCHAR(255) NOT NULL,
            request_id NVARCHAR(255) NULL,
            question NVARCHAR(MAX) NULL,
            answer NVARCHAR(MAX) NULL,
            timestamp_start DATETIME2 NOT NULL,
            timestamp_start_streaming DATETIME2 NULL,
            timestamp_end DATETIME2 NULL,
            feedback NVARCHAR(50) NULL,
            feedback_text NVARCHAR(MAX) NULL,
            user_id NVARCHAR(255) NULL,
            model_used NVARCHAR(255) NULL,
            temperature FLOAT NULL,
            agentic_retrival_total_token_usage INT NULL,
            prompt_total_token_usage NVARCHAR(MAX) NULL,
            extra_info_thoughts NVARCHAR(MAX) NULL,
            agentic_retrival_duration_seconds FLOAT NULL,
            total_duration_seconds FLOAT NULL
        );
        
        -- Add new columns if they don't exist (for existing tables)
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'timestamp_start_streaming')
            ALTER TABLE chat_logs ADD timestamp_start_streaming DATETIME2 NULL;
            
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'agentic_retrival_total_token_usage')
            ALTER TABLE chat_logs ADD agentic_retrival_total_token_usage INT NULL;
            
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'prompt_total_token_usage')
            ALTER TABLE chat_logs ADD prompt_total_token_usage NVARCHAR(MAX) NULL;
            
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'extra_info_thoughts')
            ALTER TABLE chat_logs ADD extra_info_thoughts NVARCHAR(MAX) NULL;
            
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'agentic_retrival_duration_seconds')
            ALTER TABLE chat_logs ADD agentic_retrival_duration_seconds FLOAT NULL;
            
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'total_duration_seconds')
            ALTER TABLE chat_logs ADD total_duration_seconds FLOAT NULL;
        
        -- Remove old columns if they exist
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'prompt_text')
            ALTER TABLE chat_logs DROP COLUMN prompt_text;
            
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'tokens_used')
            ALTER TABLE chat_logs DROP COLUMN tokens_used;
            
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'duration_seconds')
            ALTER TABLE chat_logs DROP COLUMN duration_seconds;
            
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chat_logs') AND name = 'created_at')
            ALTER TABLE chat_logs DROP COLUMN created_at;
        
        -- Index pentru căutare rapidă după conversation_id
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_chat_logs_conversation_id')
        CREATE INDEX IX_chat_logs_conversation_id ON chat_logs(conversation_id);
        
        -- Index pentru căutare după user_id
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_chat_logs_user_id')
        CREATE INDEX IX_chat_logs_user_id ON chat_logs(user_id);
        
        -- Index pentru căutare după timestamp
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_chat_logs_timestamp_start')
        CREATE INDEX IX_chat_logs_timestamp_start ON chat_logs(timestamp_start);
        """
        
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string, timeout=self.max_connection_timeout)
            cursor = connection.cursor()
            cursor.execute(create_table_sql)
            connection.commit()
            self._log_safely("🎉 [DATABASE SUCCESS] Tabela chat_logs verificată/creată cu succes")
            self._log_safely("✅ [DATABASE] pyodbc + Azure SQL Database funcționează perfect!")
            
        except Exception as e:
            self._log_safely(f"❌ [DATABASE ERROR] Eroare la crearea tabelei: {e}")
            
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass
    
    def _should_log_connection_error(self) -> bool:
        """Verifică dacă ar trebui să logeze o eroare de conexiune (evită spam-ul)"""
        current_time = time.time()
        if current_time - self.last_connection_error_time > self.connection_error_cooldown:
            self.last_connection_error_time = current_time
            return True
        return False
    
    async def _execute_with_retry(self, sql: str, params: tuple) -> bool:
        """Execută SQL cu retry logic"""
        if not PYODBC_AVAILABLE or not self.enable_db_logging or not self.connection_string:
            return False
        
        for attempt in range(self.connection_retry_count):
            try:
                await asyncio.to_thread(self._execute_sql, sql, params)
                return True
                
            except Exception as e:
                if attempt == self.connection_retry_count - 1:
                    # Ultima încercare eșuată
                    if self._should_log_connection_error():
                        self._log_safely(f"[DATABASE] Toate încercările de conectare au eșuat: {e}")
                    return False
                else:
                    # Încearcă din nou după delay
                    await asyncio.sleep(self.connection_retry_delay * (attempt + 1))
        
        return False
    
    def _execute_sql(self, sql: str, params: tuple):
        """Execută SQL sincrn în thread-ul de background"""
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string, timeout=self.max_connection_timeout)
            cursor = connection.cursor()
            cursor.execute(sql, params)
            connection.commit()
            
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass
    
    async def log_chat_start(
        self,
        conversation_id: str,
        request_id: str,
        question: str,
        user_id: Optional[str],
        extra_info_thoughts: str,
        agentic_retrival_total_token_usage: Optional[int] = None,
        prompt_total_token_usage: Optional[str] = None,
        model_used: Optional[str] = None,
        temperature: Optional[float] = None,
        timestamp_start: Optional[datetime] = None,
        timestamp_start_streaming: Optional[datetime] = None
    ) -> bool:
        """
        Loghează începutul unei conversații
        Returnează True dacă operația a reușit, False altfel
        """
        if timestamp_start is None:
            timestamp_start = datetime.now()
        
        insert_sql = """
        INSERT INTO chat_logs (
            conversation_id, request_id, question, user_id, extra_info_thoughts,
            agentic_retrival_total_token_usage, prompt_total_token_usage, 
            model_used, temperature, timestamp_start, timestamp_start_streaming
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            conversation_id,
            request_id,
            question,
            user_id,
            extra_info_thoughts,
            agentic_retrival_total_token_usage,
            prompt_total_token_usage,
            model_used,
            temperature,
            timestamp_start,
            timestamp_start_streaming
        )
        
        success = await self._execute_with_retry(insert_sql, params)
        if success:
            self._log_safely(f"🎉 [DATABASE SUCCESS] Chat start logged pentru request_id: {request_id}")
            self._log_safely("✅ [DATABASE] pyodbc funcționează perfect! Toate operațiunile sunt salvate în Azure SQL!")
        
        return success
    
    async def log_chat_end(
        self,
        request_id: str,
        answer: str,
        agentic_retrival_duration_seconds: Optional[float] = None,
        timestamp_end: Optional[datetime] = None
    ) -> bool:
        """
        Actualizează log-ul cu răspunsul și sfârșitul conversației
        Returnează True dacă operația a reușit, False altfel
        """
        if timestamp_end is None:
            timestamp_end = datetime.now()
        
        update_sql = """
        UPDATE chat_logs 
        SET answer = ?, 
            agentic_retrival_duration_seconds = ?, 
            timestamp_end = ?
        WHERE request_id = ?
        """
        
        params = (answer, agentic_retrival_duration_seconds, timestamp_end, request_id)
        
        success = await self._execute_with_retry(update_sql, params)
        if success:
            self._log_safely(f"[DATABASE] Chat end logged pentru request_id: {request_id}")
        
        return success
    
    async def log_chat_end_with_tokens(
        self,
        request_id: str,
        answer: str,
        agentic_retrival_duration_seconds: Optional[float] = None,
        timestamp_end: Optional[datetime] = None,
        prompt_total_token_usage: Optional[str] = None,
        total_duration_seconds: Optional[float] = None
    ) -> bool:
        """
        Actualizează log-ul cu răspunsul, sfârșitul conversației și token usage-ul final
        Returnează True dacă operația a reușit, False altfel
        """
        if timestamp_end is None:
            timestamp_end = datetime.now()
        
        update_sql = """
        UPDATE chat_logs 
        SET answer = ?, 
            agentic_retrival_duration_seconds = ?, 
            timestamp_end = ?,
            prompt_total_token_usage = ?,
            total_duration_seconds = ?
        WHERE request_id = ?
        """
        
        params = (answer, agentic_retrival_duration_seconds, timestamp_end, prompt_total_token_usage, total_duration_seconds, request_id)
        
        success = await self._execute_with_retry(update_sql, params)
        if success:
            self._log_safely(f"[DATABASE] Chat end with tokens logged pentru request_id: {request_id}")
        
        return success
    
    async def log_streaming_start(
        self,
        request_id: str,
        timestamp_start_streaming: Optional[datetime] = None
    ) -> bool:
        """
        Actualizează log-ul cu timestamp-ul de început al streaming-ului
        Returnează True dacă operația a reușit, False altfel
        """
        if timestamp_start_streaming is None:
            timestamp_start_streaming = datetime.now()
        
        update_sql = """
        UPDATE chat_logs 
        SET timestamp_start_streaming = ?
        WHERE request_id = ?
        """
        
        params = (timestamp_start_streaming, request_id)
        
        success = await self._execute_with_retry(update_sql, params)
        if success:
            self._log_safely(f"[DATABASE] Streaming start logged pentru request_id: {request_id}")
        
        return success
    
    async def log_feedback(
        self,
        conversation_id: str,
        feedback: str,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Loghează feedback-ul utilizatorului
        Poate crea o înregistrare nouă sau poate actualiza ultima înregistrare pentru conversation_id
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Dacă avem request_id, actualizează înregistrarea specifică
        if request_id:
            update_sql = """
            UPDATE chat_logs 
            SET feedback = ?, 
                feedback_text = ?
            WHERE request_id = ?
            """
            params = (feedback, feedback_text, request_id)
            
            success = await self._execute_with_retry(update_sql, params)
            if success:
                self._log_safely(f"[DATABASE] Feedback logged pentru request_id: {request_id}")
                return success
        
        # Fallback: încearcă să actualizeze ultima înregistrare pentru această conversație
        update_sql = """
        UPDATE chat_logs 
        SET feedback = ?, 
            feedback_text = ?
        WHERE conversation_id = ? 
        AND id = (SELECT MAX(id) FROM chat_logs WHERE conversation_id = ?)
        """
        
        params = (feedback, feedback_text, conversation_id, conversation_id)
        
        success = await self._execute_with_retry(update_sql, params)
        if success:
            self._log_safely(f"[DATABASE] Feedback logged pentru conversation_id: {conversation_id} (fallback)")
        else:
            # Dacă actualizarea nu a reușit, creează o înregistrare nouă doar pentru feedback
            insert_sql = """
            INSERT INTO chat_logs (
                conversation_id, feedback, feedback_text, user_id, timestamp_start
            ) VALUES (?, ?, ?, ?, ?)
            """
            
            feedback_params = (conversation_id, feedback, feedback_text, user_id, timestamp)
            success = await self._execute_with_retry(insert_sql, feedback_params)
            if success:
                self._log_safely(f"[DATABASE] Feedback înregistrare nouă creată pentru conversation_id: {conversation_id}")
        
        return success
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list:
        """
        Recuperează istoricul unei conversații din baza de date
        """
        if not self.enable_db_logging or not self.connection_string:
            return []
        
        select_sql = """
        SELECT TOP (?) 
            id, conversation_id, request_id, question, answer, 
            timestamp_start, timestamp_start_streaming, timestamp_end, feedback, feedback_text,
            user_id, model_used, temperature,
            agentic_retrival_total_token_usage, prompt_total_token_usage,
            extra_info_thoughts, agentic_retrival_duration_seconds, created_at
        FROM chat_logs 
        WHERE conversation_id = ?
        ORDER BY timestamp_start DESC
        """
        
        try:
            result = await asyncio.to_thread(self._fetch_data, select_sql, (limit, conversation_id))
            self._log_safely(f"[DATABASE] Recuperat {len(result)} înregistrări pentru conversation_id: {conversation_id}")
            return result
            
        except Exception as e:
            if self._should_log_connection_error():
                self._log_safely(f"[DATABASE] Eroare la recuperarea istoricului: {e}")
            return []
    
    def _fetch_data(self, sql: str, params: tuple) -> list:
        """Recuperează date din baza de date sincrn"""
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string, timeout=self.max_connection_timeout)
            cursor = connection.cursor()
            cursor.execute(sql, params)
            
            # Convertește rows în dicționare
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    column_name = columns[i]
                    # Convertește datetime în string pentru JSON serialization
                    if isinstance(value, datetime):
                        row_dict[column_name] = value.isoformat()
                    else:
                        row_dict[column_name] = value
                result.append(row_dict)
            
            return result
            
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass


# Instanță globală pentru database logger
azure_sql_logger = AzureSQLLogger(enable_db_logging=True)
