import json
from typing import Any, Tuple, Type
from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class HALACustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name in ["backend", "frontend"]:
            if value == "true" or value == "True":
                return True
            return False
        return json.loads(value)


class Settings(BaseSettings):
    # backend: bool = Field(False, alias="ENABLE_BACKEND")
    # frontend: bool = Field(False, alias="ENABLE_FRONTEND")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (HALACustomSource(settings_cls),)
