import unittest
import argparse
import pydantic as pdt
import typing as tp
from io import StringIO
from unittest.mock import patch
from confstack import ConfStack
from confstack.example01 import ConfStackExample01


class TestPositionalArgsExtension(unittest.TestCase):
    """Test adding positional arguments to the ArgumentParser."""

    def test_single_positional_arg(self):
        """Test that a single positional arg can be added and parsed."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="Input file to process")

        args = parser.parse_args(["--key_00", "cli_value", "myfile.txt"])

        self.assertEqual(args.key_00, "cli_value")
        self.assertEqual(args.input_file, "myfile.txt")

    def test_required_positional_without_value_fails(self):
        """Test that missing required positional arg raises SystemExit."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="Input file to process")

        with self.assertRaises(SystemExit):
            parser.parse_args(["--key_00", "cli_value"])

    def test_multiple_positional_args(self):
        """Test multiple positional args work with config options."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="Input file")
        parser.add_argument("output_file", help="Output file")

        args = parser.parse_args(["input.txt", "output.txt", "--key_01", "val"])

        self.assertEqual(args.input_file, "input.txt")
        self.assertEqual(args.output_file, "output.txt")
        self.assertEqual(args.key_01, "val")

    def test_positional_arg_order_variations(self):
        """Test positional args work in different positions."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="Input file")

        # Positional at end
        args1 = parser.parse_args(["--key_00", "x", "--key_01", "y", "file1.txt"])
        self.assertEqual(args1.key_00, "x")
        self.assertEqual(args1.key_01, "y")
        self.assertEqual(args1.input_file, "file1.txt")

        # Positional at beginning (after optional)
        args2 = parser.parse_args(["file2.txt", "--key_00", "z"])
        self.assertEqual(args2.key_00, "z")
        self.assertEqual(args2.input_file, "file2.txt")


