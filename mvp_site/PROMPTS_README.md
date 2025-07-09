# Prompts Directory

## Overview

This directory contains the AI system instructions that guide the Gemini AI service in generating appropriate responses for different aspects of the WorldArchitect.AI RPG experience. These prompts define the AI's behavior, knowledge, and response patterns.

## Directory Structure

```
prompts/
├── master_directive.md         # Core AI behavior and instruction hierarchy
├── game_state_instruction.md   # Game state management and data structures
├── narrative_system_instruction.md  # Story generation and narrative guidelines
├── mechanics_system_instruction.md  # Game mechanics and rules implementation
├── character_template.md       # Character creation and development templates
└── dnd_srd_instruction.md      # D&D 5e System Reference Document rules
```

## Prompt Files

### master_directive.md
- **Purpose**: Establishes the core AI personality and instruction hierarchy
- **Key Features**:
  - Defines the AI's role as a Game Master
  - Sets instruction precedence rules
  - Establishes authority levels for different prompt types
  - Provides meta-instructions for handling conflicts

### game_state_instruction.md
- **Purpose**: Defines game state management and data structure requirements
- **Key Features**:
  - JSON response format specifications
  - State update protocols
  - Entity schema definitions
  - Data validation requirements
  - Combat state management rules

### narrative_system_instruction.md
- **Purpose**: Guides story generation and narrative style
- **Key Features**:
  - Writing style guidelines
  - Story pacing and structure
  - Character development principles
  - Dialogue and description standards
  - Planning block requirements

### mechanics_system_instruction.md
- **Purpose**: Implements game mechanics and rules
- **Key Features**:
  - D&D 5e rule implementation
  - Dice rolling procedures
  - Combat mechanics
  - Skill checks and saves
  - Character progression rules

### character_template.md
- **Purpose**: Provides character creation and development templates
- **Key Features**:
  - Character sheet templates
  - Attribute assignment guidelines
  - Background and trait options
  - Character development arcs
  - NPC creation patterns

### dnd_srd_instruction.md
- **Purpose**: System Reference Document for D&D 5e rules
- **Key Features**:
  - Core rules reference
  - Spell descriptions
  - Monster statistics
  - Equipment and items
  - Condition effects

## Prompt Loading System

### Loading Order
The prompts are loaded in a specific order to ensure proper instruction hierarchy:

1. **master_directive.md** - Loaded first to establish authority
2. **game_state_instruction.md** - Loaded second for data structure authority
3. **Debug instructions** - Generated dynamically for technical functionality
4. **Selected prompts** - Loaded based on campaign configuration
5. **System reference** - D&D SRD loaded last for rule lookup

### Conditional Loading
Not all prompts are loaded for every request:

- **Always Loaded**: master_directive.md, game_state_instruction.md, dnd_srd_instruction.md
- **Conditionally Loaded**: narrative_system_instruction.md, mechanics_system_instruction.md
- **Context Dependent**: character_template.md (only during character creation)

## Prompt Management

### File Format
- **Format**: Markdown (.md) files
- **Encoding**: UTF-8
- **Structure**: Hierarchical with clear sections
- **Length**: Varies by complexity (500-3000 words each)

### Content Guidelines
1. **Clear Instructions**: Unambiguous directives
2. **Hierarchical Structure**: Organized with headers and sections
3. **Examples**: Concrete examples for complex concepts
4. **Consistency**: Consistent terminology and formatting
5. **Completeness**: Comprehensive coverage of domain area

### Version Control
- All prompts are version controlled with the codebase
- Changes require testing to ensure AI behavior remains consistent
- Critical prompts (master_directive, game_state) require careful review

## Prompt Architecture

### Instruction Hierarchy
```
1. Master Directive (Highest Authority)
   ├── Core AI personality and behavior
   ├── Instruction conflict resolution
   └── Meta-rules for prompt handling

2. Game State Instructions (Second Authority)
   ├── Data structure requirements
   ├── JSON response format
   └── State management protocols

3. Feature-Specific Instructions (Third Authority)
   ├── Narrative guidelines
   ├── Mechanics implementation
   └── Character templates

4. Reference Materials (Lowest Authority)
   ├── D&D SRD rules
   ├── World content
   └── Historical context
```

