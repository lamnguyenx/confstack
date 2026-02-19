# Implementation Plan: Extending ArgumentParser Tests

**Date:** 2026-02-05  
**File to Create:** `src/confstack/__tests__/test__args_extension.py`  
**Status:** Ready for Implementation  

## Overview

The `get_argparser()` method returns an `argparse.ArgumentParser` pre-populated with config options.
Users may want to extend this parser by adding:
- Positional arguments (e.g., input files)
- Custom optional arguments (e.g., --verbose, --output)
- Subparsers/subcommands
- Additional validation or actions

This test file ensures these extension scenarios work correctly and that config loading
integrates properly with custom arguments.

## Prerequisites

None - this is a pure test addition. The `get_argparser()` method already exists and returns
an ArgumentParser that can be extended.

## Test Implementation Details

### Import Requirements

```python
import unittest
import argparse
import pydantic as pdt
from confstack import ConfStack
from confstack.example01 import ConfStackExample01
```

---

### Class 1: `TestPositionalArgsExtension`

**Purpose:** Verify positional arguments can be added to the parser.

**Test 1.1:** `test_single_positional_arg`
- Get parser from `ConfStackExample01.get_argparser()`
- Add positional arg: `parser.add_argument("input_file")`
- Parse: `["--key_00", "cli_value", "myfile.txt"]`
- Assert: `key_00` is "cli_value", `input_file` is "myfile.txt"

**Test 1.2:** `test_required_positional_without_value_fails`
- Add required positional arg
- Parse with missing positional (only config args)
- Assert: SystemExit raised

**Test 1.3:** `test_multiple_positional_args`
- Add two positional args: `input_file`, `output_file`
- Parse: `["input.txt", "output.txt", "--key_01", "val"]`
- Assert both positional args captured correctly
- Assert config arg `key_01` is "val"

**Test 1.4:** `test_positional_arg_order_variations`
- Test positional args at beginning, middle, and end of arg list
- Verify argparse handles all cases correctly

---

### Class 2: `TestCustomOptionalArgs`

**Purpose:** Verify custom optional arguments work alongside config options.

**Test 2.1:** `test_add_boolean_flag`
- Add `--verbose` store_true flag
- Parse without flag: verify False
- Parse with flag: verify True
- Ensure config defaults still work

**Test 2.2:** `test_custom_arg_with_value`
- Add `--output` with required string value
- Parse: `["--key_00", "x", "--output", "result.json"]`
- Assert: `key_00` is "x", `output` is "result.json"

**Test 2.3:** `test_mixed_order_parsing`
- Parse args in different order:
  - `["--verbose", "--key_00", "x"]`
  - `["--key_00", "x", "--verbose"]`
  - `["--key_00", "x", "--verbose", "--key_01", "y"]`
- Verify order doesn't matter for final values

**Test 2.4:** `test_custom_arg_with_choices`
- Add `--format` with choices=["json", "yaml", "xml"]
- Test valid choice
- Test invalid choice raises error

**Test 2.5:** `test_custom_arg_with_default`
- Add optional arg with default value
- Parse without providing it
- Assert default is used

---

### Class 3: `TestSubparsersExtension`

**Purpose:** Verify subparsers/subcommands work with config arguments.

**Test 3.1:** `test_single_subcommand`
- Create subparser: `run`
- Add subcommand-specific arg: `--threads` (int)
- Parse: `["run", "--threads", "4"]`
- Assert subcommand parsed, threads=4

**Test 3.2:** `test_subcommand_with_config_args`
- Parse: `["--key_00", "config_val", "run", "--threads", "4"]`
- Assert both top-level config and subcommand args parsed

**Test 3.3:** `test_multiple_subcommands`
- Create subparsers: `run`, `init`, `status`
- Each with different args
- Test each subcommand works

**Test 3.4:** `test_subcommand_required_arg`
- Create subcommand with required arg
- Parse without required arg
- Assert SystemExit raised

---

### Class 4: `TestIntegrationWithLoadConfig`

**Purpose:** Verify custom args don't interfere with `load_config()`.

**Helper Method:** `_extract_config_args(args_namespace)`
- Input: argparse.Namespace with all parsed args
- Logic: Filter args to only include valid config paths
- Output: dict suitable for `load_config()`

**Test 4.1:** `test_filter_custom_args_before_load_config`
- Parse mixed args: config options + custom options
- Use helper to extract only config paths
- Call `load_config(filtered_args)`
- Assert config loaded correctly, custom args ignored

