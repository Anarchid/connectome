# Testing Element Creation Capability

## Quick Test Scenarios

### Scenario 1: Basic Element Creation

**User Input:**
```
I need to track some ideas for our project. Can you help me organize them?
```

**Expected Agent Response:**
```xml
Let me create a scratchpad to help you track project ideas.

<list_element_templates>

I can create a simple scratchpad for storing your project ideas. Let me set that up for you.

<create_element template="simple_scratchpad" name="Project Ideas Tracker" description="A place to collect and organize project ideas">

Great! I've created a "Project Ideas Tracker" for you. You can now add ideas to it. What's the first idea you'd like to record?
```

**User Follow-up:**
```
Add: "Implement user authentication with OAuth2"
```

**Expected Agent Response:**
```xml
<add_note_to_scratchpad source="Project Ideas Tracker">
Implement user authentication with OAuth2
</add_note_to_scratchpad>

I've added that idea to your tracker. Would you like to add more ideas?
```

### Scenario 2: Multiple Elements

**User Input:**
```
I need separate places to track bugs and feature requests
```

**Expected Agent Response:**
```xml
I'll create two separate scratchpads for you - one for bugs and one for features.

<create_element template="simple_scratchpad" name="Bug Tracker" description="Track bugs and issues">

<create_element template="simple_scratchpad" name="Feature Requests" description="Track feature requests and enhancements">

Perfect! I've created:
1. "Bug Tracker" - for tracking bugs and issues
2. "Feature Requests" - for tracking new features and enhancements

You can now add items to either tracker. What would you like to record first?
```

### Scenario 3: Viewing Current Elements

**User Input:**
```
What tracking tools do I have available?
```

**Expected Agent Response:**
```xml
Let me show you all the elements and tools currently available to you.

<list_my_elements>

You currently have these elements available:

1. **Agent Scratchpad** (Default)
   - add_note_to_scratchpad
   - get_notes_from_scratchpad
   - clear_all_scratchpad_notes

2. **Project Ideas Tracker**
   - add_note_to_scratchpad
   - get_notes_from_scratchpad
   - clear_all_scratchpad_notes

3. **Bug Tracker**
   - add_note_to_scratchpad
   - get_notes_from_scratchpad
   - clear_all_scratchpad_notes

4. **Feature Requests**
   - add_note_to_scratchpad
   - get_notes_from_scratchpad
   - clear_all_scratchpad_notes

Each of these can store notes independently. Which one would you like to work with?
```

### Scenario 4: Complex Workflow

**User Input:**
```
I'm starting a code review. Help me organize my findings.
```

**Expected Agent Response:**
```xml
I'll help you organize your code review findings. Let me set up a dedicated space for this.

<create_element template="simple_scratchpad" name="Code Review Notes" description="Findings from code review session">

I've created "Code Review Notes" for you. As you review the code, you can tell me about:
- Issues or bugs you find
- Suggestions for improvements
- Questions for the author
- Positive feedback

Just let me know what you find, and I'll organize it in your review notes.
```

## Validation Checklist

### Tool Visibility
- [ ] `list_element_templates` appears in available tools
- [ ] `create_element` appears in available tools
- [ ] `list_my_elements` appears in available tools

### Element Creation
- [ ] Elements are created with unique IDs
- [ ] Creation returns success with tool list
- [ ] Activation event is emitted

### Tool Availability
- [ ] New element tools appear immediately after creation
- [ ] Tools can be called with source parameter
- [ ] Tools route correctly to the right element

### VEIL Updates
- [ ] SpaceVeilProducer emits tool ambient facets
- [ ] New elements appear in VEIL with their tools
- [ ] Tool aggregation includes all elements

### Persistence
- [ ] Created elements persist across restarts (via replay)
- [ ] Element state is maintained
- [ ] Timeline events are recorded

## Error Cases to Test

1. **Invalid Template**
   ```xml
   <create_element template="nonexistent_template" name="Test">
   ```
   Should return error about unknown template

2. **Missing Required Fields**
   ```xml
   <create_element template="simple_scratchpad">
   ```
   Should return error about missing name

3. **Duplicate Names** (Allowed)
   ```xml
   <create_element template="simple_scratchpad" name="Notes">
   <create_element template="simple_scratchpad" name="Notes">
   ```
   Should create two elements with same name but different IDs

## Performance Considerations

- Element creation should complete in < 100ms
- Tool aggregation should not significantly slow down
- VEIL updates should remain responsive
- Memory usage should scale linearly with elements
