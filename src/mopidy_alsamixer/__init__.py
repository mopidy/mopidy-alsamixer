import pathlib
from importlib.metadata import version

from mopidy import config, ext
from mopidy.config import ConfigSchema

__version__ = version("mopidy-alsamixer")


class Extension(ext.Extension):
    dist_name = "mopidy-alsamixer"
    ext_name = "alsamixer"
    version = __version__

    def get_default_config(self) -> str:
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> ConfigSchema:
        schema = super().get_config_schema()
        schema["device"] = config.String()
        schema["card"] = config.Integer(optional=True, minimum=0)
        schema["control"] = config.String()
        schema["min_volume"] = config.Integer(minimum=0, maximum=100)
        schema["max_volume"] = config.Integer(minimum=0, maximum=100)
        schema["volume_scale"] = config.String(choices=("linear", "cubic", "log"))
        return schema

    def setup(self, registry: ext.Registry) -> None:
        from mopidy_alsamixer.mixer import AlsaMixer  # noqa: PLC0415

        registry.add("mixer", AlsaMixer)
