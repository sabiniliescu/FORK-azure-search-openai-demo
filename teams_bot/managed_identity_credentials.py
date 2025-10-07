"""
Managed Identity credentials for Bot Framework
"""
import logging
from typing import Optional
from azure.identity import ManagedIdentityCredential
from botframework.connector.auth import AppCredentials

logger = logging.getLogger(__name__)

class ManagedIdentityAppCredentials(AppCredentials):
    """
    AppCredentials implementation using Azure Managed Identity
    """
    
    def __init__(self, app_id: str, tenant_id: Optional[str] = None):
        """
        Initialize Managed Identity credentials
        
        Args:
            app_id: The Microsoft App ID (client ID of the managed identity)
            tenant_id: The Azure AD tenant ID
        """
        # Set required attributes directly (don't call super().__init__)
        self.microsoft_app_id = app_id
        self.microsoft_app_password = ""
        self.tenant_id = tenant_id
        self.oauth_scope = None  # Required by BotFrameworkAdapter
        
        # Create Managed Identity credential (synchronous version)
        self.credential = ManagedIdentityCredential(client_id=app_id)
        
        # Bot Framework token endpoint scope
        self.scope = "https://api.botframework.com/.default"
        
        logger.info(f"🔐 Initialized ManagedIdentityAppCredentials for app {app_id}")
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get access token using Managed Identity
        
        Args:
            force_refresh: Force token refresh
            
        Returns:
            Access token string
        """
        try:
            logger.info("🔑 Requesting access token using Managed Identity...")
            token = self.credential.get_token(self.scope)
            logger.info("✅ Successfully obtained access token via Managed Identity")
            return token.token
        except Exception as e:
            logger.error(f"❌ Failed to get token via Managed Identity: {e}")
            raise
    
    def signed_session(self, session=None):
        """
        Add authentication to session
        
        Args:
            session: Optional session to sign
        """
        # Get token and add to session
        token = self.get_access_token()
        if session:
            session.headers["Authorization"] = f"Bearer {token}"
        return session
