"""
Main application file for Teams Bot
"""
import os
import sys
import logging
from dotenv import load_dotenv
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from bot import TeamsBot

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
APP_TYPE = os.environ.get("MICROSOFT_APP_TYPE", "")  # Can be "UserAssignedMSI"
APP_TENANTID = os.environ.get("MICROSOFT_APP_TENANTID", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:50505")
PORT = int(os.environ.get("PORT", 8000))

# Global adapter and bot instances (initialized in create_app)
ADAPTER = None
BOT = None


def init_bot():
    """
    Initialize the Bot Framework adapter and bot instance
    Uses Managed Identity if APP_TYPE is UserAssignedMSI
    
    Returns:
        Tuple of (adapter, bot)
    """
    global ADAPTER, BOT
    
    # Check if using Managed Identity
    if APP_TYPE == "UserAssignedMSI":
        logger.info(f"🔐 Configuring bot with Managed Identity")
        logger.info(f"🔐 App ID: {APP_ID}")
        if APP_TENANTID:
            logger.info(f"🔐 Tenant ID: {APP_TENANTID}")
        
        # Import custom Managed Identity adapter
        from managed_identity_adapter import ManagedIdentityBotAdapter
        
        # Create adapter with Managed Identity
        adapter = ManagedIdentityBotAdapter(
            app_id=APP_ID,
            tenant_id=APP_TENANTID if APP_TENANTID else None
        )
        
        logger.info("✅ Bot adapter configured with Managed Identity")
    else:
        # Standard authentication with app password
        logger.info(f"🔐 Configuring bot with standard authentication")
        logger.info(f"🔐 App ID: {APP_ID}")
        
        settings = BotFrameworkAdapterSettings(
            app_id=APP_ID,
            app_password=APP_PASSWORD if APP_PASSWORD else ""
        )
        adapter = BotFrameworkAdapter(settings)
    
    # Catch-all for errors
    async def on_error(context, error):
        """
        Global error handler for the bot
        
        Args:
            context: Turn context
            error: Exception that occurred
        """
        logger.error(f"Error: {error}", exc_info=True)
        try:
            await context.send_activity(f"Ne pare rău, a apărut o eroare: {str(error)}")
        except:
            logger.error("Failed to send error message to user")
    
    adapter.on_turn_error = on_error
    
    # Create the bot
    bot = TeamsBot(BACKEND_URL)
    
    ADAPTER = adapter
    BOT = bot
    
    return adapter, bot


# Listen for incoming requests
async def messages(req: Request) -> Response:
    """
    Main endpoint for receiving messages from Teams
    
    Args:
        req: Incoming HTTP request
        
    Returns:
        HTTP response
    """
    try:
        # Check content type
        content_type = req.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logger.error(f"Invalid content type: {content_type}")
            return Response(status=415, text="Content-Type must be application/json")

        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        # For local testing without Bot Service, collect responses and return them
        # This allows testing without a deployed Bot Framework Connector
        invoke_response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        
        if invoke_response:
            return Response(status=invoke_response.status, body=invoke_response.body, content_type="application/json")
        return Response(status=200)
        
    except Exception as exception:
        logger.error(f"Exception in messages endpoint: {exception}", exc_info=True)
        return Response(status=500, text=str(exception))


# Health check endpoint
async def health_check(req: Request) -> Response:
    """
    Health check endpoint
    
    Args:
        req: Incoming HTTP request
        
    Returns:
        HTTP response with health status
    """
    return Response(
        status=200,
        text='{"status": "healthy", "service": "teams-bot"}',
        content_type="application/json"
    )


async def home(req: Request) -> Response:
    """Simple landing endpoint for root path."""
    return Response(
        status=200,
        text='{"status": "ok", "service": "teams-bot"}',
        content_type="application/json"
    )


# Create and configure the app
def create_app() -> web.Application:
    """
    Create and configure the aiohttp application
    
    Returns:
        Configured web application
    """
    # Initialize bot adapter and bot instance
    init_bot()
    
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_get("/", home)
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health_check)
    return app


# Create app instance for Azure App Service (Gunicorn needs this)
app = create_app()


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f"🤖 Starting Teams Bot on port {PORT}")
    logger.info("=" * 70)
    logger.info(f"📍 Backend URL: {BACKEND_URL}")
    logger.info(f"📍 Bot endpoint: http://localhost:{PORT}/api/messages")
    logger.info(f"💚 Health: http://localhost:{PORT}/health")
    logger.info(f"🔐 App ID: {'Configured' if APP_ID else 'Empty (dev mode)'}")
    logger.info("")
    logger.info("To test with Bot Framework Emulator:")
    logger.info("1. Download: https://github.com/Microsoft/BotFramework-Emulator/releases")
    logger.info(f"2. Open Bot URL: http://localhost:{PORT}/api/messages")
    logger.info("3. Leave App ID and Password empty for local testing")
    logger.info("=" * 70)

    try:
        # Use localhost for local development (Bot Emulator compatibility)
        # Use 0.0.0.0 for Azure deployment
        host = "localhost" if not APP_ID else "0.0.0.0"
        web.run_app(app, host=host, port=PORT)
    except Exception as error:
        logger.error(f"Failed to start application: {error}")
        sys.exit(1)
