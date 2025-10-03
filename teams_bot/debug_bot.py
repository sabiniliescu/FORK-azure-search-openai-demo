"""
Debug version of app.py with extensive logging
"""
import os
import sys
import logging
from dotenv import load_dotenv
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import ActivityHandler, TurnContext, BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from backend_client import BackendClient

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:50505")
PORT = int(os.environ.get("PORT", 3978))

# Create adapter
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


class DebugBot(ActivityHandler):
    """Debug bot with extensive logging"""
    
    def __init__(self, backend_url: str):
        self.backend_client = BackendClient(backend_url)
        self.conversation_history = {}
        logger.info(f"🤖 Bot initialized with backend: {backend_url}")
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle message with detailed logging"""
        try:
            user_message = turn_context.activity.text
            user_id = turn_context.activity.from_property.id
            conversation_id = turn_context.activity.conversation.id
            
            logger.info(f"📨 Message received")
            logger.info(f"   User ID: {user_id}")
            logger.info(f"   Conversation ID: {conversation_id}")
            logger.info(f"   Message: {user_message}")
            
            # Get history
            history = self.conversation_history.get(conversation_id, [])
            logger.info(f"   History length: {len(history)}")
            
            # Call backend
            logger.info(f"🔄 Calling backend...")
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
            
            logger.info(f"✅ Backend response received")
            logger.info(f"   Response keys: {list(response.keys())}")
            
            # Extract answer
            message_obj = response.get("message", {})
            logger.info(f"   Message object keys: {list(message_obj.keys())}")
            
            answer_text = message_obj.get("content", "")
            logger.info(f"   Answer length: {len(answer_text)} chars")
            logger.info(f"   Answer preview: {answer_text[:100]}...")
            
            # Update history
            history.append({"user": user_message, "assistant": answer_text})
            self.conversation_history[conversation_id] = history[-10:]
            
            # Format and send
            formatted_reply = self._format_response(response)
            logger.info(f"📤 Sending reply ({len(formatted_reply)} chars)")
            
            await turn_context.send_activity(formatted_reply)
            logger.info(f"✅ Reply sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in on_message_activity: {e}", exc_info=True)
            error_msg = f"Eroare: {str(e)}"
            try:
                await turn_context.send_activity(error_msg)
            except:
                logger.error("Failed to send error message to user")
    
    def _format_response(self, response: dict) -> str:
        """Format response"""
        message_obj = response.get("message", {})
        answer = message_obj.get("content", "Nu am primit răspuns.")
        
        context_data = response.get("context", {})
        data_points = context_data.get("data_points", {})
        
        formatted = f"{answer}\n\n"
        
        if data_points and isinstance(data_points, dict):
            text_sources = data_points.get("text", [])
            if text_sources:
                formatted += "📚 **Surse:**\n"
                for i, source in enumerate(text_sources[:5], 1):
                    if isinstance(source, str):
                        formatted += f"{i}. {source}\n"
                    elif isinstance(source, dict):
                        title = source.get("title", source.get("name", "Document"))
                        formatted += f"{i}. {title}\n"
        
        return formatted.strip()


# Error handler
async def on_error(context, error):
    logger.error(f"❌ Adapter error: {error}", exc_info=True)
    try:
        await context.send_activity(f"Eroare adapter: {str(error)}")
    except Exception as e:
        logger.error(f"Failed to send error to user: {e}")


ADAPTER.on_turn_error = on_error

# Create bot
BOT = DebugBot(BACKEND_URL)


# Messages endpoint
async def messages(req: Request) -> Response:
    """Handle messages"""
    try:
        logger.info("=" * 70)
        logger.info("📥 NEW REQUEST to /api/messages")
        logger.info(f"   Method: {req.method}")
        logger.info(f"   Headers: {dict(req.headers)}")
        
        content_type = req.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logger.error(f"❌ Invalid content type: {content_type}")
            return Response(status=415, text="Content-Type must be application/json")

        body = await req.json()
        logger.info(f"📦 Request body type: {body.get('type', 'unknown')}")
        
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        logger.info(f"🔄 Processing activity...")
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        
        if response:
            logger.info(f"📤 Returning response with status {response.status}")
            return Response(status=response.status, text=response.body)
        
        logger.info("✅ Request completed successfully (200)")
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"❌ Exception in messages endpoint: {e}", exc_info=True)
        return Response(status=500, text=str(e))


# Health endpoint
async def health_check(req: Request) -> Response:
    """Health check"""
    return Response(
        status=200,
        text='{"status": "healthy", "service": "debug-bot"}',
        content_type="application/json"
    )


# Create app
def create_app() -> web.Application:
    """Create web app"""
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", lambda req: Response(text="Debug Bot is running!"))
    return app


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f"🤖 Starting DEBUG BOT on port {PORT}")
    logger.info("=" * 70)
    logger.info(f"📍 Backend URL: {BACKEND_URL}")
    logger.info(f"📍 Bot endpoint: http://localhost:{PORT}/api/messages")
    logger.info(f"💚 Health: http://localhost:{PORT}/health")
    logger.info(f"🔐 App ID: {'Configured' if APP_ID else 'Empty (dev mode)'}")
    logger.info("=" * 70)
    
    app = create_app()
    
    try:
        web.run_app(app, host="localhost", port=PORT)
    except Exception as error:
        logger.error(f"❌ Failed to start: {error}")
        sys.exit(1)
