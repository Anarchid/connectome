# Example Configuration for ToolTextParsingLoopComponent

This document shows how to configure an agent to use the new `ToolTextParsingLoopComponent` for testing text-based tool parsing.

## Environment Configuration

Create a `.env` file with the following configuration:

```bash
# LLM Configuration
CONNECTOME_LLM_TYPE=litellm
CONNECTOME_LLM_DEFAULT_MODEL=gpt-4
CONNECTOME_LLM_API_KEY=your_openai_api_key_here

# Logging Configuration (recommended for testing)
CONNECTOME_LOG_LEVEL=DEBUG
CONNECTOME_LOG_TO_FILE=true
CONNECTOME_LOG_FILE_PATH=logs/connectome.log

# Activity Adapters (Discord, Telegram, etc.)
CONNECTOME_ACTIVITY_ADAPTERS_JSON=[{"id": "discord_adapter_1", "url": "http://localhost:5001", "auth_token": null}]

# Agents Configuration - Using ToolTextParsingLoopComponent
CONNECTOME_AGENTS_JSON=[{
  "agent_id": "text_parsing_agent", 
  "name": "Text Parsing Agent", 
  "description": "An agent that uses text-parsing for tool calls instead of the tool_call API", 
  "agent_loop_component_type_name": "ToolTextParsingLoopComponent", 
  "platform_aliases": {"discord_adapter_1": "TextBot"}, 
  "handles_direct_messages_from_adapter_ids": ["discord_adapter_1"]
}]
```

## Agent Loop Component Types

The system now supports multiple agent loop components:

- **`SimpleRequestResponseLoopComponent`** (default): Uses the LLM's native tool_call API
- **`ToolTextParsingLoopComponent`** (new): Parses tool calls from text responses, supports multiple tool calls per response

## Testing Multiple Tool Calls

With `ToolTextParsingLoopComponent`, you can test scenarios where the agent makes multiple tool calls in a single response:

```json
// Example LLM response that the text parsing loop can handle:
{
  "response": "I'll help you with that. Let me send a message and then check another channel.\n\n<tool_calls>\n[{\"name\": \"cha_123__send_message\", \"parameters\": {\"text\": \"Hello from the agent!\"}}, {\"name\": \"cha_456__get_recent_messages\", \"parameters\": {\"limit\": 5}}]\n</tool_calls>"
}
```

## Comparison of Agent Loop Types

| Feature | SimpleRequestResponseLoopComponent | ToolTextParsingLoopComponent |
|---------|-----------------------------------|------------------------------|
| Tool Call API | Native LLM tool_call API | Text parsing (JSON/XML) |
| Multiple Tools/Response | No (LLM limitation) | Yes |
| Tool Aggregation | No | Yes (shows `send_message` instead of prefixed variants) |
| LLM Compatibility | OpenAI, Anthropic (tool_call) | Any LLM that can follow instructions |
| Parsing Control | LLM-controlled | Full application control |
| Error Handling | LLM provider errors | Custom parsing with fallbacks |

## Configuration Notes

1. **Model Selection**: Text parsing works with any instruction-following model, while tool_call API requires specific model support
2. **Tool Rendering**: The new component uses aggregated tool definitions in the context, showing consolidated tools instead of prefixed duplicates
3. **Error Recovery**: Text parsing provides better error recovery and partial execution capabilities 