### Prompt Integration
- **System Instructions**: Combined into single system instruction
- **Dynamic Content**: Generated based on game state and context
- **Contextual Additions**: World content, debug instructions, etc.
- **Token Management**: Optimized for AI model token limits

## Development Guidelines

### Adding New Prompts
1. **Identify Need**: Determine what behavior needs guidance
2. **Define Scope**: Clearly scope the prompt's responsibility
3. **Write Content**: Follow existing format and style
4. **Test Integration**: Ensure compatibility with existing prompts
5. **Update Loading**: Modify gemini_service.py to load new prompt

### Modifying Existing Prompts
1. **Backup Current**: Save current version before changes
2. **Incremental Changes**: Make small, testable modifications
3. **Test Behavior**: Verify AI responses remain appropriate
4. **Document Changes**: Record what was changed and why
5. **Monitor Impact**: Watch for unintended behavioral changes

### Content Standards
- **Specificity**: Provide specific, actionable instructions
- **Clarity**: Use clear, unambiguous language
- **Completeness**: Cover all relevant scenarios
- **Consistency**: Maintain consistent tone and terminology
- **Testability**: Include guidance that can be validated

## Archived Prompts

### Removed Prompts
The following prompts have been archived to `prompt_archive/` directory:
- **calibration_instruction.md** (2,808 words) - AI calibration guidelines
- **destiny_ruleset.md** (1,012 words) - Destiny RPG system rules
- **dual_system_quick_reference.md** (354 words) - Multi-system support
- **attribute_conversion_guide.md** (822 words) - Attribute system conversion
- **character_sheet_template.md** (659 words) - Character sheet formatting

### Archival Reasons
- **Complexity Reduction**: Simplified instruction set for better AI performance
- **System Consolidation**: Moved from dual-system to D&D-only
- **Performance Optimization**: Reduced token usage for better response times
- **Maintenance**: Easier to maintain fewer, more focused prompts

## Performance Considerations

### Token Usage
- **Total Tokens**: ~15,000-20,000 tokens for full prompt set
- **Optimization**: Regular review to minimize token usage
- **Prioritization**: Most important instructions loaded first
- **Conditional Loading**: Only load necessary prompts for each request

### Response Quality
- **Instruction Fatigue**: Too many instructions can reduce compliance
- **Clarity**: Clear, specific instructions improve response quality
- **Hierarchy**: Well-defined hierarchy prevents instruction conflicts
- **Testing**: Regular testing ensures prompts work as intended

## Testing Prompts

### Validation Methods
1. **Response Quality**: Manual review of AI responses
2. **Behavior Consistency**: Consistent behavior across sessions
3. **Rule Compliance**: Adherence to game rules and mechanics
4. **Format Compliance**: Proper JSON formatting and structure
5. **Edge Cases**: Handling of unusual or unexpected scenarios

### Test Scenarios
- **Character Creation**: Complete character creation flow
- **Combat Scenarios**: Various combat situations
- **Story Generation**: Different narrative situations
- **State Management**: Complex state updates
- **Error Handling**: Invalid inputs and edge cases

## Maintenance

### Regular Tasks
1. **Review**: Monthly review of prompt effectiveness
2. **Update**: Keep prompts current with game changes
3. **Optimize**: Regularly optimize for token usage
4. **Test**: Continuous testing with new AI model versions
5. **Archive**: Remove obsolete or redundant content

### Quality Metrics
- **Response Accuracy**: AI responses match expected behavior
- **Rule Compliance**: Adherence to game mechanics
- **Consistency**: Consistent responses across similar situations
- **User Satisfaction**: Positive user feedback on AI behavior
- **Performance**: Response time and token efficiency

## Integration

### Code Integration
- **Loading**: Handled by `gemini_service.py`
- **Caching**: Prompts are cached after first load
- **Updates**: Require application restart to take effect
- **Constants**: Prompt paths defined in `constants.py`

### Configuration
- **Prompt Selection**: Based on campaign settings
- **Feature Flags**: Some prompts loaded conditionally
- **Debug Mode**: Additional instructions for debugging
- **World Content**: Dynamic content based on world selection