# Developer Guide: Creating New Elements in Connectome

## Overview

This guide explains how to create new Elements with custom functionality in the Connectome framework. Elements are modular units that provide specific capabilities to agents through a component-based architecture.

## Core Concepts

### Elements
Elements are containers that hold components. They represent functional units like scratchpads, chat interfaces, or any custom functionality you want to add.

### Components
Components provide specific behaviors to Elements. There are typically four types of components for a functional Element:

1. **State Component** - Manages the element's data/state
2. **Action Handler Component** - Provides tools/actions the agent can use
3. **VEIL Producer Component** - Generates visual representations for the HUD
4. **Tool Provider Component** - Manages tool registration (standard component)

## Architecture Pattern

Here's the standard architecture for a new Element:

```
YourElement
├── StateComponent (manages data)
├── ActionHandlerComponent (provides tools)
├── VeilProducerComponent (generates VEIL)
└── ToolProviderComponent (standard - manages tools)
```

## Step-by-Step Guide

### Step 1: Create the State Component

The state component manages your element's data. Create a file like `elements/elements/components/your_feature/state_component.py`:

```python
from elements.component_registry import register_component
from elements.elements.base import Component
import logging

logger = logging.getLogger(__name__)

@register_component
class YourStateComponent(Component):
    """
    Manages the state/data for your element.
    """
    COMPONENT_TYPE = "YourStateComponent"
    
    def initialize(self, **kwargs) -> None:
        """Initialize the component state."""
        super().initialize(**kwargs)
        # Initialize your state structure
        self._state.setdefault('_data_items', [])
        self._state.setdefault('_metadata', {})
        logger.debug(f"YourStateComponent initialized for Element {self.owner.id}")
    
    def add_item(self, item_data: Dict[str, Any]) -> bool:
        """Add an item to the state."""
        try:
            self._state['_data_items'].append(item_data)
            # Notify VEIL producer of change
            veil_producer = self.get_sibling_component("YourVeilProducer")
            if veil_producer:
                veil_producer.emit_delta()
            return True
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return False
    
    def get_items(self) -> List[Dict[str, Any]]:
        """Get all items from state."""
        return list(self._state.get('_data_items', []))
    
    def clear_items(self) -> bool:
        """Clear all items."""
        try:
            self._state['_data_items'] = []
            # Notify VEIL producer
            veil_producer = self.get_sibling_component("YourVeilProducer")
            if veil_producer:
                veil_producer.emit_delta()
            return True
        except Exception as e:
            logger.error(f"Error clearing items: {e}")
            return False
```

### Step 2: Create the Action Handler Component

The action handler provides tools that agents can use. Create `elements/elements/components/your_feature/action_handler.py`:

