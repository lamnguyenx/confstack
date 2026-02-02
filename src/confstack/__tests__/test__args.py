import unittest
import os
import json
import tempfile
from unittest.mock import patch
from confstack import ConfStack
from confstack.example01 import ConfStackExample01
import argparse
import pydantic as pdt
import typing as tp


class TestToArgparser(unittest.TestCase):
    def test_basic_parser(self):
        parser = ConfStackExample01.to_argparser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(parser.prog, "__main__.py")

    def test_parser_options_example(self):
        parser = ConfStackExample01.to_argparser()
        key00_action = next(a for a in parser._actions if a.dest == "key_00")
        self.assertEqual(key00_action.default, None)
        self.assertEqual(key00_action.option_strings, ["--key_00"])
        self.assertFalse(key00_action.required)
        self.assertEqual(key00_action.help, "Set key_00")

        nested_action = next(
            a for a in parser._actions if a.dest == "key_02__subkey_01"
        )
        self.assertEqual(nested_action.default, None)
        self.assertEqual(nested_action.option_strings, ["--key_02__subkey_01"])

    def test_parser_parse_args(self):
        parser = ConfStackExample01.to_argparser()
        args = parser.parse_args(
            ["--key_00", "cli_test", "--key_02__subkey_01", "nested_test"]
        )
        self.assertEqual(vars(args)["key_00"], "cli_test")
        self.assertEqual(vars(args)["key_02__subkey_01"], "nested_test")

    def test_inline_model(self):
        class Nested(pdt.BaseModel):
            qux: str = "quux"

        class Simple(ConfStack):
            foo: str = "def"
            bar: bool = False
            baz: bool = True
            nested: Nested = pdt.Field(default_factory=lambda: Nested())

        parser = Simple.to_argparser()
        foo_action = next(a for a in parser._actions if a.dest == "foo")
        self.assertEqual(foo_action.default, None)
        self.assertEqual(foo_action.option_strings, ["--foo"])

        bar_action = next(a for a in parser._actions if a.dest == "bar")
        self.assertEqual(bar_action.option_strings, ["--bar"])

        baz_action = next(a for a in parser._actions if a.dest == "baz")
        self.assertEqual(baz_action.option_strings, ["--baz"])

        qux_action = next(a for a in parser._actions if a.dest == "nested__qux")
        self.assertEqual(qux_action.default, None)
        self.assertEqual(qux_action.help, "Set nested.qux")
        self.assertEqual(qux_action.option_strings, ["--nested__qux"])

    def test_parse_bool_flags(self):
        class BoolModels(ConfStack):
            false_flag: bool = False
            true_flag: bool = True

        parser = BoolModels.to_argparser()
        args_false = parser.parse_args(["--false_flag", "true"])
        self.assertEqual(vars(args_false)["false_flag"], "true")
        args_true = parser.parse_args(["--true_flag", "false"])
        self.assertEqual(vars(args_true)["true_flag"], "false")

    def test_required_field(self):
        class ReqModel(ConfStack):
            req: str  # required

        parser = ReqModel.to_argparser()
        req_action = next(a for a in parser._actions if a.dest == "req")
        self.assertFalse(req_action.required)

        import sys

        args = parser.parse_args(["--req", "test"])
        self.assertEqual(vars(args)["req"], "test")

    def test_empty_model(self):
        parser = ConfStack.to_argparser()
        non_base_actions = [
            a
            for a in parser._actions
            if a.dest and a.option_strings and a.dest != "help"
        ]
        self.assertEqual(len(non_base_actions), 0)


class TestArgparserDescription(unittest.TestCase):
    def test_default_app_name_description(self):
        parser = ConfStack.to_argparser()
        self.assertEqual(parser.description, "ConfStack Configuration")

    def test_custom_app_name_description(self):
        class CustomApp(ConfStack):
            app_name: tp.ClassVar[str] = "MyCustomApp"
            setting: str = "default"

        parser = CustomApp.to_argparser()
        self.assertEqual(parser.description, "MyCustomApp Configuration")


