# Text Processor

A Python 3.11+ command-line utility for common text processing operations including word/character/line counting, text replacement, and case conversion.

## Features

- **Count Operations**: Count words, characters (with/without spaces), lines, and paragraphs
- **Text Replacement**: Replace text with case-sensitive or case-insensitive matching
- **Case Conversion**: Convert text to uppercase, lowercase, title case, or capitalize
- **Flexible Input**: Read from files or stdin
- **Output Options**: Display results in terminal or save to files
- **Comprehensive Statistics**: Get detailed text analysis in one command

## Installation

```bash
# Clone or copy the text_processor directory
cd text_processor

# Install dependencies (optional, for development)
pip install -r requirements.txt
```

## Usage

### Basic Syntax

```bash
python text_processor.py <command> [options]
```

### Count Operations

Count words in a file:
```bash
python text_processor.py count words -f input.txt
```

Count characters (including spaces) from stdin:
```bash
echo "Hello World" | python text_processor.py count characters
```

Count characters excluding spaces:
```bash
python text_processor.py count characters --no-spaces -f input.txt
```

Count lines:
```bash
python text_processor.py count lines -f document.txt
```

Get comprehensive statistics:
```bash
python text_processor.py count all -f document.txt
```

### Text Replacement

Replace text (case sensitive):
```bash
python text_processor.py replace "old text" "new text" -f input.txt
```

Replace text (case insensitive) and save to file:
```bash
python text_processor.py replace "hello" "hi" -f input.txt -o output.txt -i
```

Replace from stdin:
```bash
echo "Hello World" | python text_processor.py replace "World" "Universe"
```

### Case Conversion

Convert to uppercase:
```bash
python text_processor.py case upper -f input.txt
```

Convert to title case and save to file:
```bash
python text_processor.py case title -f input.txt -o output.txt
```

Convert from stdin:
```bash
echo "hello world" | python text_processor.py case capitalize
```

Available case types:
- `upper`: UPPERCASE
- `lower`: lowercase
- `title`: Title Case
- `capitalize`: Capitalize first letter only

## API Reference

### Core Operations Module (`operations.py`)

#### `count_words(text: str) -> int`
Count the number of words in text.

#### `count_characters(text: str, include_spaces: bool = True) -> int`
Count characters, optionally excluding whitespace.

#### `count_lines(text: str) -> int`
Count the number of lines in text.

#### `replace_text(text: str, old: str, new: str, case_sensitive: bool = True) -> str`
Replace occurrences of old text with new text.

#### `convert_case(text: str, case_type: str) -> str`
Convert text case. Supported types: 'upper', 'lower', 'title', 'capitalize'.

#### `get_text_stats(text: str) -> Dict[str, Any]`
Get comprehensive text statistics including word count, character counts, lines, and paragraphs.

## Command Line Options

### Global Options
- `-f, --file`: Input file path (default: read from stdin)
- `-h, --help`: Show help message

### Count Command
- `type`: Type of count (`words`, `characters`, `lines`, `all`)
- `--no-spaces`: Exclude spaces from character count

### Replace Command
- `old`: Text to replace
- `new`: Replacement text
- `-o, --output`: Output file (default: stdout)
- `-i, --ignore-case`: Case-insensitive replacement

### Case Command
- `type`: Case conversion type (`upper`, `lower`, `title`, `capitalize`)
- `-o, --output`: Output file (default: stdout)

## Examples

### Word Processing Pipeline
```bash
# Count words in multiple files
python text_processor.py count words -f file1.txt
python text_processor.py count words -f file2.txt

# Replace and convert case in pipeline
cat input.txt | \
  python text_processor.py replace "old" "new" | \
  python text_processor.py case title > output.txt
```

### Text Analysis
```bash
# Get comprehensive statistics
python text_processor.py count all -f document.txt

# Output:
# Text Statistics:
#   Words: 1500
#   Characters (with spaces): 8750
#   Characters (without spaces): 7200
#   Lines: 75
#   Paragraphs: 12
```

### Batch Processing
```bash
# Process multiple files with same operation
for file in *.txt; do
  python text_processor.py case upper -f "$file" -o "upper_$file"
done
```

## Testing

Run the test suite:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=text_processor

# Run specific test file
pytest tests/test_operations.py -v
```

## Error Handling

The tool provides informative error messages for common issues:

- **File not found**: Clear message when input file doesn't exist
- **Permission denied**: Helpful message for read/write permission issues
- **Invalid arguments**: Descriptive help for incorrect command usage
- **Unicode errors**: Graceful handling of encoding issues

## Development

### Code Structure
```
text_processor/
├── __init__.py           # Package initialization
├── operations.py         # Core text processing logic
├── text_processor.py     # CLI interface
├── requirements.txt      # Dependencies
├── README.md            # Documentation
└── tests/               # Test suite
    ├── __init__.py
    ├── test_operations.py
    └── test_cli.py
```

### Code Quality
- Follows PEP 8 style guidelines
- Type hints for better code documentation
- Comprehensive error handling
- 90%+ test coverage
- No external dependencies for core functionality

## License

This project is part of WorldArchitect.AI and follows the same licensing terms.

## Contributing

1. Ensure all tests pass: `pytest tests/ -v`
2. Check code coverage: `pytest tests/ --cov=text_processor`
3. Follow PEP 8 style guidelines
4. Add tests for new functionality