```python
from elements.component_registry import register_component
from elements.elements.base import Component
from elements.elements.components.tool_provider import ToolProviderComponent, ToolParameter
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

@register_component
class YourActionHandler(Component):
    """
    Provides actions (tools) for your element.
    """
    COMPONENT_TYPE = "YourActionHandler"
    
    # Define required sibling components
    REQUIRED_SIBLING_COMPONENTS = [YourStateComponent, ToolProviderComponent]
    
    def initialize(self, **kwargs) -> None:
        """Initialize and register tools."""
        super().initialize(**kwargs)
        self._register_tools()
        logger.debug(f"YourActionHandler initialized for Element {self.owner.id}")
    
    def _get_state_component(self) -> Optional[YourStateComponent]:
        """Helper to get the state component."""
        return self.get_sibling_component(YourStateComponent)
    
    def _get_tool_provider(self) -> Optional[ToolProviderComponent]:
        """Helper to get the tool provider."""
        return self.get_sibling_component(ToolProviderComponent)
    
    def _register_tools(self) -> None:
        """Register all tools with the ToolProviderComponent."""
        tool_provider = self._get_tool_provider()
        if not tool_provider:
            logger.error("ToolProviderComponent not found. Cannot register tools.")
            return
        
        # Define tool parameters
        add_params: List[ToolParameter] = [
            {
                "name": "content",
                "type": "string",
                "description": "The content to add",
                "required": True
            },
            {
                "name": "metadata",
                "type": "object",
                "description": "Optional metadata",
                "required": False
            }
        ]
        
        # Register tools
        tool_provider.register_tool_function(
            name="add_to_your_element",
            description="Adds new content to your element",
            parameters_schema=add_params,
            tool_func=self.handle_add_item
        )
        
        tool_provider.register_tool_function(
            name="get_from_your_element",
            description="Retrieves all items from your element",
            parameters_schema=[],  # No parameters needed
            tool_func=self.handle_get_items
        )
        
        tool_provider.register_tool_function(
            name="clear_your_element",
            description="Clears all items from your element",
            parameters_schema=[],
            tool_func=self.handle_clear_items
        )
        
        logger.info(f"Tools registered for Element {self.owner.id}")
    
    def handle_add_item(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle adding an item to the element.
        
        Returns:
            Tool execution result dictionary
        """
        state_comp = self._get_state_component()
        if not state_comp:
            return {"success": False, "result": None, "error": "State component not found"}
        
        item_data = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        success = state_comp.add_item(item_data)
        
        if success:
            # Record event on timeline
            self._record_timeline_event("item_added", {
                "element_id": self.owner.id,
                "content_preview": content[:50] + ('...' if len(content) > 50 else '')
            })
            return {"success": True, "result": "Item added successfully", "error": None}
        else:
            return {"success": False, "result": None, "error": "Failed to add item"}
    
    def handle_get_items(self) -> Dict[str, Any]:
        """Handle retrieving items."""
        state_comp = self._get_state_component()
        if not state_comp:
            return {"success": False, "result": [], "error": "State component not found"}
        
        try:
            items = state_comp.get_items()
            return {"success": True, "result": items, "error": None}
        except Exception as e:
            return {"success": False, "result": [], "error": str(e)}
    
    def handle_clear_items(self) -> Dict[str, Any]:
        """Handle clearing all items."""
        state_comp = self._get_state_component()
        if not state_comp:
            return {"success": False, "result": None, "error": "State component not found"}
        
        item_count = len(state_comp.get_items())
        success = state_comp.clear_items()
        
        if success:
            self._record_timeline_event("items_cleared", {
                "element_id": self.owner.id,
                "cleared_count": item_count
            })
            return {"success": True, "result": f"Cleared {item_count} items", "error": None}
        else:
            return {"success": False, "result": None, "error": "Failed to clear items"}
    
    def _record_timeline_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event on the parent space timeline."""
        if not self.owner:
            return
        
        parent_space = self.owner.get_parent_object()
        if parent_space and hasattr(parent_space, 'add_event_to_primary_timeline'):
            event_payload = {
                "event_type": event_type,
                "data": data
            }
            parent_space.add_event_to_primary_timeline(event_payload)
```

### Step 3: Create the VEIL Producer Component

The VEIL producer generates visual representations. Create `elements/elements/components/your_feature/veil_producer.py`:

