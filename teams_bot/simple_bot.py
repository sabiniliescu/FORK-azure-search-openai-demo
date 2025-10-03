"""
Simplified bot for debugging - responds without calling backend
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
PORT = int(os.environ.get("PORT", 3978))

# Create adapter
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


class SimpleBot(ActivityHandler):
    """Simple bot for testing"""
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle message"""
        try:
            text = turn_context.activity.text
            logger.info(f"📨 Received: {text}")
            
            response = f"✅ Bot funcționează! Ai spus: '{text}'\n\nAcest mesaj confirmă că bot-ul primește și procesează mesaje corect."
            
            await turn_context.send_activity(response)
            logger.info(f"✅ Sent response")
            
        except Exception as e:
            logger.error(f"❌ Error in on_message_activity: {e}", exc_info=True)
            await turn_context.send_activity(f"Eroare: {str(e)}")


# Error handler
async def on_error(context, error):
    logger.error(f"❌ Adapter error: {error}", exc_info=True)
    try:
        await context.send_activity(f"A apărut o eroare: {str(error)}")
    except:
        pass


ADAPTER.on_turn_error = on_error

# Create bot
BOT = SimpleBot()


# Messages endpoint
async def messages(req: Request) -> Response:
    """Handle messages from Bot Framework"""
    try:
        logger.info("📥 Incoming request to /api/messages")
        
        if "application/json" not in req.headers.get("Content-Type", ""):
            logger.error("❌ Invalid content type")
            return Response(status=415, text="Content-Type must be application/json")

        body = await req.json()
        logger.info(f"📦 Request body: {body}")
        
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        
        if response:
            logger.info(f"📤 Sending response with status {response.status}")
            return Response(status=response.status, text=response.body)
        
        logger.info("✅ Request processed successfully")
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"❌ Exception in messages endpoint: {e}", exc_info=True)
        return Response(status=500, text=str(e))


# Health endpoint
async def health_check(req: Request) -> Response:
    """Health check"""
    return Response(
        status=200,
        text='{"status": "healthy", "service": "simple-bot"}',
        content_type="application/json"
    )


# Create app
def create_app() -> web.Application:
    """Create web app"""
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", lambda req: Response(text="Bot is running!"))
    return app


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f"🤖 Starting SIMPLE DEBUG BOT on port {PORT}")
    logger.info("=" * 70)
    logger.info(f"📍 Endpoint: http://localhost:{PORT}/api/messages")
    logger.info(f"💚 Health: http://localhost:{PORT}/health")
    logger.info(f"🔐 App ID: {'Configured' if APP_ID else 'Empty (dev mode)'}")
    logger.info("=" * 70)
    
    app = create_app()
    
    try:
        web.run_app(app, host="localhost", port=PORT)
    except Exception as error:
        logger.error(f"❌ Failed to start: {error}")
        sys.exit(1)
