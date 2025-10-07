"""
Custom Bot Framework Adapter using Azure Managed Identity
"""
import logging
from typing import Optional
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from managed_identity_credentials import ManagedIdentityAppCredentials

logger = logging.getLogger(__name__)

class ManagedIdentityBotAdapter(BotFrameworkAdapter):
    """
    Custom BotFrameworkAdapter that uses Managed Identity for authentication
    """
    
    def __init__(self, app_id: str, tenant_id: Optional[str] = None):
        """
        Initialize adapter with Managed Identity
        
        Args:
            app_id: Microsoft App ID (Managed Identity client ID)
            tenant_id: Azure AD Tenant ID
        """
        # Create settings with empty password
        settings = BotFrameworkAdapterSettings(
            app_id=app_id,
            app_password=""
        )
        
        # Initialize base adapter
        super().__init__(settings)
        
        # Override credentials with Managed Identity implementation
        self.credentials = ManagedIdentityAppCredentials(
            app_id=app_id,
            tenant_id=tenant_id
        )
        
        # CRITICAL: Override the app_credentials property to ensure
        # connector clients use our Managed Identity credentials
        self._credentials = self.credentials
        
        logger.info(f"✅ ManagedIdentityBotAdapter initialized for app {app_id}")
    
    def get_app_credentials(self, app_id: str, oauth_scope: str = None):
        """
        Override to return Managed Identity credentials
        
        Args:
            app_id: The app ID
            oauth_scope: OAuth scope (not used with Managed Identity)
            
        Returns:
            Managed Identity credentials
        """
        return self.credentials
