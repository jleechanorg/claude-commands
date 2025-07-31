import os
import re
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


import constants
import gemini_service
import logging_util
from gemini_service import _load_instruction_file, _loaded_instructions_cache

# The list of all known prompt types to test, using shared constants.
PROMPT_TYPES_TO_TEST = [
    constants.PROMPT_TYPE_NARRATIVE,
    constants.PROMPT_TYPE_MECHANICS,
    constants.PROMPT_TYPE_GAME_STATE,
]


class TestPromptLoading(unittest.TestCase):
    def setUp(self):
        """Clear the instruction cache before each test to ensure isolation."""
        _loaded_instructions_cache.clear()

    def test_all_prompts_are_loadable_via_service(self):
        """
        Ensures that all referenced prompt files can be loaded successfully
        by calling the actual _load_instruction_file function.
        """
        logging_util.info(
            "--- Running Test: test_all_prompts_are_loadable_via_service ---"
        )

        for p_type in gemini_service.PATH_MAP.keys():
            content = _load_instruction_file(p_type)
            assert isinstance(content, str)
            assert len(content) > 0, f"Prompt file for {p_type} should not be empty."

    def test_loading_unknown_prompt_raises_error(self):
        """
        Ensures that calling _load_instruction_file with an unknown type
        correctly raises a ValueError, following the strict loading policy.
        """
        logging_util.info(
            "--- Running Test: test_loading_unknown_prompt_raises_error ---"
        )
        with self.assertRaises(ValueError):
            _load_instruction_file("this_is_not_a_real_prompt_type")

    def test_all_prompt_files_are_registered_in_service(self):
        """
        Ensures that every .md file in the prompts directory is registered
        in the gemini_service.path_map, and vice-versa. This prevents
        un-loaded or orphaned prompt files.
        """
        logging_util.info(
            "--- Running Test: test_all_prompt_files_are_registered_in_service ---"
        )

        prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompts"
        )

        # 1. Get all .md files from the filesystem (excluding README files)
        try:
            disk_files = {
                f
                for f in os.listdir(prompts_dir)
                if f.endswith(".md") and f.lower() != "readme.md"
            }
        except FileNotFoundError:
            self.fail(f"Prompts directory not found at {prompts_dir}")

        # 2. Get all file basenames from the service's path_map
        service_files = {os.path.basename(p) for p in gemini_service.PATH_MAP.values()}

        # 3. Compare the sets
        unregistered_files = disk_files - service_files
        assert len(unregistered_files) == 0, f"Found .md files in prompts/ dir not registered in gemini_service.path_map: {unregistered_files}"

        missing_files = service_files - disk_files
        assert len(missing_files) == 0, f"Found files in gemini_service.path_map that do not exist in prompts/: {missing_files}"

    def test_all_registered_prompts_are_actually_used(self):
        """
        Ensures that every prompt registered in PATH_MAP is actually used
        somewhere in the codebase. This prevents dead/unused prompts.
        """
        logging_util.info(
            "--- Running Test: test_all_registered_prompts_are_actually_used ---"
        )

        # Get all prompt types from PATH_MAP
        prompt_types = set(gemini_service.PATH_MAP.keys())

        # Create reverse mapping from constant values to constant names
        # by inspecting the constants module
        prompt_to_constant = {}
        for attr_name in dir(constants):
            if attr_name.startswith("PROMPT_TYPE_"):
                attr_value = getattr(constants, attr_name)
                if isinstance(attr_value, str):  # Only include string constants
                    prompt_to_constant[attr_value] = attr_name

        # Search for usage of each prompt type in the codebase
        codebase_dir = os.path.dirname(os.path.dirname(__file__))
        unused_prompts = set()

        for prompt_type in prompt_types:
            # Check if prompt type is used anywhere in Python files
            found_usage = False
            constant_name = prompt_to_constant.get(
                prompt_type, f"PROMPT_TYPE_{prompt_type.upper()}"
            )

            # Search through Python files for usage
            for root, dirs, files in os.walk(codebase_dir):
                # Skip test directories and __pycache__
                # More specific: only skip if the directory name itself starts with 'test' or is __pycache__
                basename = os.path.basename(root)
                if basename.startswith("test") or basename == "__pycache__":
                    continue

                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, encoding="utf-8") as f:
                                content = f.read()
                                # Look for the prompt type constant being used or the literal value
                                if (
                                    constant_name in content
                                    or f"'{prompt_type}'" in content
                                    or f'"{prompt_type}"' in content
                                ):
                                    found_usage = True
                                    break
                        except (UnicodeDecodeError, PermissionError):
                            continue

                if found_usage:
                    break

            if not found_usage:
                unused_prompts.add(prompt_type)

        # This test should pass now that we're looking for the right patterns
        assert len(unused_prompts) == 0, f"Found prompt types registered in PATH_MAP but not used in codebase: {unused_prompts}"

        # Also verify that prompt types are actually called via _load_instruction_file
        # This is a more specific check for actual loading via constants
        used_in_loading = set()

        # Check if gemini_service.py path calculation is correct
        gemini_service_path = os.path.join(codebase_dir, "gemini_service.py")
        if not os.path.exists(gemini_service_path):
            logging_util.warning(
                f"gemini_service.py not found at {gemini_service_path}"
            )

        # Search for _load_instruction_file calls with constants
        for root, dirs, files in os.walk(codebase_dir):
            # Skip test directories and __pycache__
            basename = os.path.basename(root)
            if basename.startswith("test") or basename == "__pycache__":
                continue

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            content = f.read()
                            # Look for _load_instruction_file calls with constants
                            if (
                                "_load_instruction_file(constants.PROMPT_TYPE_"
                                in content
                            ):
                                # Extract the constant names used in _load_instruction_file calls

                                matches = re.findall(
                                    r"_load_instruction_file\(constants\.(PROMPT_TYPE_\w+)\)",
                                    content,
                                )
                                for match in matches:
                                    # Get the actual constant value
                                    if hasattr(constants, match):
                                        constant_value = getattr(constants, match)
                                        if constant_value in prompt_types:
                                            used_in_loading.add(constant_value)

                            # Also check for dynamic loading in loops
                            # Look for patterns like: for p_type in [...]: _load_instruction_file(p_type)
                            if (
                                "for p_type in" in content
                                and "_load_instruction_file(p_type)" in content
                            ):
                                # This indicates dynamic loading - check the context
                                lines = content.split("\n")
                                for i, line in enumerate(lines):
                                    if "_load_instruction_file(p_type)" in line:
                                        # Look backwards for the loop definition
                                        for j in range(max(0, i - 10), i):
                                            if "for p_type in" in lines[j]:
                                                # Check if it mentions prompt types
                                                if "selected_prompts" in lines[j]:
                                                    # Mark narrative and mechanics as used (they're in selected_prompts)
                                                    used_in_loading.add("narrative")
                                                    used_in_loading.add("mechanics")
                                                elif "prompt_order" in lines[j]:
                                                    # Also check prompt_order list
                                                    used_in_loading.add("narrative")
                                                    used_in_loading.add("mechanics")
                                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue

        # Define prompts that are loaded conditionally
        conditional_prompts = {
            constants.PROMPT_TYPE_NARRATIVE,  # Only when narrative selected
            constants.PROMPT_TYPE_MECHANICS,  # Only when mechanics selected
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE,  # Only when narrative is selected
        }

        # Separate always-loaded vs conditional prompts
        always_loaded_prompts = prompt_types - conditional_prompts
        not_loaded_always = always_loaded_prompts - used_in_loading

        # All always-loaded prompts should be found
        assert len(not_loaded_always) == 0, f"Found always-loaded prompt types that are never loaded: {not_loaded_always}"

        # Conditional prompts should be loaded when conditions are met
        conditional_not_loaded = conditional_prompts - used_in_loading

        # Verify conditional prompts are at least referenced in conditional logic
        conditional_referenced = set()
        for root, dirs, files in os.walk(codebase_dir):
            # Skip test directories and __pycache__
            basename = os.path.basename(root)
            if basename.startswith("test") or basename == "__pycache__":
                continue

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            content = f.read()
                            # Look for conditional loading patterns
                            for prompt_type in conditional_prompts:
                                constant_name = prompt_to_constant.get(
                                    prompt_type, f"PROMPT_TYPE_{prompt_type.upper()}"
                                )
                                # Check various conditional patterns
                                if (
                                    (
                                        "in selected_prompts" in content
                                        and constant_name in content
                                    )
                                    or (
                                        f"constants.{constant_name} in selected_prompts"
                                        in content
                                    )
                                    or (
                                        f"{constant_name} in selected_prompts"
                                        in content
                                    )
                                ):
                                    conditional_referenced.add(prompt_type)
                                # Also check character_template special case
                                if (
                                    prompt_type == "character_template"
                                    and "PROMPT_TYPE_NARRATIVE in selected_prompts"
                                    in content
                                    and "_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE)"
                                    in content
                                ):
                                    conditional_referenced.add(prompt_type)
                    except (UnicodeDecodeError, PermissionError):
                        continue

        unreferenced_conditionals = conditional_prompts - conditional_referenced
        assert len(unreferenced_conditionals) == 0, f"Found conditional prompt types that are not referenced in conditional logic: {unreferenced_conditionals}"

        print(
            f"✓ Always-loaded prompts: {len(always_loaded_prompts - not_loaded_always)}/{len(always_loaded_prompts)} verified"
        )
        print(
            f"✓ Conditional prompts: {len(conditional_referenced)}/{len(conditional_prompts)} properly referenced"
        )


if __name__ == "__main__":
    unittest.main()
