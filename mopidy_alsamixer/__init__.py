import pathlib

import pkg_resources
from mopidy import config, ext

__version__ = pkg_resources.get_distribution("Mopidy-ALSAMixer").version


class Extension(ext.Extension):

    dist_name = "Mopidy-ALSAMixer"
    ext_name = "alsamixer"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["device"] = config.String()
        schema["card"] = config.Integer(optional=True, minimum=0)
        schema["control"] = config.String()
        schema["min_volume"] = config.Integer(minimum=0, maximum=100)
        schema["max_volume"] = config.Integer(minimum=0, maximum=100)
        schema["volume_scale"] = config.String(
            choices=("linear", "cubic", "log")
        )
        return schema

    def setup(self, registry):
        from mopidy_alsamixer.mixer import AlsaMixer

        registry.add("mixer", AlsaMixer)
