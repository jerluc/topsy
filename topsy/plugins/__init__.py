from typing import cast, Protocol

from topsy.config import PluginConfig


class Plugin(Protocol):
    """
    Core topsy plugin protocol

    More TBW
    """

    def process(self) -> bool: ...
    def close(self) -> None: ...


def init_plugins(configs: list[PluginConfig]) -> list[Plugin]:
    plugins = []
    for config in configs:
        kwargs = config.model_dump(exclude={"module"})
        ctor = getattr(config.module, "Plugin")
        plugins.append(cast(Plugin, ctor(**kwargs)))
    return plugins


def safe_process(plugins: list[Plugin]):
    for plugin in plugins:
        if hasattr(plugin, "process"):
            return plugin.process()


def safe_close(plugins: list[Plugin]):
    for plugin in plugins:
        if hasattr(plugin, "close"):
            return plugin.close()
