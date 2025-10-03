"""
Simple test script to run the Teams bot locally without backend dependency
"""
import os
import sys
import logging
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
PORT = int(os.environ.get("PORT", 3978))

# Create adapter
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Simple test bot
class TestBot:
    """Simple test bot for local testing"""
    
    async def on_turn(self, turn_context):
        """Handle incoming message"""
        if turn_context.activity.type == "message":
            user_message = turn_context.activity.text
            logger.info(f"Received: {user_message}")
            
            # Simple response for testing
            response = f"🤖 Bot funcționează! Ai spus: '{user_message}'\n\n"
            response += "Pentru a te conecta la backend-ul real, pornește backend-ul și folosește app.py principal."
            
            await turn_context.send_activity(response)


# Catch-all for errors
async def on_error(context, error):
    logger.error(f"Error: {error}")
    await context.send_activity("A apărut o eroare. Te rog încearcă din nou.")


ADAPTER.on_turn_error = on_error

# Create the test bot
BOT = TestBot()


# Listen for incoming requests
async def messages(req: Request) -> Response:
    """Main endpoint for receiving messages from Teams"""
    if "application/json" in req.headers.get("Content-Type", ""):
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return Response(status=response.status, text=response.body)
        return Response(status=200)
    except Exception as exception:
        logger.error(f"Exception: {exception}")
        return Response(status=500, text=str(exception))


# Health check endpoint
async def health_check(req: Request) -> Response:
    """Health check endpoint"""
    return Response(
        status=200,
        text='{"status": "healthy", "service": "teams-bot-test"}',
        content_type="application/json"
    )


# Create and configure the app
def create_app() -> web.Application:
    """Create and configure the aiohttp application"""
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", lambda req: Response(text="Teams Bot is running! Endpoint: /api/messages"))
    return app


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Teams Bot TEST MODE on port {}".format(PORT))
    logger.info("=" * 60)
    logger.info("")
    logger.info("Bot endpoint: http://localhost:{}/api/messages".format(PORT))
    logger.info("Health check: http://localhost:{}/health".format(PORT))
    logger.info("")
    logger.info("To test with Bot Framework Emulator:")
    logger.info("1. Download: https://github.com/Microsoft/BotFramework-Emulator/releases")
    logger.info("2. Open Bot URL: http://localhost:{}/api/messages".format(PORT))
    logger.info("3. Leave App ID and Password empty for local testing")
    logger.info("")
    logger.info("=" * 60)
    
    app = create_app()
    
    try:
        web.run_app(app, host="localhost", port=PORT)
    except Exception as error:
        logger.error(f"Failed to start: {error}")
        sys.exit(1)
