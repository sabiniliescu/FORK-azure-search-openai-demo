"""
Client for communicating with the existing backend API
"""
import aiohttp
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BackendClient:
    """Client to interact with the backend chat API"""

    def __init__(self, backend_url: str, api_key: Optional[str] = None):
        """
        Initialize the backend client
        
        Args:
            backend_url: Base URL of the backend API
            api_key: Optional API key for authentication
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_key = api_key
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def chat(
        self, 
        message: str, 
        history: List[Dict[str, str]] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to the backend
        
        Args:
            message: User's message
            history: Conversation history
            context: Additional context and overrides
            
        Returns:
            Response from backend API
        """
        if history is None:
            history = []
        if context is None:
            context = {}

        # Format history for backend API
        messages = []
        for exchange in history:
            if "user" in exchange:
                messages.append({"role": "user", "content": exchange["user"]})
            if "assistant" in exchange:
                messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})

        # Prepare request payload matching the backend API format
        payload = {
            "messages": messages,
            "context": context.get("context", {}),
            "session_state": context.get("session_state"),
        }

        # Add overrides if provided
        if "overrides" in context:
            payload["context"]["overrides"] = context["overrides"]

        try:
            session = await self._get_session()
            url = f"{self.backend_url}/chat"
            
            logger.info(f"Sending request to {url}")
            
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                logger.info(f"Received response from backend")
                return data

        except aiohttp.ClientError as e:
            logger.error(f"Error calling backend API: {e}")
            raise Exception(f"Failed to communicate with backend: {str(e)}")

    async def ask(
        self,
        question: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a single question to the backend (Q&A mode)
        
        Args:
            question: User's question
            context: Additional context and overrides
            
        Returns:
            Response from backend API
        """
        if context is None:
            context = {}

        payload = {
            "messages": [{"role": "user", "content": question}],
            "context": context.get("context", {}),
            "session_state": context.get("session_state"),
        }

        if "overrides" in context:
            payload["context"]["overrides"] = context["overrides"]

        try:
            session = await self._get_session()
            url = f"{self.backend_url}/ask"
            
            logger.info(f"Sending ask request to {url}")
            
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                logger.info(f"Received response from backend")
                return data

        except aiohttp.ClientError as e:
            logger.error(f"Error calling backend API: {e}")
            raise Exception(f"Failed to communicate with backend: {str(e)}")

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Backend client session closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
