import unittest
import os
import json
import tempfile
import typing as tp
from unittest.mock import patch, MagicMock
from io import StringIO
from confstack import ConfStack
from confstack.example01 import ConfStackExample01
import pydantic as pdt


class MockConfigFileHelper:
    """Helper class to create mock config file loaders."""

    @staticmethod
    def create_mock_loader(config_file: str, model_cls: tp.Type[pdt.BaseModel]):
        """Create a mock loader function for config files."""

        def mock_load(config_data_inner: dict) -> None:
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
                sections = list(model_cls.model_fields.keys())
                for section_name in sections:
                    if section_name in file_config:
                        for key, value in file_config[section_name].items():
                            if value is not None:
                                ConfStack.set_nested_dict(
                                    config_data_inner,
                                    f"{section_name}.{key}",
                                    value,
                                )
            except Exception:
                pass  # ignore for test

        return mock_load


class TestConfigLoadingCli(unittest.TestCase):
    def test_load_cli_args(self):
        """Test loading from CLI args."""
        cli_args = {"key_00": "cli_value", "key_02.subkey_01": "cli_nested"}
        config = ConfStackExample01.load_config(cli_args)
        self.assertEqual(config.key_00, "cli_value")
        self.assertEqual(config.key_02.subkey_01, "cli_nested")

    def test_load_empty_cli_args(self):
        """Test loading with empty CLI args uses defaults."""
        cli_args = {}
        config = ConfStackExample01.load_config(cli_args)
        self.assertEqual(config.key_00, "layer_01_value_00")
        self.assertEqual(config.key_01, "layer_01_value_01")
        self.assertEqual(config.key_02.subkey_01, "layer_01_value_02_01")

    def test_load_multiple_cli_overrides(self):
        """Test loading with multiple CLI overrides."""
        cli_args = {
            "key_00": "new_value_00",
            "key_01": "new_value_01",
            "key_02.subkey_01": "new_nested_01",
            "key_02.subkey_02": "new_nested_02",
        }
        config = ConfStackExample01.load_config(cli_args)
        self.assertEqual(config.key_00, "new_value_00")
        self.assertEqual(config.key_01, "new_value_01")
        self.assertEqual(config.key_02.subkey_01, "new_nested_01")
        self.assertEqual(config.key_02.subkey_02, "new_nested_02")
        # Non-overridden should remain default
        self.assertEqual(config.key_02.subkey_03, "layer_01_value_02_03")

    def test_load_deep_nested_cli_args(self):
        """Test loading deeply nested CLI args."""
        cli_args = {
            "key_03.subkey_01.subsubkey_00": "deep_cli_value",
            "key_03.subkey_01.subsubkey_01": "another_deep_value",
        }
        config = ConfStackExample01.load_config(cli_args)
        self.assertEqual(config.key_03.subkey_01.subsubkey_00, "deep_cli_value")
        self.assertEqual(config.key_03.subkey_01.subsubkey_01, "another_deep_value")
        # Non-overridden deep values should remain default
        self.assertEqual(
            config.key_03.subkey_00.subsubkey_00, "layer_01_value_03_00_00"
        )


class TestConfigMethods(unittest.TestCase):
    def test_set_nested_dict(self):
        """Test set_nested_dict method."""
        data = {}
        ConfStack.set_nested_dict(data, "a.b.c", "value")
        self.assertEqual(data, {"a": {"b": {"c": "value"}}})

        # Test overwriting
        ConfStack.set_nested_dict(data, "a.b.c", "new_value")
        self.assertEqual(data["a"]["b"]["c"], "new_value")

        # Test top level
        ConfStack.set_nested_dict(data, "top", "top_value")
        self.assertEqual(data["top"], "top_value")

    def test_collect_config_paths(self):
        """Test _collect_config_paths method."""
        paths = ConfStackExample01._collect_config_paths(ConfStackExample01)
        expected = [
            "key_00",
            "key_01",
            "key_02.subkey_01",
            "key_02.subkey_02",
            "key_02.subkey_03",
            "key_03.subkey_00.subsubkey_00",
            "key_03.subkey_01.subsubkey_00",
            "key_03.subkey_01.subsubkey_01",
        ]
        self.assertEqual(set(paths), set(expected))

    def test_get_mappings(self):
        """Test _get_lower_mappings and _get_upper_mappings."""
        lower = ConfStackExample01._get_lower_mappings()
        upper = ConfStackExample01._get_upper_mappings()

        self.assertEqual(lower["app_name.key_00"], "key_00")
        self.assertEqual(lower["app_name.key_01"], "key_01")
        self.assertEqual(lower["app_name.key_02.subkey_01"], "key_02.subkey_01")

        self.assertEqual(upper["APP_NAME_KEY_00"], "key_00")
        self.assertEqual(upper["APP_NAME_KEY_01"], "key_01")
        self.assertEqual(upper["APP_NAME_KEY_02_SUBKEY_01"], "key_02.subkey_01")

    def test_flatten_config(self):
        """Test _flatten_config method."""
        config_dict = {"a": "value_a", "b": {"c": "value_c", "d": {"e": "value_e"}}}
        flattened = ConfStackExample01._flatten_config(config_dict)
        expected = [("a", "value_a"), ("b.c", "value_c"), ("b.d.e", "value_e")]
        self.assertEqual(flattened, expected)

    def test_generate_config_mapping_pandas(self):
        """Test generate_config_mapping_pandas method."""
        default_dict = ConfStackExample01.model_validate({}).model_dump()
        df = ConfStackExample01.generate_config_mapping_pandas(default_dict)
        self.assertEqual(len(df), 8)  # eight config paths
        self.assertIn("Config / CLI Args", df.columns)
        self.assertIn("Lowercase Dotted Envs.", df.columns)
        self.assertIn("Uppercase Underscored Envs.", df.columns)
        self.assertIn("Default Value", df.columns)