class TestCustomOptionalArgs(unittest.TestCase):
    """Test adding custom optional arguments to the ArgumentParser."""

    def test_add_boolean_flag(self):
        """Test adding a boolean flag works with config options."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose mode"
        )

        # Without flag
        args1 = parser.parse_args(["--key_00", "x"])
        self.assertFalse(args1.verbose)
        self.assertEqual(args1.key_00, "x")

        # With flag
        args2 = parser.parse_args(["--key_00", "y", "--verbose"])
        self.assertTrue(args2.verbose)
        self.assertEqual(args2.key_00, "y")

    def test_custom_arg_with_value(self):
        """Test custom arg with value works alongside config options."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("--output", "-o", help="Output file path")

        args = parser.parse_args(["--key_00", "x", "--output", "result.json"])

        self.assertEqual(args.key_00, "x")
        self.assertEqual(args.output, "result.json")

    def test_mixed_order_parsing(self):
        """Test that argument order doesn't affect parsing."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("--verbose", action="store_true")

        # Different orders should produce same results
        orders = [
            ["--verbose", "--key_00", "x"],
            ["--key_00", "x", "--verbose"],
            ["--key_00", "x", "--verbose", "--key_01", "y"],
        ]

        for order in orders:
            args = parser.parse_args(order)
            if "--verbose" in order:
                self.assertTrue(args.verbose, f"Failed for order: {order}")
            else:
                self.assertFalse(args.verbose, f"Failed for order: {order}")
            if "--key_00" in order:
                self.assertEqual(args.key_00, "x", f"Failed for order: {order}")

    def test_custom_arg_with_choices(self):
        """Test custom arg with choices validation."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument(
            "--format", choices=["json", "yaml", "xml"], help="Output format"
        )

        # Valid choice
        args = parser.parse_args(["--format", "json"])
        self.assertEqual(args.format, "json")

        # Invalid choice should raise SystemExit
        with self.assertRaises(SystemExit):
            parser.parse_args(["--format", "csv"])

    def test_custom_arg_with_default(self):
        """Test custom arg with default value."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("--threads", type=int, default=4, help="Number of threads")

        # Without providing the arg
        args1 = parser.parse_args(["--key_00", "x"])
        self.assertEqual(args1.threads, 4)

        # With explicit value
        args2 = parser.parse_args(["--key_00", "x", "--threads", "8"])
        self.assertEqual(args2.threads, 8)


class TestSubparsersExtension(unittest.TestCase):
    """Test adding subparsers/subcommands to the ArgumentParser."""

    def test_single_subcommand(self):
        """Test a single subcommand works."""
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        run_parser = subparsers.add_parser("run", help="Run the process")
        run_parser.add_argument(
            "--threads", type=int, default=1, help="Number of threads"
        )

        args = parser.parse_args(["run", "--threads", "4"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.threads, 4)

    def test_subcommand_with_config_args(self):
        """Test subcommand works with top-level config args."""
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run")
        run_parser.add_argument("--threads", type=int, default=1)

        args = parser.parse_args(["--key_00", "config_val", "run", "--threads", "4"])

        self.assertEqual(args.key_00, "config_val")
        self.assertEqual(args.command, "run")
        self.assertEqual(args.threads, 4)

    def test_multiple_subcommands(self):
        """Test multiple subcommands each with different args."""
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run")
        run_parser.add_argument("--threads", type=int, default=1)

        init_parser = subparsers.add_parser("init")
        init_parser.add_argument("--force", action="store_true")

        status_parser = subparsers.add_parser("status")
        status_parser.add_argument("--watch", action="store_true")

        # Test run
        args_run = parser.parse_args(["run", "--threads", "8"])
        self.assertEqual(args_run.command, "run")
        self.assertEqual(args_run.threads, 8)

        # Test init
        args_init = parser.parse_args(["init", "--force"])
        self.assertEqual(args_init.command, "init")
        self.assertTrue(args_init.force)

        # Test status
        args_status = parser.parse_args(["status", "--watch"])
        self.assertEqual(args_status.command, "status")
        self.assertTrue(args_status.watch)

    def test_subcommand_required_arg(self):
        """Test subcommand with required argument."""
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command")

        process_parser = subparsers.add_parser("process")
        process_parser.add_argument("input", help="Input file (required)")

        # Without required arg should fail
        with self.assertRaises(SystemExit):
            parser.parse_args(["process"])

        # With required arg should work
        args = parser.parse_args(["process", "data.txt"])
        self.assertEqual(args.input, "data.txt")


class TestIntegrationWithLoadConfig(unittest.TestCase):
    """Test integration of custom args with load_config()."""

    @staticmethod
    def _extract_config_args(args_namespace, model_class):
        """Extract only config-related args from parsed namespace.

        Args:
            args_namespace: argparse.Namespace with all parsed args
            model_class: ConfStack subclass to get valid config paths

        Returns:
            dict with only valid config paths
        """
        config_paths = set(model_class._collect_config_paths(model_class))
        args_dict = vars(args_namespace)

        # Filter to only include args that are valid config paths (with __ separator)
        config_args = {}
        for key, value in args_dict.items():
            if value is not None:
                # Convert __ back to . for config path matching
                dotted_path = key.replace("__", ".")
                if dotted_path in config_paths:
                    config_args[dotted_path] = value

        return config_args

    def test_filter_custom_args_before_load_config(self):
        """Test that custom args are filtered before load_config."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("--output", default="output.txt")

        args = parser.parse_args(
            ["--key_00", "cli_value", "--verbose", "--output", "custom.json"]
        )

        # Filter to only config args
        config_args = self._extract_config_args(args, ConfStackExample01)

        # Should only contain config-related args
        self.assertIn("key_00", config_args)
        self.assertEqual(config_args["key_00"], "cli_value")
        self.assertNotIn("verbose", config_args)
        self.assertNotIn("output", config_args)

        # Load config with filtered args
        config = ConfStackExample01.load_config(config_args)
        self.assertEqual(config.key_00, "cli_value")

    def test_positional_args_filtered_out(self):
        """Test that positional args are not passed to load_config."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file")

        args = parser.parse_args(["--key_00", "x", "data.txt"])
        config_args = self._extract_config_args(args, ConfStackExample01)

        # Positional should be filtered out
        self.assertNotIn("input_file", config_args)
        self.assertEqual(config_args.get("key_00"), "x")

    def test_full_workflow_with_custom_args(self):
        """Test complete workflow: parse, filter, load config."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="Input file")
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )
        parser.add_argument("--output", "-o", default="out.txt", help="Output file")

        # Parse mixed args
        args = parser.parse_args(
            [
                "--key_00",
                "config_x",
                "--verbose",
                "--key_02__subkey_01",
                "nested_val",
                "data.txt",
            ]
        )

        # Extract config args
        config_args = self._extract_config_args(args, ConfStackExample01)

        # Load config
        config = ConfStackExample01.load_config(config_args)

        # Verify config loaded correctly
        self.assertEqual(config.key_00, "config_x")
        self.assertEqual(config.key_02.subkey_01, "nested_val")

        # Verify custom args accessible separately
        self.assertEqual(args.input_file, "data.txt")
        self.assertTrue(args.verbose)
        self.assertEqual(args.output, "out.txt")


