"""
Activity Status Component

Handles activity status indicators like typing notifications through the unified component architecture.
"""
import logging
import time
from typing import Dict, Any, Optional, Callable

from ..base import Component
from elements.component_registry import register_component

logger = logging.getLogger(__name__)


@register_component
class ActivityStatusComponent(Component):
    """
    Component that handles activity status indicators (typing, presence, etc.)
    through the standard component architecture and outgoing action callback.
    """

    COMPONENT_TYPE = "ActivityStatusComponent"
    DEPENDENCIES = []
    HANDLED_EVENT_TYPES = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._outgoing_action_callback: Optional[Callable] = None

    def _on_initialize(self) -> None:
        """Initialize the activity status component."""
        logger.debug(f"ActivityStatusComponent {self.id} initialized")

    def set_outgoing_action_callback(self, callback: Callable) -> None:
        """
        Set the callback for outgoing actions (typically ExternalEventRouter.handle_outgoing_action).

        Args:
            callback: Function to call for outgoing actions
        """
        self._outgoing_action_callback = callback
        logger.debug(f"ActivityStatusComponent {self.id}: Outgoing action callback set")

    async def handle_typing_indicator(self, adapter_id: str, conversation_id: str, is_typing: bool = True) -> Dict[str, Any]:
        """
        Send a typing indicator through the unified action system.

        Args:
            adapter_id: ID of the adapter to send through
            conversation_id: ID of the conversation/chat
            is_typing: Whether typing is active (True) or not (False)

        Returns:
            Dictionary with success status and any relevant info
        """
        if not self._outgoing_action_callback:
            error_msg = "Cannot send typing indicator: No outgoing action callback set"
            logger.error(f"[{self.owner.id}] {error_msg}")
            return {"success": False, "error": error_msg}

        # Create internal request ID for tracking
        internal_request_id = f"typing_{adapter_id}_{conversation_id}_{int(time.time())}"

        # Create action request following the same pattern as tool calls
        action_request = {
            "action_type": "send_typing_indicator",
            "target_module": "ActivityClient",
            "payload": {
                "action_type": "send_typing_indicator",
                "adapter_id": adapter_id,
                "conversation_id": conversation_id,
                "is_typing": is_typing,
                "internal_request_id": internal_request_id,
                "requesting_element_id": self.owner.id
            }
        }

        try:
            logger.debug(f"[{self.owner.id}] Sending typing indicator ({is_typing}) for {adapter_id}/{conversation_id}")

            # Send through the unified action system
            dispatch_result = await self._outgoing_action_callback(action_request)

            if dispatch_result and dispatch_result.get("success"):
                logger.debug(f"[{self.owner.id}] Typing indicator successfully dispatched for req_id: {internal_request_id}")
                return {"success": True, "internal_request_id": internal_request_id}
            else:
                error_msg = f"Failed to dispatch typing indicator. Result: {dispatch_result}"
                logger.error(f"[{self.owner.id}] {error_msg} for req_id: {internal_request_id}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error dispatching typing indicator: {e}"
            logger.error(f"[{self.owner.id}] {error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}