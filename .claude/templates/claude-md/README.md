# CLAUDE.md Template System

**Content-Aware Template Library for Directory-Specific CLAUDE.md Generation**

## Overview

This template system provides comprehensive, content-aware templates for generating contextually relevant CLAUDE.md files across different types of directories. Each template follows proven POC patterns with hierarchical inheritance and actual directory analysis.

## Template Types

### 1. base-template.md
**Purpose**: Core template with universal structure and variable substitution system
**Use Cases**: 
- Custom module types not covered by specialized templates
- Base structure for creating new specialized templates
- General-purpose directory documentation

**Key Variables**:
- `{{MODULE_TYPE}}` - Type description (e.g., "Configuration & Settings")
- `{{TECHNOLOGY_STACK}}` - Technology description (e.g., "Python/YAML/Docker")
- `{{RELATIVE_PATH_TO_ROOT}}` - Calculated path to root CLAUDE.md
- `{{DIRECTORY_CONTENTS_ANALYSIS}}` - Actual file analysis content
- `{{MODULE_SPECIFIC_PROTOCOLS}}` - Technology-specific rules and protocols

### 2. frontend.md
**Purpose**: React/TypeScript frontend component directories
**Use Cases**:
- React component libraries (`src/components/`)
- Frontend application modules
- UI component systems
- TypeScript frontend codebases

**Key Variables**:
- `{{COMPONENT_COUNT}}` - Number of components
- `{{COMPONENT_LIST}}` - Detailed component inventory
- `{{SUB_MODULES}}` - Sub-directory analysis (ui/, figma/, etc.)
- `{{PRIMARY_FEATURES}}` - Main functionality description

### 3. testing.md
**Purpose**: Testing infrastructure and test suite directories
**Use Cases**:
- Test directories (`tests/`, `__tests__/`)
- Testing infrastructure modules
- Quality assurance systems
- Mock service implementations

**Key Variables**:
- `{{TEST_TECHNOLOGY_STACK}}` - Testing tech (pytest/Playwright/Jest)
- `{{TEST_COUNT}}` - Number of test files
- `{{TEST_CATEGORIES}}` - Categorized test analysis
- `{{CRITICAL_AREAS}}` - Important testing focus areas
- `{{EXTERNAL_DEPENDENCIES}}` - Services being mocked

### 4. config.md
**Purpose**: Configuration management and settings directories
**Use Cases**:
- Configuration directories (`config/`, `settings/`)
- Environment management systems
- Deployment configuration modules
- Secret and credential management

**Key Variables**:
- `{{CONFIG_TECHNOLOGY_STACK}}` - Config tech (YAML/JSON/dotenv)
- `{{CONFIG_COUNT}}` - Number of configuration files
- `{{PARAMETER_TABLE}}` - Configuration parameter documentation
- `{{API_KEY_MANAGEMENT}}` - Security protocols
- `{{ENVIRONMENT_FILES}}` - Environment-specific configurations

### 5. commands.md
**Purpose**: Command system and automation directories
**Use Cases**:
- Command directories (`.claude/commands/`)
- CLI tool implementations
- Automation script collections
- Workflow orchestration systems

**Key Variables**:
- `{{COMMAND_TECHNOLOGY_STACK}}` - Command tech (Markdown/Python/Shell)
- `{{COMMAND_COUNT}}` - Number of command files
- `{{COMMAND_CATEGORIES}}` - Command categorization
- `{{SPECIALIZED_USAGE}}` - Specific usage examples
- `{{COMMAND_SCOPE}}` - Scope of command functionality

## Variable Substitution System

### Universal Variables (All Templates)
```
{{DIRECTORY_NAME}}          # Target directory name
{{RELATIVE_PATH_TO_ROOT}}    # Calculated path to root CLAUDE.md
{{PARENT_PROJECT}}          # Project name (e.g., "WorldArchitect.AI")
{{PROJECT_NAME}}            # Full project name
{{PROJECT_SLUG}}            # URL-safe project identifier
```

### Content Analysis Variables
```
{{DIRECTORY_CONTENTS_ANALYSIS}}  # Complete file analysis section
{{FILE_LIST}}                   # Raw file listing
{{FILE_COUNT}}                  # Total number of files
{{SUB_DIRECTORIES}}             # Sub-directory analysis
```

### Technology-Specific Variables
```
{{TECHNOLOGY_STACK}}        # Primary technology description
{{MODULE_PURPOSE}}          # Module's specific purpose
{{MODULE_ROLE}}             # Module's role in project
{{DEVELOPMENT_WORKFLOW}}    # Technology-appropriate workflows
{{QUICK_REFERENCE_ITEMS}}   # Template-specific quick reference
```

## Usage Patterns

### Automatic Deployment
Templates are designed for automated deployment via content-aware analysis:

1. **Directory Analysis**: Scan directory contents to determine technology stack
2. **Template Selection**: Choose appropriate template based on analysis
3. **Variable Substitution**: Replace template variables with actual content
4. **Validation**: Ensure all required sections are populated
5. **Deployment**: Write final CLAUDE.md to target directory

### Manual Customization
Templates can be manually customized for specific needs:

1. **Copy Base Template**: Start with most appropriate template
2. **Update Variables**: Replace placeholder variables with actual content
3. **Add Specific Protocols**: Include directory-specific rules and protocols
4. **Validate Inheritance**: Ensure correct relative path to root CLAUDE.md
5. **Test Content**: Verify all sections provide value for developers

## Content-Aware Generation Features

### Actual File Analysis
- Real file inventory vs. generic placeholders
- Technology detection based on file extensions
- Directory structure analysis for sub-modules
- File count and categorization

### Proven POC Patterns
- Hierarchical inheritance from root CLAUDE.md
- Module-specific protocol sections
- Comprehensive directory contents analysis
- Technology-appropriate development workflows
- Consistent quick reference sections

### Quality Standards
- Production-ready content depth
- Specific examples and command patterns
- Security considerations where applicable
- Integration with existing project workflows
- Maintenance and testing guidance

## Integration with Deployment System

These templates are designed to integrate with the selective CLAUDE.md deployment system:

1. **High-Value Directory Identification**: Automated analysis identifies directories needing CLAUDE.md
2. **Template Matching**: Content analysis determines appropriate template
3. **Variable Population**: Directory inspection populates template variables
4. **Quality Validation**: Generated content validated against quality standards
5. **Deployment Execution**: Final CLAUDE.md files deployed to target directories

## Template Development Guidelines

### Adding New Templates
1. **Follow POC Patterns**: Use existing templates as structure reference
2. **Include Variable System**: Support comprehensive variable substitution
3. **Provide Real Examples**: Include actual file reference patterns
4. **Technology Focus**: Target specific technology stacks or use cases
5. **Quality Standards**: Match comprehensiveness of existing templates

### Template Maintenance
1. **Version Consistency**: Keep templates aligned with root CLAUDE.md updates
2. **Variable Updates**: Add new variables as deployment system evolves
3. **Content Accuracy**: Ensure examples match current project patterns
4. **Documentation**: Update this README when adding new templates or variables

## Success Metrics

### Template Effectiveness
- **Relevance**: 95%+ of content applicable to target directory
- **Completeness**: All major aspects of directory covered
- **Actionability**: Clear guidance for developers working in directory
- **Consistency**: Aligned with project-wide development protocols

### Deployment Success
- **Coverage**: 80-100 high-value directories covered
- **Quality**: Generated content meets POC quality standards  
- **Maintenance**: Templates remain current with project evolution
- **Developer Value**: Measurable improvement in development workflow efficiency