class TestArgumentConflicts(unittest.TestCase):
    """Test edge cases around argument naming conflicts."""

    def test_custom_arg_with_same_name_as_config_field_raises_error(self):
        """Test that adding arg with same name as config option raises error.

        This documents that argparse raises ArgumentError for duplicate options
        unless conflict_handler='resolve' is set.
        """
        parser = ConfStackExample01.get_argparser()

        # Adding another --key_00 should raise ArgumentError
        with self.assertRaises(argparse.ArgumentError):
            parser.add_argument("--key_00", help="Overridden key_00")

    def test_conflict_handler_resolve_allows_override(self):
        """Test that conflict_handler='resolve' allows overriding config args."""
        # Create parser with conflict resolution
        parser = argparse.ArgumentParser(conflict_handler="resolve")
        parser.description = f"{ConfStackExample01.app_name} Configuration"

        # Add original config arg
        parser.add_argument(
            "--key_00", dest="key_00", type=str, default=None, help="Original key_00"
        )

        # Override with new behavior (e.g., adding choices)
        parser.add_argument(
            "--key_00",
            dest="key_00",
            choices=["a", "b", "c"],
            help="Overridden key_00 with choices",
        )

        # Should use the override version
        args = parser.parse_args(["--key_00", "a"])
        self.assertEqual(args.key_00, "a")

        # Invalid choice should fail
        with self.assertRaises(SystemExit):
            parser.parse_args(["--key_00", "invalid"])


class TestHelpIntegration(unittest.TestCase):
    """Test help output includes all arguments."""

    def test_help_includes_config_and_custom_args(self):
        """Test help shows both config options and custom args."""
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("--verbose", help="Enable verbose mode")
        parser.add_argument("input_file", help="Input file to process")

        help_text = parser.format_help()

        # Config options should be present
        self.assertIn("--key_00", help_text)
        self.assertIn("--key_01", help_text)
        self.assertIn("--key_02__subkey_01", help_text)

        # Custom args should be present
        self.assertIn("--verbose", help_text)
        self.assertIn("input_file", help_text)

    def test_help_with_subparsers(self):
        """Test help shows subcommands and their args."""
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run", help="Run command")
        run_parser.add_argument("--threads", type=int, help="Number of threads")

        # Main help should show subcommands
        main_help = parser.format_help()
        self.assertIn("run", main_help)

        # Subcommand help should show specific args
        sub_help = run_parser.format_help()
        self.assertIn("--threads", sub_help)

    def test_custom_description_preserved(self):
        """Test that custom description is preserved in help."""
        parser = ConfStackExample01.get_argparser()

        # Default description check
        self.assertIsNotNone(parser.description)
        if parser.description:
            self.assertIn("app_name Configuration", parser.description)

        # Create custom parser with new description
        custom_parser = argparse.ArgumentParser(description="Custom Tool Description")
        # Manually add config args
        paths = ConfStackExample01._collect_config_paths(ConfStackExample01)
        for path in paths:
            option_name = path.replace(".", "__")
            custom_parser.add_argument(f"--{option_name}")

        self.assertIsNotNone(custom_parser.description)
        if custom_parser.description:
            self.assertIn("Custom Tool Description", custom_parser.description)


