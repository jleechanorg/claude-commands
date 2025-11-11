"""
Integration tests for text_processor CLI functionality.
"""

import os
import tempfile
from io import StringIO
from unittest.mock import mock_open, patch

import pytest

from text_processor.text_processor import (
    create_parser,
    handle_case_command,
    handle_count_command,
    handle_replace_command,
    main,
    read_input,
)


class TestReadInput:
    """Test input reading functionality."""

    def test_read_input_from_file(self):
        """Test reading input from a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = read_input(temp_path)
            assert result == "test content"
        finally:
            os.unlink(temp_path)

    def test_read_input_file_not_found(self):
        """Test reading from non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            read_input("/non/existent/file.txt")

    @patch('builtins.open', mock_open())
    def test_read_input_permission_error(self):
        """Test permission error when reading file."""
        with patch('builtins.open', side_effect=PermissionError):
            with pytest.raises(PermissionError, match="Permission denied"):
                read_input("protected_file.txt")

    @patch('sys.stdin')
    def test_read_input_from_stdin(self, mock_stdin):
        """Test reading input from stdin."""
        mock_stdin.read.return_value = "stdin content"
        result = read_input()
        assert result == "stdin content"

    @patch('builtins.open', mock_open())
    def test_read_input_unicode_error(self):
        """Test Unicode decode error."""
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
            with pytest.raises(ValueError, match="Unable to decode file as UTF-8"):
                read_input("binary_file.bin")


class TestHandleCountCommand:
    """Test count command handling."""

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_count_words(self, mock_print, mock_read):
        """Test word count command."""
        mock_read.return_value = "hello world test"

        class Args:
            file = "test.txt"
            type = "words"
            no_spaces = False

        handle_count_command(Args())
        mock_print.assert_called_with("Words: 3")

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_count_characters_with_spaces(self, mock_print, mock_read):
        """Test character count with spaces."""
        mock_read.return_value = "hello world"

        class Args:
            file = "test.txt"
            type = "characters"
            no_spaces = False

        handle_count_command(Args())
        mock_print.assert_called_with("Characters (with spaces): 11")

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_count_characters_without_spaces(self, mock_print, mock_read):
        """Test character count without spaces."""
        mock_read.return_value = "hello world"

        class Args:
            file = "test.txt"
            type = "characters"
            no_spaces = True

        handle_count_command(Args())
        mock_print.assert_called_with("Characters (without spaces): 10")

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_count_lines(self, mock_print, mock_read):
        """Test line count command."""
        mock_read.return_value = "line1\nline2\nline3"

        class Args:
            file = "test.txt"
            type = "lines"
            no_spaces = False

        handle_count_command(Args())
        mock_print.assert_called_with("Lines: 3")

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_count_all(self, mock_print, mock_read):
        """Test all statistics command."""
        mock_read.return_value = "Hello world.\n\nSecond paragraph."

        class Args:
            file = "test.txt"
            type = "all"
            no_spaces = False

        handle_count_command(Args())

        # Check that all statistics are printed
        calls = mock_print.call_args_list
        assert any("Text Statistics:" in str(call) for call in calls)
        assert any("Words: 4" in str(call) for call in calls)

    @patch('text_processor.text_processor.read_input')
    @patch('sys.stderr', new_callable=StringIO)
    def test_handle_count_file_error(self, mock_stderr, mock_read):
        """Test count command with file error."""
        mock_read.side_effect = FileNotFoundError("File not found: test.txt")

        class Args:
            file = "test.txt"
            type = "words"
            no_spaces = False

        with pytest.raises(SystemExit, match="1"):
            handle_count_command(Args())

        assert "Error: File not found: test.txt" in mock_stderr.getvalue()


class TestHandleReplaceCommand:
    """Test replace command handling."""

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_replace_stdout(self, mock_print, mock_read):
        """Test replace command with stdout output."""
        mock_read.return_value = "hello world"

        class Args:
            file = "test.txt"
            old = "world"
            new = "universe"
            output = None
            ignore_case = False

        handle_replace_command(Args())
        mock_print.assert_called_with("hello universe", end='')

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_handle_replace_file_output(self, mock_print, mock_file, mock_read):
        """Test replace command with file output."""
        mock_read.return_value = "hello world"

        class Args:
            file = "input.txt"
            old = "world"
            new = "universe"
            output = "output.txt"
            ignore_case = False

        handle_replace_command(Args())

        mock_file.assert_called_with("output.txt", 'w', encoding='utf-8')
        mock_file().write.assert_called_with("hello universe")
        mock_print.assert_called_with("Output written to: output.txt")

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_replace_ignore_case(self, mock_print, mock_read):
        """Test replace command with case insensitive option."""
        mock_read.return_value = "Hello WORLD"

        class Args:
            file = "test.txt"
            old = "world"
            new = "universe"
            output = None
            ignore_case = True

        handle_replace_command(Args())
        mock_print.assert_called_with("Hello universe", end='')


