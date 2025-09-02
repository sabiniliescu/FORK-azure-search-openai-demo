import json
import time
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import asyncio
from .database_logger import azure_sql_logger


@dataclass
class ChatLogEntry:
    """Data class pentru o înregistrare de logging pentru chat"""
    question: str
    answer: str
    user_id: Optional[str]
    conversation_id: str
    prompt: str
    timestamp_start: datetime
    timestamp_end: Optional[datetime]
    tokens_used: Optional[int]
    feedback: Optional[str] = None
    feedback_text: Optional[str] = None
    model_used: Optional[str] = None
    temperature: Optional[float] = None


class ChatLogger:
    """Logger pentru capturarea și salvarea informațiilor de chat"""
    
    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
        self.active_logs: Dict[str, ChatLogEntry] = {}  # Pentru tracking log-urile active
    
    def start_chat_log(
        self,
        request_id: str,
        question: str,
        user_id: Optional[str],
        conversation_id: str,
        prompt: str,
        model_used: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> None:
        """Începe logging-ul pentru o cerere de chat"""
        if not self.enable_logging:
            return
        
        log_entry = ChatLogEntry(
            question=question,
            answer="",  # Va fi completat la finish_chat_log
            user_id=user_id,
            conversation_id=conversation_id,
            prompt=prompt,
            timestamp_start=datetime.now(),
            timestamp_end=None,
            tokens_used=None,
            model_used=model_used,
            temperature=temperature
        )
        
        self.active_logs[request_id] = log_entry
        
        # Log în terminal - doar informațiile care se salvează în DB
        print(f"\n[DB LOG] 📝 Chat Start | ID: {request_id}")
        print(f"  Conversation: {conversation_id}")
        print(f"  User: {user_id or 'Anonymous'}")
        print(f"  Model: {model_used or 'Unknown'}")
        print(f"  Question: {question[:100]}{'...' if len(question) > 100 else ''}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_chat_start_to_db(
            conversation_id=conversation_id,
            request_id=request_id,
            question=question,
            user_id=user_id,
            prompt_text=prompt,
            model_used=model_used,
            temperature=temperature,
            timestamp_start=log_entry.timestamp_start
        ))
    
    def finish_chat_log(
        self,
        request_id: str,
        answer: str,
        tokens_used: Optional[int] = None
    ) -> None:
        """Finalizează logging-ul pentru o cerere de chat"""
        if not self.enable_logging or request_id not in self.active_logs:
            return
        
        log_entry = self.active_logs[request_id]
        log_entry.answer = answer
        log_entry.timestamp_end = datetime.now()
        log_entry.tokens_used = tokens_used
        
        # Calculează durata
        duration = (log_entry.timestamp_end - log_entry.timestamp_start).total_seconds()
        
        # Log în terminal - doar informațiile care se salvează în DB
        print(f"[DB LOG] ✅ Chat End | ID: {request_id}")
        print(f"  Duration: {duration:.2f}s | Tokens: {tokens_used or 'N/A'}")
        print(f"  Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
        
        # Salvează log-ul complet (pentru acum doar în terminal)
        self._save_complete_log(log_entry)
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_chat_end_to_db(
            request_id=request_id,
            answer=answer,
            tokens_used=tokens_used,
            timestamp_end=log_entry.timestamp_end
        ))
        
        # Curăță din active logs
        del self.active_logs[request_id]
    
    def log_feedback(
        self,
        conversation_id: str,
        feedback: str,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None,
        answer_index: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Loghează feedback-ul utilizatorului"""
        if not self.enable_logging:
            return
        
        timestamp = datetime.now()
        
        # Log în terminal - doar informațiile care se salvează în DB
        print(f"[DB LOG] 👍 Feedback | {feedback.upper()}")
        print(f"  Conversation: {conversation_id}")
        print(f"  User: {user_id or 'Anonymous'}")
        if feedback_text:
            print(f"  Text: {feedback_text[:80]}{'...' if len(feedback_text) > 80 else ''}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_feedback_to_db(
            conversation_id=conversation_id,
            feedback=feedback,
            feedback_text=feedback_text,
            user_id=user_id,
            timestamp=timestamp,
            request_id=request_id
        ))
    
    def _save_complete_log(self, log_entry: ChatLogEntry) -> None:
        """Salvează log-ul complet - doar un sumar al datelor din DB"""
        duration = 0
        if log_entry.timestamp_end:
            duration = (log_entry.timestamp_end - log_entry.timestamp_start).total_seconds()
        
        print(f"[DB LOG] 💾 Complete | Conv: {log_entry.conversation_id}")
        print(f"  Q: {log_entry.question[:60]}{'...' if len(log_entry.question) > 60 else ''}")
        print(f"  A: {log_entry.answer[:60]}{'...' if len(log_entry.answer) > 60 else ''}")
        print(f"  Model: {log_entry.model_used} | Duration: {duration:.1f}s | Tokens: {log_entry.tokens_used or 'N/A'}")
        print("")
    
    def _schedule_task(self, coro):
        """Programează o task asincronă, creând un event loop dacă este necesar"""
        try:
            # Încearcă să obții event loop-ul curent
            loop = asyncio.get_running_loop()
            # Dacă avem un loop activ, creează task-ul
            asyncio.create_task(coro)
        except RuntimeError:
            # Nu există un event loop activ, creează unul nou în background
            try:
                def run_in_thread():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(coro)
                    except Exception as e:
                        print(f"[DATABASE ERROR] Task background eșuat: {e}")
                    finally:
                        loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                
            except Exception as e:
                print(f"[DATABASE ERROR] Nu s-a putut programa task-ul: {e}")
    
    async def _save_chat_start_to_db(
        self,
        conversation_id: str,
        request_id: str,
        question: str,
        user_id: Optional[str],
        prompt_text: str,
        model_used: Optional[str],
        temperature: Optional[float],
        timestamp_start: datetime
    ) -> None:
        """Salvează începutul chat-ului în baza de date (asincron)"""
        try:
            await azure_sql_logger.log_chat_start(
                conversation_id=conversation_id,
                request_id=request_id,
                question=question,
                user_id=user_id,
                prompt_text=prompt_text,
                model_used=model_used,
                temperature=temperature,
                timestamp_start=timestamp_start
            )
        except Exception as e:
            # Aplicația continuă să ruleze chiar dacă baza de date nu este disponibilă
            print(f"[DATABASE ERROR] Nu s-a putut salva chat start în DB: {e}")
    
    async def _save_chat_end_to_db(
        self,
        request_id: str,
        answer: str,
        tokens_used: Optional[int],
        timestamp_end: datetime
    ) -> None:
        """Salvează sfârșitul chat-ului în baza de date (asincron)"""
        try:
            await azure_sql_logger.log_chat_end(
                request_id=request_id,
                answer=answer,
                tokens_used=tokens_used,
                timestamp_end=timestamp_end
            )
        except Exception as e:
            # Aplicația continuă să ruleze chiar dacă baza de date nu este disponibilă
            print(f"[DATABASE ERROR] Nu s-a putut salva chat end în DB: {e}")
    
    async def _save_feedback_to_db(
        self,
        conversation_id: str,
        feedback: str,
        feedback_text: Optional[str],
        user_id: Optional[str],
        timestamp: datetime,
        request_id: Optional[str] = None
    ) -> None:
        """Salvează feedback-ul în baza de date (asincron)"""
        try:
            await azure_sql_logger.log_feedback(
                conversation_id=conversation_id,
                feedback=feedback,
                feedback_text=feedback_text,
                user_id=user_id,
                timestamp=timestamp,
                request_id=request_id
            )
        except Exception as e:
            # Aplicația continuă să ruleze chiar dacă baza de date nu este disponibilă
            print(f"[DATABASE ERROR] Nu s-a putut salva feedback în DB: {e}")


# Instanță globală pentru logger
chat_logger = ChatLogger(enable_logging=True)
