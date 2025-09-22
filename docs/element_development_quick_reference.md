# Element Development Quick Reference

## Component Checklist

When creating a new Element, you need these components:

- [ ] **State Component** (YourStateComponent)
  - Inherits from: `Component`
  - Purpose: Manages element data/state
  - Key methods: `add_*()`, `get_*()`, `clear_*()`, `update_*()`
  - Must emit VEIL delta after state changes

- [ ] **Action Handler** (YourActionHandler)
  - Inherits from: `Component`
  - Purpose: Provides tools/actions
  - Key methods: `handle_*()` for each tool
  - Must register tools in `initialize()`
  - Returns: `{"success": bool, "result": Any, "error": Optional[str]}`

- [ ] **VEIL Producer** (YourVeilProducer)
  - Inherits from: `VeilProducer`
  - Purpose: Generates visual representation
  - Key method: `calculate_delta()`
  - Uses: StatusFacet, EventFacet, AmbientFacet

- [ ] **Tool Provider** (Standard Component)
  - Already implemented
  - Just include in prefab: `{"type": "ToolProviderComponent"}`

## File Structure

```
elements/elements/components/your_feature/
├── __init__.py
├── state_component.py      # YourStateComponent
├── action_handler.py       # YourActionHandler
└── veil_producer.py       # YourVeilProducer
```

## Prefab Template

```python
"your_element_type": {
    "description": "Brief description of what this element does",
    "element_constructor_arg_keys": ["name", "description"],
    "components": [
        {"type": "YourStateComponent"},
        {"type": "ToolProviderComponent"},
        {"type": "YourActionHandler"},
        {"type": "YourVeilProducer"}
    ],
    "required_configs_for_element": ["name"],
    "element_attributes_from_config": {
        "config_key": "element_attribute"
    }
}
```

## Common Imports

```python
# For all components
from elements.component_registry import register_component
import logging
logger = logging.getLogger(__name__)

# For State Component
from elements.elements.base import Component

# For Action Handler
from elements.elements.components.tool_provider import ToolProviderComponent, ToolParameter
from typing import Dict, Any, List, Optional

# For VEIL Producer
from elements.elements.components.base_component import VeilProducer
from elements.veil.veil_facets import EventFacet, StatusFacet, AmbientFacet
from elements.veil.facet_operations import FacetOperationBuilder, VEILFacetOperation
```

## Key Patterns

### Getting Sibling Components
```python
state_comp = self.get_sibling_component("YourStateComponent")
tool_provider = self.get_sibling_component(ToolProviderComponent)
```

### Emitting VEIL Updates
```python
veil_producer = self.get_sibling_component("YourVeilProducer")
if veil_producer:
    veil_producer.emit_delta()
```

### Recording Timeline Events
```python
parent_space = self.owner.get_parent_object()
if parent_space and hasattr(parent_space, 'add_event_to_primary_timeline'):
    event_payload = {
        "event_type": "your_event_type",
        "data": {"key": "value"}
    }
    parent_space.add_event_to_primary_timeline(event_payload)
```

### Tool Registration
```python
tool_provider.register_tool_function(
    name="tool_name",
    description="What this tool does",
    parameters_schema=[
        {
            "name": "param_name",
            "type": "string",  # string|number|boolean|array|object
            "description": "What this parameter is for",
            "required": True
        }
    ],
    tool_func=self.handle_tool_name
)
```

### Tool Response Format
```python
return {
    "success": True,  # or False
    "result": result_data,  # The actual result
    "error": None  # or error message string
}
```

## VEILFacet Types

### StatusFacet (Container State)
```python
StatusFacet(
    facet_id=f"{owner_id}_container",
    veil_timestamp=time.time(),
    owner_element_id=owner_id,
    status_type="container_created",
    current_state={
        "element_id": owner_id,
        "element_name": self.owner.name,
        "item_count": len(items),
        "available_tools": tool_list
    }
)
```

### EventFacet (Content Items)
```python
EventFacet(
    facet_id=item_id,
    veil_timestamp=time.time(),
    owner_element_id=owner_id,
    event_type="item_added",
    content=item_content,
    links_to=container_facet_id
)
```

### AmbientFacet (Tool Information)
```python
AmbientFacet(
    facet_id=f"{owner_id}_tools_ambient",
    owner_element_id=owner_id,
    ambient_type="your_tools_family",
    content=structured_tool_data,
    trigger_threshold=1500
)
```

## Testing Commands

```bash
# 1. Add your element to agent config in .env
# 2. Start the system
python host/main.py

# 3. Test in conversation
# The agent should have access to your tools
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Tools not appearing | Check ToolProviderComponent is in prefab and tool registration in initialize() |
| VEIL not updating | Ensure emit_delta() is called after state changes |
| Component not found | Verify @register_component decorator and imports |
| State not persisting | Use self._state dictionary, not instance variables |
| Timeline events missing | Check parent space reference and event payload structure |

## Remember

1. **Components are singleton per Element** - One instance of each component type
2. **State lives in State Component only** - Other components read/modify through it
3. **Tools must be registered in initialize()** - Not in __init__
4. **VEIL updates are reactive** - Emit delta after state changes
5. **Error handling is important** - Always return structured responses

