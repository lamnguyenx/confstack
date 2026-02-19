import pydantic as pdt
import typing as tp
import confstack


class ConfStackExample01(confstack.ConfStack):
    app_name: tp.ClassVar[str] = "app_name"
    key_00: str = "layer_01_value_00"
    key_01: str = "layer_01_value_01"

    class Key02(pdt.BaseModel):
        subkey_01: str = "layer_01_value_02_01"
        subkey_02: str = "layer_01_value_02_02"
        subkey_03: str = "layer_01_value_02_03"

    key_02: Key02 = pdt.Field(default_factory=Key02)

    class Key03(pdt.BaseModel):
        class Subkey00(pdt.BaseModel):
            subsubkey_00: str = "layer_01_value_03_00_00"

        subkey_00: Subkey00 = pdt.Field(default_factory=Subkey00)

        class Subkey01(pdt.BaseModel):
            subsubkey_00: str = "layer_01_value_03_01_00"
            subsubkey_01: str = "layer_01_value_03_01_01"

        subkey_01: Subkey01 = pdt.Field(default_factory=Subkey01)

    key_03: Key03 = pdt.Field(default_factory=Key03)


if __name__ == "__main__":
    parser = ConfStackExample01.get_argparser()

    # Add generic extra optional arguments not in the ConfStack model
    parser.add_argument(
        "--extra_flag_01",
        action="store_true",
        help="Extra flag argument 01 (boolean)",
    )
    parser.add_argument(
        "--extra_args_01",
        type=str,
        default="default_value_01",
        help="Extra argument 01 (default: default_value_01)",
    )
    parser.add_argument(
        "--extra_args_02",
        type=str,
        default="default_value_02",
        help="Extra argument 02 (default: default_value_02)",
    )
    parser.add_argument(
        "--extra_args_03",
        type=str,
        default="default_value_03",
        help="Extra argument 03 (default: default_value_03)",
    )

    # Add generic extra positional arguments
    parser.add_argument(
        "extra_pos_args_01",
        nargs="?",
        default="default_pos_01",
        help="Extra positional argument 01 (default: default_pos_01)",
    )
    parser.add_argument(
        "extra_pos_args_02",
        nargs="?",
        default="default_pos_02",
        help="Extra positional argument 02 (default: default_pos_02)",
    )

    args = parser.parse_args()

    # Load config with all args - extra keys are allowed by the model
    config = ConfStackExample01.load_config(args)
    config.print_json()