```python
from elements.component_registry import register_component
from elements.elements.components.base_component import VeilProducer
from elements.veil.veil_facets import EventFacet, StatusFacet, AmbientFacet
from elements.veil.facet_operations import FacetOperationBuilder, VEILFacetOperation
from typing import Dict, Any, List, Optional
import logging
import time

logger = logging.getLogger(__name__)

@register_component
class YourVeilProducer(VeilProducer):
    """
    Generates VEIL representation for your element.
    """
    COMPONENT_TYPE = "YourVeilProducer"
    
    def initialize(self, **kwargs) -> None:
        """Initialize the component."""
        super().initialize(**kwargs)
        self._state.setdefault('_last_item_ids', set())
        self._state.setdefault('_container_created', False)
        logger.debug(f"YourVeilProducer initialized for Element {self.owner.id}")
    
    def _get_state_component(self) -> Optional['YourStateComponent']:
        """Get the state component."""
        return self.get_sibling_component("YourStateComponent")
    
    def calculate_delta(self) -> Optional[List[VEILFacetOperation]]:
        """
        Calculate VEILFacet operations for your element.
        
        Returns:
            List of VEILFacetOperation instances
        """
        state_comp = self._get_state_component()
        if not state_comp:
            logger.error("State component not found")
            return None
        
        if not self.owner:
            logger.error("Owner not set")
            return None
        
        facet_operations = []
        owner_id = self.owner.id
        container_facet_id = f"{owner_id}_container"
        
        # Get current state
        current_items = state_comp.get_items()
        current_item_ids = {self._generate_item_id(item) for item in current_items}
        
        # 1. Handle container StatusFacet
        if not self._state.get('_container_created', False):
            # Create container
            container_state = {
                "element_id": owner_id,
                "element_name": self.owner.name,
                "item_count": len(current_items),
                "available_tools": self._get_enhanced_tools()
            }
            
            container_facet = StatusFacet(
                facet_id=container_facet_id,
                veil_timestamp=time.time(),
                owner_element_id=owner_id,
                status_type="container_created",
                current_state=container_state
            )
            
            facet_operations.append(FacetOperationBuilder.add_facet(container_facet))
            self._state['_container_created'] = True
            
        else:
            # Update container if needed
            container_state = {
                "item_count": len(current_items),
                "available_tools": self._get_enhanced_tools()
            }
            facet_operations.append(
                FacetOperationBuilder.update_facet(
                    container_facet_id,
                    {"current_state": container_state}
                )
            )
        
        # 2. Handle item additions/removals
        last_item_ids = self._state.get('_last_item_ids', set())
        
        # Added items
        for item in current_items:
            item_id = self._generate_item_id(item)
            if item_id not in last_item_ids:
                # Create EventFacet for new item
                item_facet = EventFacet(
                    facet_id=item_id,
                    veil_timestamp=time.time(),
                    owner_element_id=owner_id,
                    event_type="item_added",
                    content=item.get('content', ''),
                    links_to=container_facet_id
                )
                
                # Add item metadata
                item_facet.properties.update({
                    "metadata": item.get('metadata', {}),
                    "timestamp": item.get('timestamp', time.time())
                })
                
                facet_operations.append(FacetOperationBuilder.add_facet(item_facet))
        
        # Removed items
        removed_ids = last_item_ids - current_item_ids
        for removed_id in removed_ids:
            facet_operations.append(FacetOperationBuilder.remove_facet(removed_id))
        
        # 3. Create tools ambient facet if needed
        if self._should_emit_tools_ambient():
            tools_facet = self._create_tools_ambient_facet()
            if tools_facet:
                facet_operations.append(FacetOperationBuilder.add_facet(tools_facet))
        
        # Update state
        self._state['_last_item_ids'] = current_item_ids
        
        return facet_operations if facet_operations else None
    
    def _generate_item_id(self, item: Dict[str, Any]) -> str:
        """Generate unique ID for an item."""
        import hashlib
        content = str(item.get('content', ''))
        timestamp = str(item.get('timestamp', ''))
        hash_input = f"{content}_{timestamp}"
        return f"{self.owner.id}_item_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _get_enhanced_tools(self) -> List[Dict[str, Any]]:
        """Get enhanced tool definitions."""
        from elements.elements.components.tool_provider import ToolProviderComponent
        tool_provider = self.get_sibling_component(ToolProviderComponent)
        if tool_provider:
            return tool_provider.get_enhanced_tool_definitions()
        return []
    
    def _should_emit_tools_ambient(self) -> bool:
        """Check if we should emit tools ambient facet."""
        return bool(self._get_enhanced_tools())
    
    def _create_tools_ambient_facet(self) -> Optional[AmbientFacet]:
        """Create ambient facet for tools."""
        tools = self._get_enhanced_tools()
        if not tools:
            return None
        
        structured_content = {
            "tools": tools,
            "element_context": {
                "element_id": self.owner.id,
                "element_name": self.owner.name,
                "element_type": "your_element_type"
            },
            "tool_family": "your_element_tools"
        }
        
        ambient_facet = AmbientFacet(
            facet_id=f"{self.owner.id}_tools_ambient",
            owner_element_id=self.owner.id,
            ambient_type="your_element_tools",
            content=structured_content,
            trigger_threshold=1500
        )
        
        ambient_facet.properties.update({
            "data_format": "structured",
            "tools_count": len(tools),
            "element_type": "your_element_type"
        })
        
        return ambient_facet
```

### Step 4: Create the Prefab Definition

Add your element configuration to `elements/prefabs.py`:

```python
PREFABS = {
    # ... existing prefabs ...
    
    "your_element_type": {
        "description": "A custom element for [your functionality description]",
        "element_constructor_arg_keys": ["name", "description"],
        "components": [
            {"type": "YourStateComponent"},         # State management
            {"type": "ToolProviderComponent"},      # Standard tool management
            {"type": "YourActionHandler"},          # Your custom tools
            {"type": "YourVeilProducer"}           # VEIL representation
        ],
        "required_configs_for_element": ["name"],  # Required configuration
        "element_attributes_from_config": {
            # Map config keys to element attributes if needed
            "custom_attribute": "custom_attribute"
        }
    }
}
```

### Step 5: Configure Startup Elements (Optional)

If you want your element to be created automatically when an agent starts, add it to the agent configuration:

