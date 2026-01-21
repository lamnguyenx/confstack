# Test Refactoring Plan: 2026-01-21-01

## Overview
Refactor the existing test file `src/confstack/__tests__/test_confstack.py` by extracting the shared `MockConfig` class into a separate file `src/confstack/__tests__/test_shared_data.py` and dividing the test methods into multiple logical test files for better organization and maintainability.

## Assumptions and Analysis
- The current file (`test_confstack.py`) contains a single test class `TestConfStack` with a nested `MockConfig` class (used as shared test data/configuration) and various test methods.
- "TestConfStack" likely refers to the `MockConfig` class inside the test class, as it's the reusable component. The tests themselves will be divided.
- No other test files exist in `__tests__/`, so we're starting from one.
- Tests will be grouped by functionality (e.g., utility methods vs. loading behaviors) for clarity.
- All new files will import `MockConfig` from `test_shared_data.py`.
- Dependencies (e.g., `pytest`, `pydantic`, `confstack.ConfStack`) remain unchanged.

## Proposed Structure
- **test_shared_data.py**: Contains only the `MockConfig` class (extracted from `TestConfStack`).
- **test_config_methods.py**: Tests for static/utility methods (e.g., `set_nested_dict`, mappings, flattening).
- **test_config_loading.py**: Tests for loading behaviors (defaults, files, env vars, CLI args, precedence).

This results in 3 total test files (plus the original will be removed), keeping things manageable without over-fragmenting.

## Step-by-Step Plan
1. **Create `test_shared_data.py`**:
   - Extract `MockConfig` (lines 15-39 in the original file) to a new file.
   - Add necessary imports (e.g., `pydantic as pdt`, `typing as tp`, `from confstack import ConfStack`).
   - Make `MockConfig` a standalone class in this file.

2. **Create `test_config_methods.py`**:
   - Move tests: `test_set_nested_dict`, `test_collect_config_paths`, `test_get_mappings`, `test_flatten_config`, `test_generate_config_mapping_pandas`.
   - Import `MockConfig` from `test_shared_data`.
   - Add class structure: Create a new `TestConfStackMethods` class (or similar) to hold these tests.

3. **Create `test_config_loading.py`**:
   - Move tests: `test_load_defaults`, `test_load_config_file`, `test_load_lower_env`, `test_load_upper_env`, `test_load_cli_args`, `test_layer_precedence`.
   - Import `MockConfig` from `test_shared_data`.
   - Add class structure: Create a new `TestConfStackLoading` class (or similar) to hold these tests.

4. **Update Imports and Dependencies**:
   - In both new test files, add `from test_shared_data import MockConfig`.
   - Ensure all original imports (e.g., `pytest`, `os`, `json`, etc.) are copied to the relevant new files.
   - Update method calls to use `self.MockConfig` → `MockConfig` (since it's no longer nested).

5. **Clean Up Original File**:
   - Delete `test_confstack.py` after confirming the new files work.

6. **Verification**:
   - Run the test suite (likely `pytest` or similar) to ensure no failures.
   - Check for any missing imports or path issues.

## Potential Tradeoffs and Questions
- **Grouping**: I grouped tests by "methods" (utilities) vs. "loading" (behaviors) for simplicity. If you'd prefer different splits (e.g., by layer type: env, file, CLI), let me know—how would you like the tests divided?
- **Class Naming**: I suggested new class names like `TestConfStackMethods` and `TestConfStackLoading` to avoid conflicts. Any preferences?
- **MockConfig Placement**: Assuming `test_shared_data.py` is the right name/location. If it's meant to be something else (e.g., a fixtures file), clarify.

This plan keeps the code modular.