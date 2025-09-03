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
    extra_info_thoughts: str
    timestamp_start: datetime
    timestamp_end: Optional[datetime]
    feedback: Optional[str] = None
    feedback_text: Optional[str] = None
    model_used: Optional[str] = None
    temperature: Optional[float] = None
    agentic_retrival_total_token_usage: Optional[int] = None
    prompt_total_token_usage: Optional[str] = None
    timestamp_start_streaming: Optional[datetime] = None
    agentic_retrival_duration_seconds: Optional[float] = None


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
        extra_info_thoughts: str,
        agentic_retrival_total_token_usage: Optional[int] = None,
        prompt_total_token_usage: Optional[str] = None,
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
            extra_info_thoughts=extra_info_thoughts,
            timestamp_start=datetime.now(),
            timestamp_end=None,
            model_used=model_used,
            temperature=temperature,
            agentic_retrival_total_token_usage=agentic_retrival_total_token_usage,
            prompt_total_token_usage=prompt_total_token_usage
        )
        
        self.active_logs[request_id] = log_entry
        
        # Log în terminal - doar informațiile care se salvează în DB
        print(f"\n[DB LOG] 📝 Chat Start | ID: {request_id}")
        print(f"  Conversation: {conversation_id}")
        print(f"  User: {user_id or 'Anonymous'}")
        print(f"  Model: {model_used or 'Unknown'}")
        print(f"  Question: {question[:100]}{'...' if len(question) > 100 else ''}")
        if agentic_retrival_total_token_usage:
            print(f"  Agentic Tokens: {agentic_retrival_total_token_usage}")
        if prompt_total_token_usage:
            print(f"  Prompt Token Usage: {prompt_total_token_usage[:100]}{'...' if len(prompt_total_token_usage) > 100 else ''}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_chat_start_to_db(
            conversation_id=conversation_id,
            request_id=request_id,
            question=question,
            user_id=user_id,
            extra_info_thoughts=extra_info_thoughts,
            agentic_retrival_total_token_usage=agentic_retrival_total_token_usage,
            prompt_total_token_usage=prompt_total_token_usage,
            model_used=model_used,
            temperature=temperature,
            timestamp_start=log_entry.timestamp_start
        ))
    
    def finish_chat_log(
        self,
        request_id: str,
        answer: str,
        agentic_retrival_duration_seconds: Optional[float] = None
    ) -> None:
        """Finalizează logging-ul pentru o cerere de chat"""
        if not self.enable_logging or request_id not in self.active_logs:
            return
        
        log_entry = self.active_logs[request_id]
        log_entry.answer = answer
        log_entry.timestamp_end = datetime.now()
        log_entry.agentic_retrival_duration_seconds = agentic_retrival_duration_seconds
        
        # Calculează durata totală
        total_duration = (log_entry.timestamp_end - log_entry.timestamp_start).total_seconds()
        
        # Log în terminal - doar informațiile care se salvează în DB
        print(f"[DB LOG] ✅ Chat End | ID: {request_id}")
        print(f"  Total Duration: {total_duration:.2f}s")
        if agentic_retrival_duration_seconds:
            print(f"  Agentic Duration: {agentic_retrival_duration_seconds:.2f}s")
        print(f"  Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
        
        # Salvează log-ul complet (pentru acum doar în terminal)
        self._save_complete_log(log_entry)
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_chat_end_to_db(
            request_id=request_id,
            answer=answer,
            agentic_retrival_duration_seconds=agentic_retrival_duration_seconds,
            timestamp_end=log_entry.timestamp_end
        ))
        
        # Curăță din active logs
        del self.active_logs[request_id]
    
    def log_streaming_start(
        self,
        request_id: str
    ) -> None:
        """Loghează începutul streaming-ului pentru o cerere de chat"""
        if not self.enable_logging or request_id not in self.active_logs:
            return
        
        log_entry = self.active_logs[request_id]
        log_entry.timestamp_start_streaming = datetime.now()
        
        # Log în terminal
        print(f"[DB LOG] 🚀 Streaming Start | ID: {request_id}")
        
        # Încearcă să salveze în baza de date (asincron, fără a bloca aplicația)
        self._schedule_task(self._save_streaming_start_to_db(
            request_id=request_id,
            timestamp_start_streaming=log_entry.timestamp_start_streaming
        ))
    
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
        total_duration = 0
        if log_entry.timestamp_end:
            total_duration = (log_entry.timestamp_end - log_entry.timestamp_start).total_seconds()
        
        print(f"[DB LOG] 💾 Complete | Conv: {log_entry.conversation_id}")
        print(f"  Q: {log_entry.question[:60]}{'...' if len(log_entry.question) > 60 else ''}")
        print(f"  A: {log_entry.answer[:60]}{'...' if len(log_entry.answer) > 60 else ''}")
        print(f"  Model: {log_entry.model_used} | Total Duration: {total_duration:.1f}s")
        if log_entry.agentic_retrival_duration_seconds:
            print(f"  Agentic Duration: {log_entry.agentic_retrival_duration_seconds:.1f}s")
        if log_entry.agentic_retrival_total_token_usage:
            print(f"  Agentic Tokens: {log_entry.agentic_retrival_total_token_usage}")
        if log_entry.prompt_total_token_usage:
            print(f"  Prompt Tokens: {log_entry.prompt_total_token_usage[:60]}{'...' if len(log_entry.prompt_total_token_usage) > 60 else ''}")
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
        extra_info_thoughts: str,
        agentic_retrival_total_token_usage: Optional[str],
        prompt_total_token_usage: Optional[str],
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
                extra_info_thoughts=extra_info_thoughts,
                agentic_retrival_total_token_usage=agentic_retrival_total_token_usage,
                prompt_total_token_usage=prompt_total_token_usage,
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
        agentic_retrival_duration_seconds: Optional[float],
        timestamp_end: datetime
    ) -> None:
        """Salvează sfârșitul chat-ului în baza de date (asincron)"""
        try:
            await azure_sql_logger.log_chat_end(
                request_id=request_id,
                answer=answer,
                agentic_retrival_duration_seconds=agentic_retrival_duration_seconds,
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
    
    def _extract_agentic_token_usage(self, extra_info_thoughts: list) -> Optional[int]:
        """Extrage token usage pentru agentic retrieval din thoughts - doar total_tokens ca int"""
        try:
            # Căută în thoughts pentru entryul cu 'ModelQueryPlanning' sau agentic info
            for thought in extra_info_thoughts:
                if hasattr(thought, 'title') and hasattr(thought, 'props'):
                    if 'agentic' in thought.title.lower() or 'query' in thought.title.lower():
                        if thought.props and 'query_plan' in thought.props:
                            query_plan = thought.props['query_plan']
                            if query_plan and isinstance(query_plan, list) and len(query_plan) > 0:
                                # Extrage token info din primul query plan entry
                                first_entry = query_plan[0]
                                if isinstance(first_entry, dict):
                                    input_tokens = first_entry.get('input_tokens')
                                    output_tokens = first_entry.get('output_tokens')
                                    if input_tokens is not None and output_tokens is not None:
                                        # Returnează doar total_tokens ca int
                                        return input_tokens + output_tokens
            return None
        except Exception as e:
            print(f"[DATABASE ERROR] Eroare la extragerea agentic token usage: {e}")
            return None
    
    def _extract_prompt_token_usage(self, extra_info_thoughts: list) -> Optional[str]:
        """Extrage token usage total pentru toate prompt-urile din thoughts"""
        try:
            total_prompt_tokens = 0
            total_completion_tokens = 0
            total_reasoning_tokens = 0
            
            print(f"[DEBUG] Processing {len(extra_info_thoughts)} thoughts for prompt token extraction")
            
            # Iterează prin toate thoughts și adună token usage
            for i, thought in enumerate(extra_info_thoughts):
                print(f"[DEBUG] Thought {i}: title='{getattr(thought, 'title', 'N/A')}', has_props={hasattr(thought, 'props')}")
                
                if hasattr(thought, 'props') and thought.props:
                    print(f"[DEBUG] Props keys: {list(thought.props.keys()) if thought.props else 'None'}")
                    token_usage = thought.props.get('token_usage')
                    if token_usage:
                        print(f"[DEBUG] Found token_usage: {token_usage}")
                        if hasattr(token_usage, 'prompt_tokens'):
                            total_prompt_tokens += token_usage.prompt_tokens or 0
                        if hasattr(token_usage, 'completion_tokens'):
                            total_completion_tokens += token_usage.completion_tokens or 0
                        if hasattr(token_usage, 'reasoning_tokens'):
                            total_reasoning_tokens += token_usage.reasoning_tokens or 0
            
            print(f"[DEBUG] Total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}, reasoning={total_reasoning_tokens}")
            
            if total_prompt_tokens > 0 or total_completion_tokens > 0:
                result = {
                    'prompt_tokens': total_prompt_tokens,
                    'completion_tokens': total_completion_tokens,
                    'total_tokens': total_prompt_tokens + total_completion_tokens
                }
                if total_reasoning_tokens > 0:
                    result['reasoning_tokens'] = total_reasoning_tokens
                    
                return json.dumps(result)
            
            return None
        except Exception as e:
            print(f"[DATABASE ERROR] Eroare la extragerea prompt token usage: {e}")
            return None
    
    def _serialize_thoughts(self, extra_info_thoughts: list) -> str:
        """Serializează thoughts pentru salvare în DB"""
        try:
            serialized_thoughts = []
            for thought in extra_info_thoughts:
                thought_dict = {
                    'title': getattr(thought, 'title', ''),
                    'description': getattr(thought, 'description', ''),
                    'props': getattr(thought, 'props', {})
                }
                # Convertește props în format serializable
                if thought_dict['props']:
                    # Încearcă să convertească obiectele complexe în dict-uri
                    try:
                        # Pentru token_usage, convertește în dict
                        if 'token_usage' in thought_dict['props']:
                            token_usage = thought_dict['props']['token_usage']
                            if hasattr(token_usage, '__dict__'):
                                thought_dict['props']['token_usage'] = token_usage.__dict__
                    except Exception:
                        pass  # Ignore conversion errors
                
                serialized_thoughts.append(thought_dict)
            
            return json.dumps(serialized_thoughts, default=str, ensure_ascii=False)
        except Exception as e:
            print(f"[DATABASE ERROR] Eroare la serializarea thoughts: {e}")
            return str(extra_info_thoughts)[:1000]  # Fallback la string truncat


# Instanță globală pentru logger
chat_logger = ChatLogger(enable_logging=True)
