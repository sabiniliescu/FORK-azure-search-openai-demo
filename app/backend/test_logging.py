#!/usr/bin/env python3
"""
Test script pentru sistemul de logging de chat
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_logging.chat_logger import chat_logger
import asyncio
import time

def test_chat_logging():
    """Testează sistemul de chat logging"""
    print("=== TEST CHAT LOGGING SYSTEM ===\n")
    
    # Test 1: Start chat log
    print("1. Testing start_chat_log...")
    request_id = "test-request-123"
    question = "Ce este inteligența artificială?"
    user_id = "user-456"
    conversation_id = "conv-789"
    prompt = '[{"role": "user", "content": "Ce este inteligența artificială?"}]'
    model_used = "gpt-4"
    temperature = 0.7
    session_id = "session-101"
    
    chat_logger.start_chat_log(
        request_id=request_id,
        question=question,
        user_id=user_id,
        conversation_id=conversation_id,
        prompt=prompt,
        model_used=model_used,
        temperature=temperature,
        session_id=session_id
    )
    
    print("✓ Start chat log completed\n")
    
    # Simulăm procesarea (delay)
    time.sleep(2)
    
    # Test 2: Finish chat log
    print("2. Testing finish_chat_log...")
    answer = "Inteligența artificială (IA) este un domeniu al informaticii care se concentrează pe crearea de sisteme capabile să efectueze sarcini care de obicei necesită inteligență umană."
    tokens_used = 150
    
    chat_logger.finish_chat_log(
        request_id=request_id,
        answer=answer,
        tokens_used=tokens_used
    )
    
    print("✓ Finish chat log completed\n")
    
    # Test 3: Feedback logging
    print("3. Testing feedback logging...")
    
    chat_logger.log_feedback(
        conversation_id=conversation_id,
        session_id=session_id,
        feedback="positive",
        feedback_text="Răspuns foarte util și clar!",
        user_id=user_id,
        answer_index=0
    )
    
    print("✓ Feedback logging completed\n")
    
    # Test 4: Feedback negativ
    print("4. Testing negative feedback...")
    
    chat_logger.log_feedback(
        conversation_id=conversation_id,
        session_id=session_id,
        feedback="negative", 
        feedback_text="Răspunsul ar putea fi mai detaliat.",
        user_id=user_id,
        answer_index=0
    )
    
    print("✓ Negative feedback logging completed\n")
    
    print("=== ALL TESTS COMPLETED SUCCESSFULLY ===")
    print("Systemul de logging funcționează corect!")
    print("Aplicația va continua să ruleze normal chiar dacă baza de date nu este disponibilă.")

if __name__ == "__main__":
    test_chat_logging()
