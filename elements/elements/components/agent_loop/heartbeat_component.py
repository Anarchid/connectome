import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Tuple

from ..base_component import Component
from elements.component_registry import register_component

logger = logging.getLogger(__name__)


@register_component
class HeartbeatComponent(Component):
	COMPONENT_TYPE = "HeartbeatComponent"

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._task: Optional[asyncio.Task] = None
		self._interval_ms: int = 300
		self._running: bool = False
		self._processing_lock = asyncio.Lock()
		self._preempt_flag = False
		self._normal_queue: asyncio.Queue[Tuple[Dict[str, Any], Dict[str, Any]]] = asyncio.Queue()
		self._interrupt_queue: asyncio.Queue[Tuple[Dict[str, Any], Dict[str, Any]]] = asyncio.Queue()
		
		# NEW: Track when typing indicators were last sent for each chat
		self._last_typing_sent: Dict[str, float] = {}  # chat_id -> timestamp
		self._typing_refresh_interval: float = 8.0  # Refresh typing every 8 seconds (Discord timeout is ~10s)

	def initialize(self, **kwargs) -> None:
		super().initialize(**kwargs)
		try:
			self._interval_ms = int(kwargs.get("heartbeat_ms", self._interval_ms))
		except Exception:
			pass
		self._start()
		logger.info(f"HeartbeatComponent initialized for {self.owner.id if self.owner else 'unknown'} at {self._interval_ms} ms")

	def _start(self) -> None:
		if self._task and not self._task.done():
			return
		self._running = True
		loop = asyncio.get_event_loop()
		self._task = loop.create_task(self.run())

	async def shutdown(self) -> None:
		self._running = False
		if self._task and not self._task.done():
			self._task.cancel()
			try:
				await self._task
			except Exception:
				pass
		logger.info("HeartbeatComponent shutdown complete")

	# --- Public enqueue APIs ---
	async def enqueue_normal(self, event_payload: Dict[str, Any], timeline_context: Dict[str, Any]) -> None:
		try:
			self._normal_queue.put_nowait((event_payload, timeline_context))
		except Exception as e:
			logger.error(f"Heartbeat enqueue_normal error: {e}")

	async def enqueue_interrupt(self, event_payload: Dict[str, Any], timeline_context: Dict[str, Any]) -> None:
		try:
			self._interrupt_queue.put_nowait((event_payload, timeline_context))
		except Exception as e:
			logger.error(f"Heartbeat enqueue_interrupt error: {e}")

	async def handle_interrupt_now(self, event_payload: Dict[str, Any], timeline_context: Dict[str, Any]) -> None:
		"""Process an interrupt immediately, preempting normal work safely."""
		async with self._processing_lock:
			try:
				self._preempt_flag = True
				await self._request_agent_preempt()
				await self._process_single_event(event_payload, timeline_context)
				candidates = self._collect_focus_candidates_from_decider()
				# Always include current event conversation as candidate
				conv = event_payload.get('external_conversation_id') or event_payload.get('payload', {}).get('external_conversation_id')
				if conv and conv not in candidates:
					candidates.append(conv)
				await self._refresh_hud_and_cache(candidates)
				await self._post_decider_evaluate()
			finally:
				self._preempt_flag = False

	async def run(self):
		try:
			while self._running:
				# Interrupts take priority
				if not self._interrupt_queue.empty():
					payload, ctx = await self._interrupt_queue.get()
					await self.handle_interrupt_now(payload, ctx)
					continue
				# Normal pulse
				async with self._processing_lock:
					await self._process_pulse()
					await self._refresh_hud_and_cache(self._collect_focus_candidates_from_decider())
					await self._post_decider_evaluate()
				
				# NEW: Check for active LLM completions and send typing indicators
				await self._check_and_send_typing_indicators()
				
				await asyncio.sleep(self._interval_ms / 1000.0)
		except asyncio.CancelledError:
			logger.debug("Heartbeat task cancelled")
		except Exception as e:
			logger.error(f"Heartbeat error: {e}", exc_info=True)

	# --- Internal helpers ---
	async def _process_pulse(self) -> None:
		processed = 0
		budget = 100  # max items per pulse (tunable)
		while processed < budget and not self._normal_queue.empty():
			payload, ctx = await self._normal_queue.get()
			await self._process_single_event(payload, ctx)
			processed += 1

	async def _process_single_event(self, event_payload: Dict[str, Any], timeline_context: Dict[str, Any]) -> None:
		try:
			space = self.owner  # Heartbeat is attached to InnerSpace; owner is InnerSpace (Space subclass)
			space.process_event_for_components(event_payload, timeline_context)
		except Exception as e:
			logger.error(f"Heartbeat process_single_event error: {e}", exc_info=True)

	async def _request_agent_preempt(self) -> None:
		try:
			agent_loop = getattr(self.owner, '_agent_loop', None) if self.owner else None
			if agent_loop and hasattr(agent_loop, 'request_cancel'):
				agent_loop.request_cancel()
				# Await confirmation from agent loop via cancel event
				cancel_event = getattr(agent_loop, 'get_cancel_event', None)
				if callable(cancel_event):
					try:
						evt = cancel_event()
						await asyncio.wait_for(evt.wait(), timeout=1.0)
						# Reset event for future preemptions
						reset_fn = getattr(agent_loop, 'reset_cancel_event', None)
						if callable(reset_fn):
							reset_fn()
					except asyncio.TimeoutError:
						logger.debug("Preempt confirmation timed out; proceeding")
				else:
					# Fallback minimal delay if event not available
					await asyncio.sleep(0.01)
		except Exception as e:
			logger.debug(f"Heartbeat preempt request error: {e}")

	async def _refresh_hud_and_cache(self, candidates: List[Optional[str]]) -> None:
		try:
			# Resolve HUD component
			hud = self.owner.get_component_by_type_name("FacetAwareHUDComponent") if hasattr(self.owner, 'get_component_by_type_name') else None
			if not hud:
				# Fallback: search by type string
				for _name, comp in self.owner.get_components().items():
					if getattr(comp, 'COMPONENT_TYPE', '') == 'FacetAwareHUDComponent':
						hud = comp
						break
			if not hud or not hasattr(hud, 'refresh_snapshots'):
				return
			focus_ids = [fid for fid in (candidates or []) if fid]
			if focus_ids:
				await hud.refresh_snapshots(focus_ids)
		except Exception as e:
			logger.debug(f"Heartbeat HUD refresh error: {e}")

	def _collect_focus_candidates_from_pulse(self) -> List[str]:
		# TODO: derive from processed events in this pulse; simple stub returns empty list
		return []

	def _collect_focus_candidates_from_decider(self) -> List[str]:
		try:
			decider = None
			# Prefer InterruptDecider for focus candidates
			for _name, comp in self.owner.get_components().items():
				ctype = getattr(comp, 'COMPONENT_TYPE', '')
				if ctype == 'InterruptDeciderComponent':
					decider = comp
					break
			if decider and hasattr(decider, 'get_focus_candidates'):
				return decider.get_focus_candidates()
			return []
		except Exception:
			return []

	async def _post_decider_evaluate(self) -> None:
		try:
			# Resolve ActivationDecider
			decider = None
			for _name, comp in self.owner.get_components().items():
				if getattr(comp, 'COMPONENT_TYPE', '') == 'ActivationDeciderComponent':
					decider = comp
					break
			if decider and hasattr(decider, 'evaluate_and_maybe_activate'):
				await decider.evaluate_and_maybe_activate({})
		except Exception as e:
			logger.debug(f"Heartbeat post-decider evaluate error: {e}")
	
	async def _check_and_send_typing_indicators(self) -> None:
		"""
		Check for active LLM completions and send typing indicators as needed.
		This ensures typing indicators stay active during long LLM completions.
		"""
		try:
			# Get the agent loop component
			agent_loop = getattr(self.owner, '_agent_loop', None) if self.owner else None
			if not agent_loop:
				return
			
			# Check if there are active completions
			active_completions = agent_loop.get_active_completions() if hasattr(agent_loop, 'get_active_completions') else {}
			
			if not active_completions:
				# No active completions, clear our tracking
				self._last_typing_sent.clear()
				return
			
			# We'll get the ActivityStatusComponent for each chat as needed
			
			# Process each active completion
			current_time = time.time()
			for completion_id, context in active_completions.items():
				adapter_id = context.get('adapter_id')
				chat_id = context.get('chat_id')
				
				if not adapter_id or not chat_id:
					continue
				
				# Check if we need to send/refresh typing for this chat
				last_sent = self._last_typing_sent.get(chat_id, 0)
				time_since_last = current_time - last_sent

				if time_since_last >= self._typing_refresh_interval:
					# Send typing indicator through ActivityStatusComponent
					try:
						# Get ActivityStatusComponent from parent inner space
						parent_inner_space = getattr(self.owner, 'get_parent_object', lambda: None)()
						if parent_inner_space:
							activity_status_component = parent_inner_space.get_component_by_type("ActivityStatusComponent")
							if activity_status_component:
								result = await activity_status_component.handle_typing_indicator(adapter_id, chat_id, is_typing=True)
								if result.get("success"):
									self._last_typing_sent[chat_id] = current_time
									logger.debug(f"Sent typing indicator for {adapter_id}/{chat_id} (completion {completion_id[:8]})")
								else:
									logger.debug(f"Failed to send typing indicator for {adapter_id}/{chat_id}: {result.get('error')}")
							else:
								logger.debug(f"No ActivityStatusComponent found for typing indicator")
						else:
							logger.debug(f"Could not get parent inner space for typing indicator")
					except Exception as e:
						logger.warning(f"Error sending typing indicator: {e}")
			
			# Clean up old entries from _last_typing_sent for chats no longer active
			active_chat_ids = {ctx.get('chat_id') for ctx in active_completions.values() if ctx.get('chat_id')}
			self._last_typing_sent = {
				chat_id: timestamp 
				for chat_id, timestamp in self._last_typing_sent.items() 
				if chat_id in active_chat_ids
			}
			
		except Exception as e:
			logger.debug(f"Error in typing indicator check: {e}") 