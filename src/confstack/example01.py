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
    config = ConfStackExample01.parse_args()
    config.print_json()