class TestArgparserDeepNesting(unittest.TestCase):
    def test_deeply_nested_model(self):
        class Level3(pdt.BaseModel):
            deep_value: str = "deep"

        class Level2(pdt.BaseModel):
            level3: Level3 = pdt.Field(default_factory=Level3)
            mid_value: str = "mid"

        class Level1(pdt.BaseModel):
            level2: Level2 = pdt.Field(default_factory=Level2)

        class DeepConfig(ConfStack):
            level1: Level1 = pdt.Field(default_factory=Level1)

        parser = DeepConfig.to_argparser()
        deep_action = next(
            a for a in parser._actions if a.dest == "level1__level2__level3__deep_value"
        )
        self.assertEqual(
            deep_action.option_strings, ["--level1__level2__level3__deep_value"]
        )
        self.assertEqual(deep_action.help, "Set level1.level2.level3.deep_value")

        mid_action = next(
            a for a in parser._actions if a.dest == "level1__level2__mid_value"
        )
        self.assertEqual(mid_action.option_strings, ["--level1__level2__mid_value"])

    def test_parse_deeply_nested_args(self):
        class Inner(pdt.BaseModel):
            val: str = "inner"

        class Outer(pdt.BaseModel):
            inner: Inner = pdt.Field(default_factory=Inner)

        class DeepConfig(ConfStack):
            outer: Outer = pdt.Field(default_factory=Outer)

        parser = DeepConfig.to_argparser()
        args = parser.parse_args(["--outer__inner__val", "overridden"])
        self.assertEqual(vars(args)["outer__inner__val"], "overridden")


class TestArgparserMultipleNestedModels(unittest.TestCase):
    def test_sibling_nested_models(self):
        class Database(pdt.BaseModel):
            host: str = "localhost"
            port: int = 5432

        class Cache(pdt.BaseModel):
            host: str = "redis"
            ttl: int = 300

        class AppConfig(ConfStack):
            database: Database = pdt.Field(default_factory=Database)
            cache: Cache = pdt.Field(default_factory=Cache)
            debug: bool = False

        parser = AppConfig.to_argparser()
        dests = {a.dest for a in parser._actions if a.dest != "help"}
        expected = {
            "database__host",
            "database__port",
            "cache__host",
            "cache__ttl",
            "debug",
        }
        self.assertEqual(dests, expected)

        args = parser.parse_args(["--database__host", "prod-db", "--cache__ttl", "600"])
        self.assertEqual(vars(args)["database__host"], "prod-db")
        self.assertEqual(vars(args)["cache__ttl"], "600")


class TestArgparserMultipleFields(unittest.TestCase):
    def test_many_fields(self):
        class ManyFields(ConfStack):
            field_a: str = "a"
            field_b: str = "b"
            field_c: str = "c"
            field_d: int = 1
            field_e: float = 1.5

        parser = ManyFields.to_argparser()
        dests = {a.dest for a in parser._actions if a.dest != "help"}
        expected = {"field_a", "field_b", "field_c", "field_d", "field_e"}
        self.assertEqual(dests, expected)

    def test_all_fields_have_correct_type(self):
        class TypedFields(ConfStack):
            str_field: str = "s"
            int_field: int = 0
            float_field: float = 0.0

        parser = TypedFields.to_argparser()
        for action in parser._actions:
            if action.dest != "help":
                self.assertEqual(action.type, str)


class TestArgparserOptionalFields(unittest.TestCase):
    def test_optional_field(self):
        class OptionalConfig(ConfStack):
            optional_field: tp.Optional[str] = None
            required_field: str = "required"

        parser = OptionalConfig.to_argparser()
        opt_action = next(a for a in parser._actions if a.dest == "optional_field")
        self.assertEqual(opt_action.default, None)
        self.assertFalse(opt_action.required)

    def test_optional_with_default(self):
        class OptionalDefault(ConfStack):
            opt_with_default: tp.Optional[str] = "has_default"

        parser = OptionalDefault.to_argparser()
        action = next(a for a in parser._actions if a.dest == "opt_with_default")
        self.assertEqual(action.default, None)


class TestArgparserParseEmpty(unittest.TestCase):
    def test_parse_no_args(self):
        class SimpleConfig(ConfStack):
            setting: str = "default"

        parser = SimpleConfig.to_argparser()
        args = parser.parse_args([])
        self.assertIsNone(vars(args)["setting"])

    def test_parse_partial_args(self):
        class MultiConfig(ConfStack):
            setting_a: str = "a"
            setting_b: str = "b"
            setting_c: str = "c"

        parser = MultiConfig.to_argparser()
        args = parser.parse_args(["--setting_b", "override"])
        self.assertIsNone(vars(args)["setting_a"])
        self.assertEqual(vars(args)["setting_b"], "override")
        self.assertIsNone(vars(args)["setting_c"])


class TestArgparserSpecialCharacters(unittest.TestCase):
    def test_values_with_spaces(self):
        class SpaceConfig(ConfStack):
            path: str = "/default/path"

        parser = SpaceConfig.to_argparser()
        args = parser.parse_args(["--path", "/path/with spaces/in it"])
        self.assertEqual(vars(args)["path"], "/path/with spaces/in it")

    def test_values_with_special_chars(self):
        class SpecialConfig(ConfStack):
            url: str = "http://example.com"

        parser = SpecialConfig.to_argparser()
        args = parser.parse_args(["--url", "http://example.com?foo=bar&baz=qux"])
        self.assertEqual(vars(args)["url"], "http://example.com?foo=bar&baz=qux")

    def test_empty_string_value(self):
        class EmptyConfig(ConfStack):
            value: str = "default"

        parser = EmptyConfig.to_argparser()
        args = parser.parse_args(["--value", ""])
        self.assertEqual(vars(args)["value"], "")


