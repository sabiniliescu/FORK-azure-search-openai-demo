"""
Microsoft Teams Bot for Azure Search OpenAI Demo
This bot acts as a Teams frontend for the existing backend API
"""
import os
import logging
from typing import List
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from backend_client import BackendClient

logger = logging.getLogger(__name__)


class TeamsBot(ActivityHandler):
    """Teams Bot that integrates with the existing backend API"""

    def __init__(self, backend_url: str):
        """
        Initialize the Teams bot
        
        Args:
            backend_url: URL of the backend API (e.g., the deployed Azure Container App)
        """
        self.backend_client = BackendClient(backend_url)
        # Store conversation history per user
        self.conversation_history = {}

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming message from Teams
        
        Args:
            turn_context: Context object for the current turn
        """
        try:
            user_message = turn_context.activity.text
            user_id = turn_context.activity.from_property.id
            conversation_id = turn_context.activity.conversation.id

            logger.info(f"Received message from user {user_id}: {user_message}")

            # Send typing indicator
            typing_activity = Activity(type=ActivityTypes.typing)
            await turn_context.send_activity(typing_activity)

            # Get conversation history for this user
            history = self.conversation_history.get(conversation_id, [])

            # Call backend chat API
            response = await self.backend_client.chat(
                message=user_message,
                history=history,
                context={
                    "overrides": {
                        "temperature": 0.7,
                        "top": 3,
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": True,
                    }
                }
            )

            # Update conversation history
            answer_text = response.get("message", {}).get("content", "")
            history.append({"user": user_message, "assistant": answer_text})
            self.conversation_history[conversation_id] = history[-10:]  # Keep last 10 exchanges

            # Format response with citations
            reply_text = self._format_response(response)

            # Send response back to Teams
            await turn_context.send_activity(reply_text)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_message = f"Ne pare rău, a apărut o eroare: {str(e)}"
            await turn_context.send_activity(error_message)

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """
        Handle when members are added to the conversation
        
        Args:
            members_added: List of members added to the conversation
            turn_context: Context object for the current turn
        """
        try:
            for member in members_added:
                if member.id != turn_context.activity.recipient.id:
                    welcome_message = (
                        "👋 Bun venit! Sunt asistentul tău virtual.\n\n"
                        "Poți să-mi pui întrebări despre:\n"
                        "- Beneficiile companiei\n"
                        "- Politicile interne\n"
                        "- Descrieri de posturi\n"
                        "- Orice altceva din documentele companiei\n\n"
                        "Cum te pot ajuta astăzi?"
                    )
                    await turn_context.send_activity(welcome_message)
        except Exception as e:
            logger.error(f"Error in on_members_added: {e}", exc_info=True)

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """
        Handle conversation update events
        
        Args:
            turn_context: Context object for the current turn
        """
        # Clear conversation history when conversation is reset
        conversation_id = turn_context.activity.conversation.id
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
        
        return await super().on_conversation_update_activity(turn_context)

    def _format_response(self, response: dict) -> str:
        """
        Format the backend response for Teams display
        
        Args:
            response: Response from backend API
            
        Returns:
            Formatted string for Teams
        """
        # Backend returns: {"message": {"content": "...", "role": "assistant"}, "context": {...}}
        message_obj = response.get("message", {})
        answer = message_obj.get("content", "Scuze, nu am primit un răspuns.")
        
        # Get context data
        context_data = response.get("context", {})
        data_points = context_data.get("data_points", {})
        thoughts = context_data.get("thoughts", "")

        # Build formatted response
        formatted = f"{answer}\n\n"

        # Add citations if available (data_points contains the source documents)
        if data_points and isinstance(data_points, dict):
            text_sources = data_points.get("text", [])
            if text_sources:
                formatted += "📚 **Surse:**\n"
                for i, source in enumerate(text_sources[:5], 1):  # Max 5 sources
                    if isinstance(source, str):
                        # Simple string source
                        formatted += f"{i}. {source}\n"
                    elif isinstance(source, dict):
                        # Dict with title/url
                        title = source.get("title", source.get("name", "Document"))
                        formatted += f"{i}. {title}\n"

        return formatted.strip()

    async def clear_conversation(self, conversation_id: str):
        """
        Clear conversation history for a specific conversation
        
        Args:
            conversation_id: ID of the conversation to clear
        """
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.info(f"Cleared conversation history for {conversation_id}")
