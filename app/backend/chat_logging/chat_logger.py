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
    session_id: Optional[str] = None


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
        temperature: Optional[float] = None,
        session_id: Optional[str] = None
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
            temperature=temperature,
            session_id=session_id
        )
        
        self.active_logs[request_id] = log_entry
        
        # Log în terminal
        print(f"\n{'='*80}")
        print(f"[CHAT LOG START] Request ID: {request_id}")
        print(f"[CHAT LOG] Timestamp Start: {log_entry.timestamp_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[CHAT LOG] User ID: {user_id}")
        print(f"[CHAT LOG] Conversation ID: {conversation_id}")
        print(f"[CHAT LOG] Session ID: {session_id}")
        print(f"[CHAT LOG] Model: {model_used}")
        print(f"[CHAT LOG] Temperature: {temperature}")
        print(f"[CHAT LOG] Question: {question}")
        print(f"[CHAT LOG] Prompt Length: {len(prompt)} chars")
        
        # Afișăm preview-ul prompt-ului într-un format mai citibil
        try:
            prompt_obj = json.loads(prompt) if isinstance(prompt, str) else prompt
            if isinstance(prompt_obj, list) and len(prompt_obj) > 0:
                # Afișăm doar ultimul mesaj pentru preview
                last_message = prompt_obj[-1].get("content", "")
                # Luăm primele 300 de caractere pentru preview
                preview_text = last_message[:300] + "..." if len(last_message) > 300 else last_message
                # Înlocuim \\n cu newlines reale
                formatted_preview = preview_text.replace('\\n', '\n')
                print(f"[CHAT LOG] Last Message Preview:")
                for line in formatted_preview.split('\n'):
                    print(f"    {line}")
            else:
                print(f"[CHAT LOG] Prompt Preview: {prompt[:200]}...")
        except (json.JSONDecodeError, AttributeError):
            print(f"[CHAT LOG] Prompt Preview: {str(prompt)[:200]}...")
        
        print(f"{'='*80}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_chat_start_to_db(
            conversation_id=conversation_id,
            request_id=request_id,
            question=question,
            user_id=user_id,
            prompt_text=prompt,
            model_used=model_used,
            temperature=temperature,
            session_id=session_id,
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
        
        # Log în terminal
        print(f"\n{'='*80}")
        print(f"[CHAT LOG END] Request ID: {request_id}")
        print(f"[CHAT LOG] Timestamp End: {log_entry.timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[CHAT LOG] Duration: {duration:.2f} seconds")
        print(f"[CHAT LOG] Tokens Used: {tokens_used}")
        print(f"[CHAT LOG] Answer Length: {len(answer)} chars")
        print(f"[CHAT LOG] Answer Preview:")
        
        # Afișăm răspunsul cu \n interpretate ca line breaks
        answer_preview = answer[:800] + "..." if len(answer) > 800 else answer
        # Gestionăm atât \n real cât și string literal \\n
        formatted_answer = answer_preview.replace('\\n', '\n')
        for line in formatted_answer.split('\n'):
            print(f"    {line}")
        
        print(f"{'='*80}")
        
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
        session_id: Optional[str],
        feedback: str,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None,
        answer_index: Optional[int] = None
    ) -> None:
        """Loghează feedback-ul utilizatorului"""
        if not self.enable_logging:
            return
        
        timestamp = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"[FEEDBACK LOG] Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[FEEDBACK LOG] User ID: {user_id}")
        print(f"[FEEDBACK LOG] Conversation ID: {conversation_id}")
        print(f"[FEEDBACK LOG] Session ID: {session_id}")
        print(f"[FEEDBACK LOG] Answer Index: {answer_index}")
        print(f"[FEEDBACK LOG] Feedback: {feedback}")
        if feedback_text:
            print(f"[FEEDBACK LOG] Feedback Text: {feedback_text}")
        print(f"{'='*80}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_feedback_to_db(
            conversation_id=conversation_id,
            session_id=session_id,
            feedback=feedback,
            feedback_text=feedback_text,
            user_id=user_id,
            timestamp=timestamp
        ))
    
    def _save_complete_log(self, log_entry: ChatLogEntry) -> None:
        """Salvează log-ul complet (pentru acum în terminal)"""
        print(f"\n{'='*100}")
        print("[COMPLETE CHAT LOG]")
        print(f"Question: {log_entry.question}")
        print("Answer:")
        
        # Afișăm răspunsul complet cu \n interpretate ca line breaks
        # Gestionăm atât \n real cât și string literal \\n
        formatted_answer = log_entry.answer.replace('\\n', '\n')
        for line in formatted_answer.split('\n'):
            print(f"    {line}")
        
        print(f"User ID: {log_entry.user_id}")
        print(f"Conversation ID: {log_entry.conversation_id}")
        print(f"Session ID: {log_entry.session_id}")
        print(f"Model: {log_entry.model_used}")
        print(f"Temperature: {log_entry.temperature}")
        print(f"Start Time: {log_entry.timestamp_start}")
        print(f"End Time: {log_entry.timestamp_end}")
        
        if log_entry.timestamp_end:
            duration = (log_entry.timestamp_end - log_entry.timestamp_start).total_seconds()
            print(f"Duration: {duration:.2f} seconds")
        
        print(f"Tokens Used: {log_entry.tokens_used}")
        print(f"Feedback: {log_entry.feedback}")
        print(f"Feedback Text: {log_entry.feedback_text}")
        
        # Afișăm prompt-ul într-un format mai frumos
        print("Prompt (formatted):")
        try:
            prompt_obj = json.loads(log_entry.prompt) if isinstance(log_entry.prompt, str) else log_entry.prompt
            # Afișăm fiecare mesaj separat cu formatare îmbunătățită
            if isinstance(prompt_obj, list):
                for i, message in enumerate(prompt_obj):
                    print(f"  Message {i+1} ({message.get('role', 'unknown')}):")
                    content = message.get('content', '')
                    # Înlocuim \\n cu newlines reale pentru afișare
                    formatted_content = content.replace('\\n', '\n')
                    for line in formatted_content.split('\n'):
                        print(f"    {line}")
                    print()  # Linie goală între mesaje
            else:
                formatted_prompt = json.dumps(prompt_obj, ensure_ascii=False, indent=2)
                print(formatted_prompt)
        except (json.JSONDecodeError, AttributeError):
            print(f"Prompt: {log_entry.prompt}")
        
        print(f"{'='*100}\n")
    
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
        session_id: Optional[str],
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
                session_id=session_id,
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
        session_id: Optional[str],
        feedback: str,
        feedback_text: Optional[str],
        user_id: Optional[str],
        timestamp: datetime
    ) -> None:
        """Salvează feedback-ul în baza de date (asincron)"""
        try:
            await azure_sql_logger.log_feedback(
                conversation_id=conversation_id,
                session_id=session_id,
                feedback=feedback,
                feedback_text=feedback_text,
                user_id=user_id,
                timestamp=timestamp
            )
        except Exception as e:
            # Aplicația continuă să ruleze chiar dacă baza de date nu este disponibilă
            print(f"[DATABASE ERROR] Nu s-a putut salva feedback în DB: {e}")


# Instanță globală pentru logger
chat_logger = ChatLogger(enable_logging=True)