class TestConfigLoadingPrecedence(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "app_name.key_00": "env_value",
            "APP_NAME_KEY_02_SUBKEY_02": "upper_nested",
        },
    )
    def test_layer_precedence(self):
        """Test that later layers override earlier ones."""
        config_data = {"key_02": {"subkey_02": "file_nested"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = os.path.join(
                temp_dir, ".config", ConfStackExample01.app_name.lower()
            )
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, "w") as f:
                json.dump(config_data, f)
            with patch.object(
                ConfStackExample01, "load_layer_02_config_file"
            ) as mock_method:
                mock_method.side_effect = MockConfigFileHelper.create_mock_loader(
                    config_file, ConfStackExample01
                )
                cli_args = {"key_00": "cli_value"}
                config = ConfStackExample01.load_config(cli_args)
                # CLI should override env and file
                self.assertEqual(config.key_00, "cli_value")
                # Upper env should override file
                self.assertEqual(config.key_02.subkey_02, "upper_nested")
                # Lower env not set for subkey_02, so upper overrides file


class TestConfigLoadingEnv(unittest.TestCase):
    @patch.dict("os.environ", {"app_name.key_00": "env_lower_value"})
    def test_load_lower_env(self):
        """Test loading from lowercase dotted env vars."""
        config = ConfStackExample01.load_config({})
        self.assertEqual(config.key_00, "env_lower_value")

    @patch.dict("os.environ", {"APP_NAME_KEY_00": "env_upper_value"})
    def test_load_upper_env(self):
        """Test loading from uppercase underscored env vars."""
        config = ConfStackExample01.load_config({})
        self.assertEqual(config.key_00, "env_upper_value")


class TestConfigLoadingFile(unittest.TestCase):
    def test_load_config_file(self):
        """Test loading from config file."""
        config_data = {"key_02": {"subkey_01": "file_value"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = os.path.join(
                temp_dir, ".config", ConfStackExample01.app_name.lower()
            )
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, "w") as f:
                json.dump(config_data, f)
            with patch.object(
                ConfStackExample01, "load_layer_02_config_file"
            ) as mock_method:
                mock_method.side_effect = MockConfigFileHelper.create_mock_loader(
                    config_file, ConfStackExample01
                )
                config = ConfStackExample01.load_config({})
                self.assertEqual(config.key_02.subkey_01, "file_value")
                self.assertEqual(config.key_00, "layer_01_value_00")  # unchanged
                self.assertEqual(config.key_01, "layer_01_value_01")  # unchanged


class TestConfigLoadingDefaults(unittest.TestCase):
    def test_load_defaults(self):
        """Test loading config with defaults only."""
        config = ConfStackExample01.load_config({})
        self.assertEqual(config.key_00, "layer_01_value_00")
        self.assertEqual(config.key_01, "layer_01_value_01")
        self.assertEqual(config.key_02.subkey_01, "layer_01_value_02_01")


class TestConfigEdgeCases(unittest.TestCase):
    def test_invalid_json_config_file(self):
        """Test handling of invalid JSON in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = os.path.join(
                temp_dir, ".config", ConfStackExample01.app_name.lower()
            )
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, "w") as f:
                f.write("invalid json")
            with patch.object(
                ConfStackExample01, "load_layer_02_config_file"
            ) as mock_method:
                mock_method.side_effect = MockConfigFileHelper.create_mock_loader(
                    config_file, ConfStackExample01
                )
                config = ConfStackExample01.load_config({})
                # Should fall back to defaults since file load failed
                self.assertEqual(config.key_00, "layer_01_value_00")

    def test_missing_config_file(self):
        """Test behavior when config file does not exist."""
        with patch.object(
            ConfStackExample01, "load_layer_02_config_file"
        ) as mock_method:
            mock_method.side_effect = lambda config_data: None  # does nothing
            config = ConfStackExample01.load_config({})
            self.assertEqual(config.key_00, "layer_01_value_00")

    @patch.dict("os.environ", {"app_name.invalid_key": "value"})
    def test_env_var_invalid_path(self):
        """Test env var with invalid config path."""
        config = ConfStackExample01.load_config({})
        # Should ignore invalid env var
        self.assertEqual(config.key_00, "layer_01_value_00")

    def test_full_layer_integration(self):
        """Test all layers together: defaults -> file -> env -> cli."""
        config_data = {"key_02": {"subkey_01": "file_override"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = os.path.join(
                temp_dir, ".config", ConfStackExample01.app_name.lower()
            )
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, "w") as f:
                json.dump(config_data, f)
            with patch.object(
                ConfStackExample01, "load_layer_02_config_file"
            ) as mock_method:
                mock_method.side_effect = MockConfigFileHelper.create_mock_loader(
                    config_file, ConfStackExample01
                )
                with patch.dict(
                    "os.environ",
                    {
                        "app_name.key_01": "env_override",
                        "APP_NAME_KEY_02_SUBKEY_02": "env_upper",
                    },
                ):
                    cli_args = {
                        "key_00": "cli_override",
                        "key_02.subkey_01": "cli_nested",
                    }
                    config = ConfStackExample01.load_config(cli_args)
                    self.assertEqual(config.key_00, "cli_override")  # CLI highest
                    self.assertEqual(
                        config.key_01, "env_override"
                    )  # Env overrides default
                    self.assertEqual(
                        config.key_02.subkey_01, "cli_nested"
                    )  # CLI overrides file
                    self.assertEqual(
                        config.key_02.subkey_02, "env_upper"
                    )  # Env overrides default


class TestConfigGeneration(unittest.TestCase):
    def test_generate_markdown(self):
        """Test markdown generation for config mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            md_file = os.path.join(temp_dir, "test.md")
            ConfStackExample01.generate_markdown(md_file)
            self.assertTrue(os.path.exists(md_file))
            with open(md_file, "r") as f:
                content = f.read()
            self.assertIn("# app_name Config Mappings", content)
            self.assertIn("Config / CLI Args", content)

    def test_pandas_dataframe_content(self):
        """Test pandas dataframe has correct content."""
        default_dict = ConfStackExample01.model_validate({}).model_dump()
        df = ConfStackExample01.generate_config_mapping_pandas(default_dict)
        self.assertEqual(len(df), 8)
        # Check specific rows
        row = df.loc[df["Config / CLI Args"] == "key_00"].iloc[0]
        self.assertEqual(row["Lowercase Dotted Envs."], "app_name.key_00")
        self.assertEqual(row["Uppercase Underscored Envs."], "APP_NAME_KEY_00")
        self.assertEqual(row["Default Value"], '"layer_01_value_00"')


class TestParseArgsAndPrintJson(unittest.TestCase):
    """Tests for parse_args() and print_json() methods."""

    @patch.object(ConfStackExample01, "to_argparser")
    @patch.object(ConfStackExample01, "load_config")
    def test_parse_args(self, mock_load_config, mock_to_argparser):
        """Test parse_args method parses CLI and loads config."""
        # Setup mock parser with a simple namespace for args
        from argparse import Namespace

        mock_parser = MagicMock()
        mock_args = Namespace(key_00="parsed_value", key_01=None)
        mock_parser.parse_args.return_value = mock_args
        mock_to_argparser.return_value = mock_parser

        # Setup mock load_config return value
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Call parse_args
        result = ConfStackExample01.parse_args()

        # Verify parser was created and parse_args was called
        mock_to_argparser.assert_called_once()
        mock_parser.parse_args.assert_called_once()

        # Verify load_config was called with parsed args (includes None values)
        mock_load_config.assert_called_once_with(
            {"key_00": "parsed_value", "key_01": None}
        )

        # Verify the result is the config returned by load_config
        self.assertEqual(result, mock_config)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_json(self, mock_stdout):
        """Test print_json method outputs valid JSON."""
        config = ConfStackExample01.load_config({})
        config.print_json(indent=2)

        output = mock_stdout.getvalue()
        # Verify it's valid JSON
        parsed = json.loads(output)

        # Verify key values are present
        self.assertEqual(parsed["key_00"], "layer_01_value_00")
        self.assertEqual(parsed["key_01"], "layer_01_value_01")
        self.assertEqual(parsed["key_02"]["subkey_01"], "layer_01_value_02_01")

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_json_custom_indent(self, mock_stdout):
        """Test print_json with custom indentation."""
        config = ConfStackExample01.load_config({})
        config.print_json(indent=4)

        output = mock_stdout.getvalue()
        # Verify it's valid JSON
        parsed = json.loads(output)
        self.assertEqual(parsed["key_00"], "layer_01_value_00")
        # Check that indentation is applied (4 spaces)
        self.assertIn("    ", output)


if __name__ == "__main__":
    unittest.main()