class TestRealWorldScenarios(unittest.TestCase):
    """Integration tests mimicking real-world CLI tool scenarios."""

    def test_cli_tool_with_file_processing(self):
        """Test a file processing CLI tool scenario.

        Scenario: A tool that processes files with config options for behavior.
        - Config options: processing settings
        - Positional: input file
        - Custom: --verbose, --output
        """
        # Setup parser
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("input_file", help="File to process")
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )
        parser.add_argument(
            "--output", "-o", default="output.txt", help="Output file path"
        )

        # Simulate: mytool --key_00 "fast" --verbose input.txt --output result.json
        args = parser.parse_args(
            [
                "--key_00",
                "fast_mode",
                "--verbose",
                "--key_02__subkey_01",
                "setting_a",
                "input.txt",
                "--output",
                "result.json",
            ]
        )

        # Verify all args parsed
        self.assertEqual(args.key_00, "fast_mode")
        self.assertEqual(args.key_02__subkey_01, "setting_a")
        self.assertTrue(args.verbose)
        self.assertEqual(args.input_file, "input.txt")
        self.assertEqual(args.output, "result.json")

        # Verify config loading would work
        config_args = TestIntegrationWithLoadConfig._extract_config_args(
            args, ConfStackExample01
        )
        self.assertEqual(config_args["key_00"], "fast_mode")
        self.assertEqual(config_args["key_02.subkey_01"], "setting_a")

    def test_cli_tool_with_subcommands(self):
        """Test a CLI tool with subcommands scenario.

        Scenario: A tool with multiple operations and global config.
        - Global config options
        - Subcommands: process, validate
        - Each subcommand has specific args
        """
        parser = ConfStackExample01.get_argparser()
        subparsers = parser.add_subparsers(dest="command", required=True)

        # Process subcommand
        process_parser = subparsers.add_parser("process", help="Process data")
        process_parser.add_argument(
            "--threads", type=int, default=1, help="Number of threads"
        )
        process_parser.add_argument("input", help="Input file")

        # Validate subcommand
        validate_parser = subparsers.add_parser("validate", help="Validate data")
        validate_parser.add_argument(
            "--strict", action="store_true", help="Enable strict validation"
        )
        validate_parser.add_argument("schema", help="Schema file")

        # Test: mytool --key_00 "prod" process --threads 8 data.csv
        args_process = parser.parse_args(
            ["--key_00", "prod_config", "process", "--threads", "8", "data.csv"]
        )
        self.assertEqual(args_process.key_00, "prod_config")
        self.assertEqual(args_process.command, "process")
        self.assertEqual(args_process.threads, 8)
        self.assertEqual(args_process.input, "data.csv")

        # Test: mytool validate --strict schema.json
        args_validate = parser.parse_args(["validate", "--strict", "schema.json"])
        self.assertEqual(args_validate.command, "validate")
        self.assertTrue(args_validate.strict)
        self.assertEqual(args_validate.schema, "schema.json")

    def test_config_and_cli_workflow(self):
        """Test complete workflow: parse, filter, load config, use custom args.

        This simulates a real application that:
        1. Defines config model with defaults
        2. Extends parser with custom args
        3. Parses all args
        4. Loads config with only config-related args
        5. Uses custom args in application logic
        """
        # Step 1 & 2: Setup parser with custom args
        parser = ConfStackExample01.get_argparser()
        parser.add_argument("files", nargs="+", help="Files to process")
        parser.add_argument(
            "--dry-run", action="store_true", help="Simulate without executing"
        )
        parser.add_argument(
            "--format", choices=["json", "yaml"], default="json", help="Output format"
        )

        # Step 3: Parse all args
        cli_args = [
            "--key_00",
            "override_value",
            "--key_01",
            "another_override",
            "--dry-run",
            "--format",
            "yaml",
            "file1.txt",
            "file2.txt",
            "file3.txt",
        ]
        parsed_args = parser.parse_args(cli_args)

        # Step 4: Filter and load config
        config_args = TestIntegrationWithLoadConfig._extract_config_args(
            parsed_args, ConfStackExample01
        )
        config = ConfStackExample01.load_config(config_args)

        # Step 5: Use in application logic
        # Config values loaded correctly
        self.assertEqual(config.key_00, "override_value")
        self.assertEqual(config.key_01, "another_override")

        # Default values preserved for non-overridden fields
        self.assertEqual(config.key_02.subkey_01, "layer_01_value_02_01")

        # Custom args accessible for application logic
        self.assertEqual(parsed_args.files, ["file1.txt", "file2.txt", "file3.txt"])
        self.assertTrue(parsed_args.dry_run)
        self.assertEqual(parsed_args.format, "yaml")

        # Application could now do:
        # if parsed_args.dry_run:
        #     print("Would process files:", parsed_args.files)
        # else:
        #     process_files(parsed_args.files, output_format=parsed_args.format)


if __name__ == "__main__":
    unittest.main()
