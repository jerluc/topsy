import platformdirs
import tomlkit

from pathlib import Path
from pydantic import BaseModel
from pydantic.types import ImportString


LATEST_CONFIG_VERSION = "0"


class PluginConfig(BaseModel, extra="allow"):
    module: ImportString


class TopsyConfig(BaseModel, frozen=True):
    version: str = LATEST_CONFIG_VERSION
    plugins: list[PluginConfig] = []


def find_state_dir() -> Path:
    state_dir = Path(platformdirs.user_data_dir("topsy"))
    if not state_dir.exists():
        state_dir.mkdir(parents=True)
    return state_dir


def find_config_dir() -> Path:
    config_dir = Path(platformdirs.user_config_dir("topsy"))
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    return config_dir


def load() -> TopsyConfig:
    config_file_path = find_config_dir() / "topsy.toml"
    if not config_file_path.exists():
        with config_file_path.open("w") as config_out:
            default_config_dict = TopsyConfig().model_dump()
            tomlkit.dump(default_config_dict, config_out)

    with config_file_path.open() as config_in:
        config_dict = tomlkit.load(config_in)
    # TODO: Handle different config versions gracefull
    assert (
        config_dict["version"] == LATEST_CONFIG_VERSION
    ), f"Unsupported configuration version: {config_dict['version']}"

    return TopsyConfig.model_validate(config_dict)