**Test 4.2:** `test_positional_args_filtered_out`
- Parse with positional arg
- Verify positional not passed to load_config
- Assert no errors

**Test 4.3:** `test_full_workflow_with_custom_args`
- Get parser, add `--verbose` flag and `input_file` positional
- Parse: `["--key_00", "x", "--verbose", "data.txt"]`
- Filter config args: only `key_00` -> "x"
- Load config
- Assert config.key_00 is "x"
- Assert custom args accessible separately

---

### Class 5: `TestArgumentConflicts`

**Purpose:** Test edge cases around argument naming conflicts.

**Test 5.1:** `test_custom_arg_with_same_name_as_config_field`
- Try to add `--key_00` (already exists from config)
- Document expected behavior (argparse should raise error or override)

**Test 5.2:** `test_conflicting_destinations`
- Add custom arg with dest that matches config path internal representation
- Test behavior

---

### Class 6: `TestHelpIntegration`

**Purpose:** Verify help output includes all arguments.

**Test 6.1:** `test_help_includes_config_and_custom_args`
- Add custom args to parser
- Capture help output
- Assert: config options present
- Assert: custom options present

**Test 6.2:** `test_help_with_subparsers`
- Create subparsers
- Verify main help shows subcommands
- Verify subcommand help shows specific args

**Test 6.3:** `test_custom_description_preserved`
- Override parser description
- Verify in help output

---

### Class 7: `TestRealWorldScenarios`

**Purpose:** Integration tests mimicking real use cases.

**Test 7.1:** `test_cli_tool_with_file_processing`
```python
# Scenario: A file processing CLI tool
# - Config options for processing behavior
# - Positional arg for input file
# --verbose flag for logging
parser = MyConfig.get_argparser()
parser.add_argument("input_file", help="File to process")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
parser.add_argument("--output", "-o", default="output.txt", help="Output file path")

# Parse and verify all args work together
```

**Test 7.2:** `test_cli_tool_with_subcommands`
```python
# Scenario: A CLI tool with multiple operations
# - Global config options
# - Subcommands: process, validate, export
# - Each subcommand has specific args
parser = MyConfig.get_argparser()
subparsers = parser.add_subparsers(dest="command")

process_parser = subparsers.add_parser("process")
process_parser.add_argument("--threads", type=int, default=1)

validate_parser = subparsers.add_parser("validate")
validate_parser.add_argument("--strict", action="store_true")

# Test each command works with config
```

**Test 7.3:** `test_config_and_cli_workflow`
```python
# Complete workflow:
# 1. Parse all args (config + custom)
# 2. Filter config args
# 3. Load config with defaults + file + env + cli
# 4. Use custom args in application logic
# 5. Verify nothing conflicts
```

---

## Implementation Notes

### File Structure
```python
src/confstack/__tests__/test__args_extension.py
├── Imports
├── TestPositionalArgsExtension (4 tests)
├── TestCustomOptionalArgs (5 tests)
├── TestSubparsersExtension (4 tests)
├── TestIntegrationWithLoadConfig (3 tests + 1 helper)
├── TestArgumentConflicts (2 tests)
├── TestHelpIntegration (3 tests)
└── TestRealWorldScenarios (3 tests)

Total: ~24 test methods
```

### Testing Best Practices
- Use `self.assertRaises(SystemExit)` for argparse error cases
- Use `argparse.Namespace` for inspecting parsed args
- Access `parser._actions` only when necessary (internal API)
- Test both success and failure cases
- Use descriptive test names

### Potential Challenges
1. **Argparse error handling:** Need to capture SystemExit
2. **Help output testing:** Use capture of stdout or parse format_help()
3. **Subparser complexity:** Ensure parent args are accessible

### Dependencies
- No new dependencies needed
- Uses existing: `unittest`, `argparse`, `confstack`

## Success Criteria

All tests should pass, demonstrating:
1. ✅ Positional args can be added and work correctly
2. ✅ Custom optional args don't conflict with config options
3. ✅ Subparsers work with config arguments
4. ✅ Custom args can be filtered before passing to `load_config()`
5. ✅ Help output is comprehensive
6. ✅ Real-world scenarios work end-to-end

## Next Steps

1. Create `src/confstack/__tests__/test__args_extension.py`
2. Implement tests class by class
3. Run tests to verify they pass
4. If any tests fail, investigate and document behavior
5. Consider updating documentation if edge cases discovered

## Related Files

- `src/confstack/confstack.py` - Contains `get_argparser()` implementation
- `src/confstack/__tests__/test__args.py` - Existing parser tests
- `src/confstack/example01.py` - Test model with nested config
