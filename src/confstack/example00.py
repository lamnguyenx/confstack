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
    config = ConfStackExample00.parse_args()
    config.print_json()
