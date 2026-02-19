import pydantic as pdt
import typing as tp
import confstack


class ConfStackExample00(confstack.ConfStack):
    app_name: tp.ClassVar[str] = "app_name"
    key_00: str = "layer_01_value_00"
    key_01: str = "layer_01_value_01"

    class Key02(pdt.BaseModel):
        subkey_01: str = "layer_01_value_02_01"
        subkey_02: str = "layer_01_value_02_02"

    key_02: Key02 = pdt.Field(default_factory=Key02)


if __name__ == "__main__":
    parser = ConfStackExample00.get_argparser()
    parser.add_argument("--extra_flag_01", action="store_true")
    parser.add_argument("--extra_args_01", type=str, default="default_value_01")
    parser.add_argument("extra_pos_args_01", nargs="?")
    config = ConfStackExample00.load_config(cli_args=parser.parse_args())
    config.print_json()
