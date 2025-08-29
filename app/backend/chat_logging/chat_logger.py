import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


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


# Instanță globală pentru logger
chat_logger = ChatLogger(enable_logging=True)