class TestHandleCaseCommand:
    """Test case command handling."""

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.print')
    def test_handle_case_upper(self, mock_print, mock_read):
        """Test uppercase conversion command."""
        mock_read.return_value = "hello world"

        class Args:
            file = "test.txt"
            type = "upper"
            output = None

        handle_case_command(Args())
        mock_print.assert_called_with("HELLO WORLD", end='')

    @patch('text_processor.text_processor.read_input')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_handle_case_file_output(self, mock_print, mock_file, mock_read):
        """Test case command with file output."""
        mock_read.return_value = "hello world"

        class Args:
            file = "input.txt"
            type = "title"
            output = "output.txt"

        handle_case_command(Args())

        mock_file.assert_called_with("output.txt", 'w', encoding='utf-8')
        mock_file().write.assert_called_with("Hello World")
        mock_print.assert_called_with("Output written to: output.txt")


class TestCreateParser:
    """Test argument parser creation and configuration."""

    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        assert parser is not None
        assert "Text Processor" in parser.description

    def test_parser_count_command(self):
        """Test count command parsing."""
        parser = create_parser()
        args = parser.parse_args(['count', 'words', '-f', 'test.txt'])

        assert args.command == 'count'
        assert args.type == 'words'
        assert args.file == 'test.txt'
        assert args.no_spaces is False

    def test_parser_replace_command(self):
        """Test replace command parsing."""
        parser = create_parser()
        args = parser.parse_args(['replace', 'old', 'new', '-f', 'input.txt', '-o', 'output.txt', '-i'])

        assert args.command == 'replace'
        assert args.old == 'old'
        assert args.new == 'new'
        assert args.file == 'input.txt'
        assert args.output == 'output.txt'
        assert args.ignore_case is True

    def test_parser_case_command(self):
        """Test case command parsing."""
        parser = create_parser()
        args = parser.parse_args(['case', 'upper', '-f', 'input.txt'])

        assert args.command == 'case'
        assert args.type == 'upper'
        assert args.file == 'input.txt'
        assert args.output is None


class TestMainFunction:
    """Test main function behavior."""

    @patch('sys.argv', ['text_processor.py'])
    @patch('text_processor.text_processor.create_parser')
    def test_main_no_args(self, mock_parser):
        """Test main with no arguments shows help."""
        mock_parser_instance = mock_parser.return_value

        with pytest.raises(SystemExit, match="0"):
            main()

        mock_parser_instance.print_help.assert_called_once()

    @patch('sys.argv', ['text_processor.py', 'count', 'words'])
    @patch('text_processor.text_processor.handle_count_command')
    def test_main_count_command(self, mock_handle):
        """Test main with count command."""
        with patch('text_processor.text_processor.read_input', return_value="test"):
            main()

        mock_handle.assert_called_once()

    @patch('sys.argv', ['text_processor.py', 'replace', 'old', 'new'])
    @patch('text_processor.text_processor.handle_replace_command')
    def test_main_replace_command(self, mock_handle):
        """Test main with replace command."""
        with patch('text_processor.text_processor.read_input', return_value="test"):
            main()

        mock_handle.assert_called_once()

    @patch('sys.argv', ['text_processor.py', 'case', 'upper'])
    @patch('text_processor.text_processor.handle_case_command')
    def test_main_case_command(self, mock_handle):
        """Test main with case command."""
        with patch('text_processor.text_processor.read_input', return_value="test"):
            main()

        mock_handle.assert_called_once()

    @patch('sys.argv', ['text_processor.py', 'count', 'words'])
    @patch('text_processor.text_processor.handle_count_command')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_keyboard_interrupt(self, mock_stderr, mock_handle):
        """Test main with keyboard interrupt."""
        mock_handle.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit, match="130"):
            main()

        assert "Operation cancelled by user" in mock_stderr.getvalue()

    @patch('sys.argv', ['text_processor.py', 'count', 'words'])
    @patch('text_processor.text_processor.handle_count_command')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_unexpected_error(self, mock_stderr, mock_handle):
        """Test main with unexpected error."""
        mock_handle.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(SystemExit, match="1"):
            main()

        assert "Unexpected error: Unexpected error" in mock_stderr.getvalue()