```json
{
  "agent_id": "example_agent",
  "name": "Example Agent",
  "startup_elements": [
    {
      "prefab": "your_element_type",
      "element_id": "your_element_{agent_id}",
      "element_config": {
        "name": "Your Element for {agent_name}",
        "description": "Custom element providing [functionality]",
        "custom_attribute": "custom_value"
      }
    }
  ]
}
```

## Component Communication Patterns

### 1. State Updates
When state changes, notify the VEIL producer:
```python
# In state component methods
veil_producer = self.get_sibling_component("YourVeilProducer")
if veil_producer:
    veil_producer.emit_delta()
```

### 2. Timeline Events
Record significant events to the parent space timeline:
```python
parent_space = self.owner.get_parent_object()
if parent_space and hasattr(parent_space, 'add_event_to_primary_timeline'):
    event_payload = {
        "event_type": "your_event_type",
        "data": {"key": "value"}
    }
    parent_space.add_event_to_primary_timeline(event_payload)
```

### 3. Tool Registration
Tools must be registered with the ToolProviderComponent during initialization.

## Best Practices

### 1. Component Dependencies
- Always check for required sibling components
- Use helper methods to access sibling components
- Handle cases where components might not be available

### 2. Error Handling
- Return structured error responses from tools: `{"success": bool, "result": Any, "error": Optional[str]}`
- Log errors appropriately for debugging
- Gracefully handle missing components or invalid states

### 3. State Management
- Keep state in the state component only
- Use `_state` dictionary for persistence
- Emit VEIL deltas when state changes

### 4. VEIL Generation
- Use VEILFacet architecture (StatusFacet, EventFacet, AmbientFacet)
- Include tool information in StatusFacets
- Track changes to minimize delta operations
- Add owner tracking for efficient filtering

### 5. Tool Design
- Keep tool functions focused and single-purpose
- Validate parameters before processing
- Return consistent result structures
- Use descriptive names and clear descriptions

## Advanced Topics

### Custom Element Classes
If you need a custom element class (beyond BaseElement):

```python
from elements.elements.base import BaseElement

class YourCustomElement(BaseElement):
    """Custom element with additional functionality."""
    
    def __init__(self, element_id: str, name: str, description: str, 
                 custom_param: str, **kwargs):
        super().__init__(element_id, name, description, **kwargs)
        self.custom_param = custom_param
    
    # Add custom methods if needed
```

Then specify it in your prefab:
```python
"element_class_name": "YourCustomElement"
```

### Handling External Events
If your element needs to react to external events:

1. Add event handlers to appropriate components
2. Implement `handle_event` method in components that need it
3. Define `HANDLED_EVENT_TYPES` in the component class

### Phase-Aware Processing
For components that need to handle replay phases differently:

```python
def _should_defer_content_processing(self) -> bool:
    """Check if we're in structural replay phase."""
    # Check owner and parent for replay state
    # Defer content during structural phase only
```

## Testing Your Element

### 1. Unit Testing
Test each component independently:
- State operations
- Tool execution
- VEIL generation

### 2. Integration Testing
Test the complete element:
- Create element from prefab
- Execute tools
- Verify VEIL output
- Check timeline events

### 3. Manual Testing
- Add element to agent configuration
- Start the system
- Use tools through agent interface
- Verify HUD display

## Common Patterns Reference

### Scratchpad Pattern
- Simple list storage
- Add/get/clear operations
- Content-based ID generation
- Minimal metadata

### Messaging Pattern
- Complex state with history
- External event handling
- Rich metadata and relationships
- Bulk operations support

Choose the pattern that best fits your use case and adapt as needed.

## Troubleshooting

### Component Not Found
- Ensure all components are registered with `@register_component`
- Check component imports
- Verify prefab configuration

### Tools Not Available
- Confirm ToolProviderComponent is in prefab
- Check tool registration in initialize()
- Verify parameter schemas

### VEIL Not Updating
- Ensure emit_delta() is called after state changes
- Check calculate_delta() implementation
- Verify owner tracking

### Timeline Events Missing
- Confirm parent space reference
- Check event payload structure
- Verify timeline component availability

## Conclusion

Creating new Elements in Connectome follows a consistent pattern of state management, tool provision, and visual representation through components. By following this guide and using the existing scratchpad and messaging implementations as reference, you can extend Connectome with custom functionality tailored to your needs.

Remember: Elements are modular, reusable, and should focus on a specific capability or feature. Keep them simple, well-documented, and follow the established patterns for consistency across the system.