class TestArgparserCollectConfigPaths(unittest.TestCase):
    def test_collect_paths_flat(self):
        class FlatConfig(ConfStack):
            a: str = "a"
            b: str = "b"

        paths = FlatConfig._collect_config_paths(FlatConfig)
        self.assertEqual(sorted(paths), ["a", "b"])

    def test_collect_paths_nested(self):
        class Inner(pdt.BaseModel):
            x: str = "x"

        class NestedConfig(ConfStack):
            inner: Inner = pdt.Field(default_factory=Inner)
            top: str = "top"

        paths = NestedConfig._collect_config_paths(NestedConfig)
        self.assertEqual(sorted(paths), ["inner.x", "top"])

    def test_collect_paths_example01(self):
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
        self.assertEqual(sorted(paths), sorted(expected))


class TestArgparserHelpText(unittest.TestCase):
    def test_help_format_simple(self):
        class SimpleHelp(ConfStack):
            my_setting: str = "value"

        parser = SimpleHelp.to_argparser()
        action = next(a for a in parser._actions if a.dest == "my_setting")
        self.assertEqual(action.help, "Set my_setting")

    def test_help_format_nested(self):
        class Inner(pdt.BaseModel):
            nested_setting: str = "nested"

        class NestedHelp(ConfStack):
            inner: Inner = pdt.Field(default_factory=Inner)

        parser = NestedHelp.to_argparser()
        action = next(a for a in parser._actions if a.dest == "inner__nested_setting")
        self.assertEqual(action.help, "Set inner.nested_setting")


class TestArgparserIntegrationWithLoadConfig(unittest.TestCase):
    def test_cli_args_override_defaults(self):
        class IntegrationConfig(ConfStack):
            setting: str = "default"

        parser = IntegrationConfig.to_argparser()
        args = parser.parse_args(["--setting", "cli_value"])
        args_dict = {
            k.replace("__", "."): v for k, v in vars(args).items() if v is not None
        }
        config = IntegrationConfig.load_config(args_dict)
        self.assertEqual(config.setting, "cli_value")

    def test_nested_cli_args_override(self):
        class Nested(pdt.BaseModel):
            value: str = "nested_default"

        class NestedIntegration(ConfStack):
            nested: Nested = pdt.Field(default_factory=Nested)

        parser = NestedIntegration.to_argparser()
        args = parser.parse_args(["--nested__value", "cli_nested"])
        args_dict = {}
        for k, v in vars(args).items():
            if v is not None:
                path = k.replace("__", ".")
                args_dict[path] = v
        config = NestedIntegration.load_config(args_dict)
        self.assertEqual(config.nested.value, "cli_nested")


class TestArgparserNumericTypes(unittest.TestCase):
    def test_numeric_fields_as_strings(self):
        class NumericConfig(ConfStack):
            count: int = 10
            rate: float = 0.5

        parser = NumericConfig.to_argparser()
        args = parser.parse_args(["--count", "42", "--rate", "3.14"])
        self.assertEqual(vars(args)["count"], "42")
        self.assertEqual(vars(args)["rate"], "3.14")


class TestArgparserListAndComplexTypes(unittest.TestCase):
    def test_list_field_as_string(self):
        class ListConfig(ConfStack):
            items: tp.List[str] = pdt.Field(default_factory=list)

        parser = ListConfig.to_argparser()
        dests = {a.dest for a in parser._actions if a.dest != "help"}
        self.assertIn("items", dests)


class TestArgparserInheritance(unittest.TestCase):
    def test_inherited_fields(self):
        class BaseConfig(ConfStack):
            base_field: str = "base"

        class DerivedConfig(BaseConfig):
            derived_field: str = "derived"

        parser = DerivedConfig.to_argparser()
        dests = {a.dest for a in parser._actions if a.dest != "help"}
        self.assertEqual(dests, {"base_field", "derived_field"})

    def test_overridden_field(self):
        class BaseConfig(ConfStack):
            field: str = "base_default"

        class DerivedConfig(BaseConfig):
            field: str = "derived_default"

        parser = DerivedConfig.to_argparser()
        action = next(a for a in parser._actions if a.dest == "field")
        self.assertEqual(action.option_strings, ["--field"])
