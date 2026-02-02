import unittest
import subprocess
import sys
import json


class TestArgsViaSubshell_Example00(unittest.TestCase):
    """Test CLI args for ConfStackExample00 via subprocess."""

    def test_help_output(self):
        """Test that --help shows the correct CLI options with __ separator."""
        result = subprocess.run(
            [sys.executable, "-m", "confstack.example00", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        help_text = result.stdout

        # Check app name in description
        self.assertIn("app_name Configuration", help_text)

        # Check flat fields use single underscores (no __)
        self.assertIn("--key_00", help_text)
        self.assertIn("--key_01", help_text)

        # Check nested fields use __ separator
        self.assertIn("--key_02__subkey_01", help_text)
        self.assertIn("--key_02__subkey_02", help_text)

    def test_cli_args_override_defaults(self):
        """Test that CLI args override default values."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example00",
                "--key_00",
                "cli_custom_value",
                "--key_02__subkey_01",
                "cli_nested_value",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        # Check that CLI values are used
        self.assertEqual(output["key_00"], "cli_custom_value")
        self.assertEqual(output["key_02"]["subkey_01"], "cli_nested_value")

        # Check that non-overridden values still use defaults
        self.assertEqual(output["key_01"], "layer_01_value_01")
        self.assertEqual(output["key_02"]["subkey_02"], "layer_01_value_02_02")

    def test_cli_args_with_special_chars(self):
        """Test CLI args with spaces and special characters."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example00",
                "--key_00",
                "value with spaces",
                "--key_01",
                "http://example.com?foo=bar",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        self.assertEqual(output["key_00"], "value with spaces")
        self.assertEqual(output["key_01"], "http://example.com?foo=bar")

    def test_no_args_uses_defaults(self):
        """Test that running without args uses all default values."""
        result = subprocess.run(
            [sys.executable, "-m", "confstack.example00"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        # Check all default values are present
        self.assertEqual(output["key_00"], "layer_01_value_00")
        self.assertEqual(output["key_01"], "layer_01_value_01")
        self.assertEqual(output["key_02"]["subkey_01"], "layer_01_value_02_01")
        self.assertEqual(output["key_02"]["subkey_02"], "layer_01_value_02_02")

    def test_multiple_overrides(self):
        """Test overriding multiple nested values."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example00",
                "--key_02__subkey_01",
                "new_01",
                "--key_02__subkey_02",
                "new_02",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        self.assertEqual(output["key_02"]["subkey_01"], "new_01")
        self.assertEqual(output["key_02"]["subkey_02"], "new_02")


class TestArgsViaSubshell_Example01(unittest.TestCase):
    """Test CLI args for ConfStackExample01 via subprocess."""

    def test_help_output(self):
        """Test that --help shows the correct CLI options with __ separator."""
        result = subprocess.run(
            [sys.executable, "-m", "confstack.example01", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        help_text = result.stdout

        # Check app name in description
        self.assertIn("app_name Configuration", help_text)

        # Check flat fields use single underscores (no __)
        self.assertIn("--key_00", help_text)
        self.assertIn("--key_01", help_text)

        # Check nested fields use __ separator
        self.assertIn("--key_02__subkey_01", help_text)
        self.assertIn("--key_02__subkey_02", help_text)
        self.assertIn("--key_02__subkey_03", help_text)

        # Check deeply nested fields
        self.assertIn("--key_03__subkey_00__subsubkey_00", help_text)
        self.assertIn("--key_03__subkey_01__subsubkey_00", help_text)
        self.assertIn("--key_03__subkey_01__subsubkey_01", help_text)

    def test_cli_args_override_defaults(self):
        """Test that CLI args override default values."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example01",
                "--key_00",
                "cli_custom_value",
                "--key_02__subkey_01",
                "cli_nested_value",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        # Check that CLI values are used
        self.assertEqual(output["key_00"], "cli_custom_value")
        self.assertEqual(output["key_02"]["subkey_01"], "cli_nested_value")

        # Check that non-overridden values still use defaults
        self.assertEqual(output["key_01"], "layer_01_value_01")
        self.assertEqual(output["key_02"]["subkey_02"], "layer_01_value_02_02")

    def test_cli_args_with_special_chars(self):
        """Test CLI args with spaces and special characters."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example01",
                "--key_00",
                "value with spaces",
                "--key_01",
                "http://example.com?foo=bar",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        self.assertEqual(output["key_00"], "value with spaces")
        self.assertEqual(output["key_01"], "http://example.com?foo=bar")

    def test_no_args_uses_defaults(self):
        """Test that running without args uses all default values."""
        result = subprocess.run(
            [sys.executable, "-m", "confstack.example01"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        # Check all default values are present
        self.assertEqual(output["key_00"], "layer_01_value_00")
        self.assertEqual(output["key_01"], "layer_01_value_01")
        self.assertEqual(output["key_02"]["subkey_01"], "layer_01_value_02_01")
        self.assertEqual(output["key_02"]["subkey_02"], "layer_01_value_02_02")
        self.assertEqual(output["key_02"]["subkey_03"], "layer_01_value_02_03")
        self.assertEqual(
            output["key_03"]["subkey_00"]["subsubkey_00"],
            "layer_01_value_03_00_00",
        )

    def test_multiple_overrides(self):
        """Test overriding multiple nested values."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example01",
                "--key_02__subkey_01",
                "new_01",
                "--key_02__subkey_02",
                "new_02",
                "--key_02__subkey_03",
                "new_03",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        self.assertEqual(output["key_02"]["subkey_01"], "new_01")
        self.assertEqual(output["key_02"]["subkey_02"], "new_02")
        self.assertEqual(output["key_02"]["subkey_03"], "new_03")

    def test_deep_nesting_override(self):
        """Test overriding deeply nested values."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "confstack.example01",
                "--key_03__subkey_01__subsubkey_00",
                "deep_override_00",
                "--key_03__subkey_01__subsubkey_01",
                "deep_override_01",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)

        self.assertEqual(
            output["key_03"]["subkey_01"]["subsubkey_00"], "deep_override_00"
        )
        self.assertEqual(
            output["key_03"]["subkey_01"]["subsubkey_01"], "deep_override_01"
        )
        # Non-overridden deep value should remain default
        self.assertEqual(
            output["key_03"]["subkey_00"]["subsubkey_00"],
            "layer_01_value_03_00_00",
        )


if __name__ == "__main__":
    unittest.main()
