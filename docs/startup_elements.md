# Startup Elements Configuration

## Overview

The startup elements feature allows agents to be configured with additional elements that are automatically created when the InnerSpace is initialized. This enables customization of agent capabilities without modifying the core code.

## Configuration

Startup elements are configured in the agent's JSON configuration under the `startup_elements` field:

```json
{
  "agent_id": "example_agent",
  "name": "Example Agent",
  "startup_elements": [
    {
      "prefab": "simple_scratchpad",
      "element_id": "notes_{agent_id}",
      "element_config": {
        "name": "Notes",
        "description": "Notes for {agent_name}"
      }
    }
  ]
}
```

## Element Specification

Each startup element specification supports the following fields:

- **prefab** (required): The name of the prefab to use (must exist in `elements/prefabs.py`)
- **element_id** (required): Unique ID for the element (supports template variables)
- **element_config** (optional): Configuration passed to the element constructor
- **component_config_overrides** (optional): Override configurations for specific components
- **enabled_by_default** (optional): Boolean to enable/disable element creation (default: true)

## Template Variables

The following template variables are supported in `element_id` and `element_config` values:

- `{agent_id}` - The unique ID of the agent
- `{agent_name}` - The display name of the agent
- `{agent_description}` - The description of the agent

## Examples

### Basic Scratchpad
```json
{
  "prefab": "simple_scratchpad",
  "element_id": "notes_{agent_id}",
  "element_config": {
    "name": "Notes",
    "description": "Personal notes for {agent_name}"
  }
}
```

### Multiple Storage Elements
```json
"startup_elements": [
  {
    "prefab": "simple_scratchpad",
    "element_id": "research_{agent_id}",
    "element_config": {
      "name": "Research Notes",
      "description": "Research findings"
    }
  },
  {
    "prefab": "simple_scratchpad",
    "element_id": "tasks_{agent_id}",
    "element_config": {
      "name": "Task List",
      "description": "Todo items"
    }
  }
]
```

### Conditional Elements
```json
{
  "prefab": "simple_scratchpad",
  "element_id": "optional_{agent_id}",
  "element_config": {
    "name": "Optional Feature",
    "description": "Only created if enabled"
  },
  "enabled_by_default": false
}
```

## Implementation Details

1. **Processing Order**: Startup elements are created after the default scratchpad but before agent loop initialization
2. **Error Handling**: If an element fails to create, an error is logged but processing continues
3. **Duplicate Prevention**: Element IDs must be unique within the InnerSpace
4. **Template Substitution**: Templates are recursively substituted in all string values

## Future Enhancements

The following enhancements are planned for future releases:

1. **Environment Variable Substitution**: `{env:VARIABLE_NAME}` syntax
2. **Dynamic Variables**: `{timestamp}`, `{uuid}`, etc.
3. **Conditional Logic**: Create elements based on complex conditions
4. **Element Dependencies**: Specify dependencies between elements
5. **Custom Prefab Loading**: Load prefabs from external files
6. **Runtime Element Creation**: Allow agents to create elements dynamically

## Migration Path

Currently, the default scratchpad is still hard-coded in `InnerSpace.__init__`. The migration path is:

1. **Current**: Default scratchpad is hard-coded, additional elements via startup_elements
2. **Next**: Make default scratchpad optional via configuration flag
3. **Future**: Move all default elements to configuration
4. **Final**: Provide migration tools for existing deployments

## Best Practices

1. **Use Descriptive IDs**: Include the element's purpose in its ID
2. **Template Variables**: Use template variables for agent-specific information
3. **Prefab Reuse**: Reuse existing prefabs when possible
4. **Error Handling**: Always test configurations with invalid prefabs
5. **Documentation**: Document custom prefabs and their requirements

## Troubleshooting

### Element Not Created
- Check logs for error messages
- Verify prefab name exists in `prefabs.py`
- Ensure element_id is unique
- Check required fields in element_config

### Template Not Substituted
- Verify template variable syntax is correct
- Check that the variable is supported
- Look for typos in variable names

### Component Errors
- Verify component type names in overrides
- Check that override values are valid for the component
- Review component initialization logs

